#!/usr/bin/env python
# encoding: utf-8
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, print_function, unicode_literals

import os
import threading
try:
    from queue import Queue # py3
except:
    from Queue import Queue # py2

from efl import ecore


class LibarchiveBackend(object):
    """ This backend use the python libarchive wrapper included in epack
        The wrappers are a plain copy from:
        https://pypi.python.org/pypi/libarchive-c/1.0

        Use threading to don't block the UI.
    """
    name = "Libarchive"

    def __init__(self, archive_file):
        import epack.libarchive

        self.libarchive = epack.libarchive

        # check if we can really open the archive (raise exception on fail)
        with self.libarchive.file_reader(archive_file) as archive:
            pass

        self._queue = Queue()
        self._total_size = 0
        self._stoprequest = threading.Event()
        self._thread = None

    def list_content(self, archive_file, done_cb):
        self._cleanup()
        ecore.Timer(0.1, self._check_list_queue, done_cb)
        self._thread = threading.Thread(target=self._list_in_a_thread,
                                        args=(archive_file,))
        self._thread.start()

    def extract(self, archive_file, destination, progress_cb, done_cb):
        self._cleanup()
        ecore.Timer(0.1, self._check_extract_queue, progress_cb, done_cb)
        self._thread = threading.Thread(target=self._extract_in_a_thread,
                                        args=(archive_file, destination))
        self._thread.start()

    def abort(self):
        self._stoprequest.set()
        self._cleanup()

    def _cleanup(self):
        if self._thread:
            self._thread.join()
            self._thread = None
        self._stoprequest.clear()
        
    def _list_in_a_thread(self, archive_file):
        L = list()
        self._total_size = 0
        with self.libarchive.file_reader(archive_file) as archive:
            for entry in archive:
                L.append(entry.pathname)
                self._total_size += entry.size
                if self._stoprequest.isSet():
                    break
        self._queue.put(sorted(L))

    def _extract_in_a_thread(self, archive_file, destination):
        written = 0
        perm_to_apply = []
        try:
            with self.libarchive.file_reader(archive_file) as archive:
                for entry in archive:
                    # print(entry.pathname, entry.size, oct(entry.perm), entry.mtime)
                    path = os.path.join(destination, entry.pathname)

                    # create a folder
                    if entry.isdir:
                        if not os.path.exists(path):
                            os.mkdir(path)
                        perm_to_apply.insert(0, (path, entry.perm))

                    # or write a file to disk
                    else: # TODO test other special types
                        # ensure the folder where the file reside exists
                        dirname = os.path.dirname(path)
                        if not os.path.exists(dirname):
                            os.makedirs(dirname)
                        # write the file
                        with open(path, 'wb') as f:
                            for block in entry.get_blocks():
                                f.write(block)
                                written += len(block)
                                perc = float(written) / self._total_size
                                self._queue.put((perc, entry.pathname))

                                if self._stoprequest.isSet():
                                    raise RuntimeError('stopped')
                        # apply correct permission to files
                        os.chmod(path, entry.perm)

                    # apply correct mtime to files and folders
                    os.utime(path, (-1, entry.mtime))

            # apply correct permission to folders (should be well ordered)
            for path, perm in perm_to_apply:
                os.chmod(path, perm)

        except RuntimeError as e:
            self._queue.put(('done', 'stopped'))
        except Exception as e:
            self._queue.put(('error', str(e)))
        else:
            self._queue.put(('done', 'success'))

    def _check_list_queue(self, done_cb):
        if self._queue.empty():
            return ecore.ECORE_CALLBACK_RENEW

        self._cleanup()
        done_cb(self._queue.get())
        return ecore.ECORE_CALLBACK_CANCEL

    def _check_extract_queue(self, progress_cb, done_cb):
        # is an item available in the queue ?
        if self._queue.empty():
            return ecore.ECORE_CALLBACK_RENEW

        # get the last item in the queue
        while not self._queue.empty():
            item1, item2 = self._queue.get()

        # call the progress callback
        if isinstance(item1, float):
            progress_cb(item1, item2)
            return ecore.ECORE_CALLBACK_RENEW

        # extract completed
        self._cleanup()
        done_cb(item2)
        return ecore.ECORE_CALLBACK_CANCEL
