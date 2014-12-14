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

__authors__ = "Dave Andreoli (davemds) & Wolfgang Morawetz (wfx)"
__copyright__ = "Copyright (C) 2014 Wolfgang Morawetz"
__version__ = "2014.12.7.050"
__description__ = 'A simple tool to extract any file with efm'
__github__ = 'https://github.com/wfx/epack'
__source__ = 'Source code and bug reports: {0}'.format(__github__)
PY_EFL = "https://git.enlightenment.org/bindings/python/python-efl.git/"

import os
import sys
import magic
try:
    from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
    from efl import elementary
    from efl.elementary.window import StandardWindow
    from efl.elementary.innerwindow import InnerWindow
    from efl.elementary.box import Box
    from efl.elementary.frame import Frame
    from efl.elementary.icon import Icon
    from efl.elementary.label import Label
    from efl.elementary.entry import Entry
    from efl.elementary.list import List
    from efl.elementary.button import Button
    from efl.elementary.table import Table
    from efl.elementary.check import Check
    from efl.elementary.fileselector_button import FileselectorButton
    from efl.elementary.fileselector import Fileselector
    from efl.elementary.progressbar import Progressbar
    from efl.elementary.panel import Panel, ELM_PANEL_ORIENT_LEFT
    from efl import ecore
    from efl.ecore import Exe, ECORE_EXE_PIPE_READ, ECORE_EXE_PIPE_READ_LINE_BUFFERED
except ImportError:
    print("ImportError: Please install Python-EFL:\n ", PY_EFL)
    exit(1)


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.0

# the extracting application needs support to read from stdin.
# and bsdtar is great at all.
EXTRACT_MAP = {
    'application/gzip': 'bsdtar -xf -','application/x-gzip': 'bsdtar -xf -',
    'application/bzip2': 'bsdtar -xf -','application/x-bzip2': 'bsdtar -xf -',
    'application/bz2': 'bsdtar -xf -','application/x-bz2': 'bsdtar -xf -',
    'application/rar': 'bsdtar -xf -','application/x-rar': 'bsdtar -xf -',
    'application/gz': 'bsdtar -xf -','application/x-gz': 'gbsdtar -xf -',
    'application/tar': 'bsdtar -xf -','application/x-tar': 'bsdtar -xf -',
    'application/tbz2': 'bsdtar -xf -','application/x-tbz2': 'bsdtar -xf -',
    'application/tar.bz2': 'bsdtar -xf -','application/x-tar.bz2': 'bsdtar -xf -',
    'application/tar.gz': 'bsdtar -xf -','application/x-tar.gz': 'bsdtar -xf -',
    'application/tgz': 'bsdtar -xf -','application/x-tgz': 'bsdtar -xf -',
    'application/zip': 'bsdtar -xf -','application/x-zip': 'bsdtar -xf -',
    'application/Z': 'bsdtar -xf -','application/x-Z': 'bsdtar -xf -',
    'application/xz': 'bsdtar -xf -','application/x-xz': 'bsdtar -xf -',
    'application/iso9660-image': 'bsdtar -xf -','application/x-iso9660-image': 'bsdtar -xf -'
}

LIST_MAP = {
    'application/gzip': 'bsdtar -tf','application/x-gzip': 'bsdtar -tf',
    'application/bzip2': 'bsdtar -tf','application/x-bzip2': 'bsdtar -tf',
    'application/bz2': 'bsdtar -tf','application/x-bz2': 'bsdtar -tf',
    'application/rar': 'bsdtar -tf','application/x-rar': 'bsdtar -tf',
    'application/gz': 'bsdtar -tf','application/x-gz': 'gbsdtar -tf',
    'application/tar': 'bsdtar -tf','application/x-tar': 'bsdtar -tf',
    'application/tbz2': 'bsdtar -tf','application/x-tbz2': 'bsdtar -tf',
    'application/tar.gz': 'bsdtar -tf','application/x-tar.gz': 'bsdtar -tf',
    'application/tar.bz2': 'bsdtar -tf','application/x-tar.bz2': 'bsdtar -tf',
    'application/tgz': 'bsdtar -tf','application/x-tgz': 'bsdtar -tf',
    'application/zip': 'bsdtar -tf','application/x-zip': 'bsdtar -tf',
    'application/Z': 'bsdtar -tf','application/x-Z': 'bsdtar -tf',
    'application/xz': 'bsdtar -tf','application/x-xz': 'bsdtar -tf',
    'application/iso9660-image': 'bsdtar -tf -','application/x-iso9660-image': 'bsdtar -tf -'
}


def mime_type_query(fname):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return m.file(fname)

class MainWin(StandardWindow):
    def __init__(self, fname):
        self.fname = fname
        self.mime_type = mime_type_query(fname)
        self.dest_folder = os.path.dirname(fname)

        # the window
        StandardWindow.__init__(self, 'epack.py', 'Epack')
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: elementary.exit())


        if not EXTRACT_MAP.get(self.mime_type):
            errlb = Label(self)
            errlb.text_set("Mimetype: "+self.mime_type+" is not supported")
            errwin = InnerWindow(self, content=errlb)
            errwin.show()
        else:
            # main vertical box
            vbox = Box(self, size_hint_weight=EXPAND_BOTH)
            self.resize_object_add(vbox)
            vbox.show()

            ### header horiz box
            hbox = Box(self, horizontal=True, size_hint_weight=EXPAND_HORIZ,
                       size_hint_align=FILL_HORIZ)
            vbox.pack_end(hbox)
            hbox.show()

            # spinner
            self.spinner = Progressbar(hbox, style="wheel", pulse_mode=True)
            self.spinner.pulse(True)
            self.spinner.show()
            hbox.pack_end(self.spinner)

            # info entry
            self.hlabel = Entry(hbox, editable=False,
                                text="Reading archive, please wait...",
                                size_hint_weight=EXPAND_HORIZ,
                                size_hint_align=FILL_HORIZ)
            self.hlabel.show()
            hbox.pack_end(self.hlabel)

            # list with file content
            self.file_list = List(self, size_hint_weight=EXPAND_BOTH,
                                  size_hint_align=FILL_BOTH)
            self.file_list.show()
            vbox.pack_end(self.file_list)

            ### footer table
            table = Table(self, size_hint_weight=EXPAND_HORIZ,
                                size_hint_align=FILL_HORIZ)
            vbox.pack_end(table)
            table.show()

            # fsb
            icon = Icon(self, standard='folder')#, size_hint_min=(20,20))
            self.fsb = FileselectorButton(self, inwin_mode=False,
                                          folder_only=True, content=icon,
                                          size_hint_align=FILL_HORIZ)
            self.fsb.callback_file_chosen_add(self.chosen_folder_cb)
            table.pack(self.fsb, 0, 0, 1, 1)
            self.fsb.show()

            # delete archive checkbox
            self.del_chk = Check(hbox, text="Delete archive after extraction",
                                 size_hint_weight=EXPAND_HORIZ,
                                 size_hint_align=(0.0, 1.0))
            table.pack(self.del_chk, 1, 0, 1, 1)
            self.del_chk.show()

            # create archive folder
            self.create_folder_chk = Check(hbox, text="Create archive folder.",
                                           size_hint_weight=EXPAND_HORIZ,
                                           size_hint_align=(0.0, 1.0))
            self.create_folder_chk.callback_changed_add(
                                            lambda c: self.update_header())
            table.pack(self.create_folder_chk, 2, 0, 1, 1)
            self.create_folder_chk.show()

            # extract button
            self.btn1 = Button(self, text='Extract', disabled=True)
            self.btn1.callback_clicked_add(self.extract_btn_cb)
            table.pack(self.btn1, 0, 1, 1, 1)
            self.btn1.show()

            # progress bar
            self.pbar = Progressbar(self, size_hint_weight=EXPAND_HORIZ,
                                    size_hint_align=(-1.0, 0.5))
            table.pack(self.pbar, 1, 1, 1, 1)
            self.pbar.show()

            # ask for the archive content list
            backend.list_content(self.fname, self.mime_type, self.list_done_cb)

        # show the window
        self.resize(300, 200)
        self.show()

    def update_header(self):
        if self.create_folder_chk.state is True:
            folder = os.path.join(self.dest_folder, os.path.basename(self.fname))
        else:
            folder = self.dest_folder
        self.hlabel.text = "<b>Archive:</b> %s<br><b>Destination:</b> %s" % (
                            os.path.basename(self.fname), folder)

    def chosen_folder_cb(self, fs, folder):
        if folder:
            self.dest_folder = folder
            self.update_header()

    def extract_btn_cb(self, btn):
        self.btn1.disabled = True
        if self.create_folder_chk.state == True:
            folder = os.path.basename(self.fname)
            self.dest_folder = os.path.join(self.dest_folder, folder)
            os.mkdir(self.dest_folder)

        backend.extract(self.fname, self.mime_type, self.dest_folder,
                        self.extract_progress_cb)

    def list_done_cb(self, file_list):
        for f in file_list:
            self.file_list.item_append(f)
        self.file_list.go()
        self.spinner.pulse(False)
        self.spinner.delete()
        self.btn1.disabled = False
        self.update_header()

    def extract_progress_cb(self, progress):
        if progress == 'done':
            if self.del_chk.state == True:
                os.remove(self.fname)
            elementary.exit()
        else:
            self.pbar.value = progress


class FileChooserWin(StandardWindow):
    def __init__(self):
        StandardWindow.__init__(self, 'epack.py', 'Choose an archive')
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: elementary.exit())

        fs = Fileselector(self, expandable=False,
                          path=os.path.expanduser('~'),
                          size_hint_weight=EXPAND_BOTH,
                          size_hint_align=FILL_BOTH)
        fs.callback_done_add(self.done_cb)
        fs.mime_types_filter_append(list(EXTRACT_MAP.keys()), 'Archive files')
        fs.mime_types_filter_append(['*'], 'All files')
        fs.show()

        self.resize_object_add(fs)
        self.resize(300, 400)
        self.show()

    def done_cb(self, fs, path):
        if path is None:
            elementary.exit()
            return

        if not os.path.isdir(path):
            MainWin(path)
            self.delete()


class ShellBackend(object):
    """ This backend use pv + bsdtar to extract archives
        Use ecore.Exe to don't block the UI.
    """
    name = "pv | bsdtar in an ecore.Exe"

    def __init__(self):
        # TODO backend requirement checks here
        pass

    def list_content(self, archive_file, mime_type, done_cb):
        self._contents = list()
        cmd = '%s "%s"' % (LIST_MAP.get(mime_type), archive_file)
        exe = ecore.Exe(cmd, ecore.ECORE_EXE_PIPE_READ |
                             ecore.ECORE_EXE_PIPE_READ_LINE_BUFFERED)
        exe.on_data_event_add(self._list_stdout)
        exe.on_del_event_add(self._list_done, done_cb)

    def extract(self, archive_file, mime_type, destination, progress_cb):
        os.chdir(destination)
        cmd = 'pv -n "%s" | %s ' % (archive_file, EXTRACT_MAP.get(mime_type))
        exe = ecore.Exe(cmd, ecore.ECORE_EXE_PIPE_ERROR |
                             ecore.ECORE_EXE_PIPE_ERROR_LINE_BUFFERED)
        exe.on_error_event_add(self._extract_stderr, progress_cb)
        exe.on_del_event_add(self._extract_done, progress_cb)

    def _list_stdout(self, command, event):
        self._contents.extend(event.lines)

    def _list_done(self, command, event, done_cb):
        done_cb(self._contents)

    def _extract_stderr(self, command, event, progress_cb):
        progress = float(event.lines[0])
        progress_cb(progress / 100)

    def _extract_done(self, command, event, progress_cb):
        progress_cb('done')


class LibarchiveBackend(object):
    """ This backend use the python libarchive wrapper found at:
        https://pypi.python.org/pypi/libarchive

        Use threading to don't block the UI.

        NOTE: the wrapper seems not to expose the file mode so we cannot
              appy the correct permission to the extracted files/folders
    """
    name = "Libarchive in a thread"

    def __init__(self):
        import libarchive.public
        import threading
        try:    from queue import Queue # py3
        except: from Queue import Queue # py2

        self.libarchive = libarchive.public
        self.Thread = threading.Thread
        self._queue = Queue()
        self._total_size = 0

    def list_content(self, archive_file, mime_type, done_cb):
        ecore.Timer(0.1, self._check_queue, done_cb)
        self.Thread(target=self._list_in_a_thread,
                    args=(archive_file,)).start()

    def extract(self, archive_file, mime_type, destination, progress_cb):
        ecore.Timer(0.1, self._check_queue, progress_cb)
        self.Thread(target=self._extract_in_a_thread,
                    args=(archive_file, destination)).start()

    def _list_in_a_thread(self, archive_file):
        L = list()
        self._total_size = 0
        with self.libarchive.file_enumerator(archive_file) as archive:
            for entry in archive:
                L.append(entry.pathname)
                self._total_size += entry.size
        self._queue.put(L)

    def _extract_in_a_thread(self, archive_file, destination):
        written = 0
        with self.libarchive.file_reader(archive_file) as archive:
            for entry in archive:
                # print(entry.pathname, entry.size)
                # TODO MODE !!!!!!!!

                path = os.path.join(destination, entry.pathname)

                if entry.filetype.IFDIR:
                    if not os.path.exists(path):
                        os.mkdir(path)
                else: # TODO test other special types
                    with open(path, 'wb') as f:
                        for block in entry.get_blocks():
                            f.write(block)
                            written += len(block)
                            self._queue.put(float(written) / self._total_size)
        self._queue.put('done')

    def _check_queue(self, user_cb):
        # is an item available in the queue ?
        if self._queue.empty():
            return ecore.ECORE_CALLBACK_RENEW

        # get the last item in the queue
        while not self._queue.empty():
            item = self._queue.get()

        # call the user callback
        user_cb(item)

        # continue or stop the timer
        if item == 'done' or isinstance(item, list):
            return ecore.ECORE_CALLBACK_CANCEL
        else:
            return ecore.ECORE_CALLBACK_RENEW


class PythonLibarchiveBackend(object):
    """ This backend use the python-libarchive wrapper found at:
        https://pypi.python.org/pypi/python-libarchive
        
        Use multiprocessing to don't block the UI, as the wrapper doesn't
        work well using threads.

        NOTE: I'm not really sure that the multiprocessing module will not
              clash with the ecore mainloop.
        NOTE: python-libarchive do not work with python3 :(
        NOTE: python-libarchive seems not really maintained :(
    """
    name = "Python-Libarchive in a subprocess"

    def __init__(self):
        import libarchive
        import multiprocessing

        self.libarchive = libarchive
        self.Process = multiprocessing.Process
        self._queue = multiprocessing.Queue()
        self._total_size = multiprocessing.Value('L', 0)

    def list_content(self, archive_file, mime_type, done_cb):
        ecore.Timer(0.1, self._check_queue, done_cb)
        self.Process(target=self._list_in_a_thread,
                     args=(archive_file,)).start()

    def extract(self, archive_file, mime_type, destination, progress_cb):
        ecore.Timer(0.1, self._check_queue, progress_cb)
        self.Process(target=self._extract_in_a_thread,
                     args=(archive_file, destination)).start()

    def _list_in_a_thread(self, archive_file):
        L = list()
        tot = 0
        with self.libarchive.Archive(archive_file) as archive:
            for entry in archive:
                L.append(entry.pathname)
                tot += entry.size
        self._total_size.value = tot
        self._queue.put(L)

    def _extract_in_a_thread(self, archive_file, destination):
        written = 0
        tot = self._total_size.value
        with self.libarchive.Archive(archive_file) as archive:
            for entry in archive:
                # print(entry.pathname, entry.size, oct(entry.mode))
                path = os.path.join(destination, entry.pathname)

                # create a folder
                if entry.isdir():
                    if not os.path.exists(path):
                        os.mkdir(path)

                # or write a file to disk
                else: # TODO test other special types
                    with open(path, 'wb') as f:
                        for block in archive.readstream(entry.size):
                            f.write(block)
                            written += len(block)
                            self._queue.put(float(written) / tot)

                # apply the correct file/folder permission
                os.chmod(path, entry.mode)
        
        self._queue.put('done')

    def _check_queue(self, user_cb):
        # is an item available in the queue ?
        if self._queue.empty():
            return ecore.ECORE_CALLBACK_RENEW

        # get the last item in the queue
        while not self._queue.empty():
            item = self._queue.get()

        # call the user callback
        user_cb(item)

        # continue or stop the timer
        if item == 'done' or isinstance(item, list):
            return ecore.ECORE_CALLBACK_CANCEL
        else:
            return ecore.ECORE_CALLBACK_RENEW


def load_backend():
    for backend in PythonLibarchiveBackend, LibarchiveBackend, ShellBackend:
        try:
            instance = backend()
            break
        except Exception as e:
            # print(e)
            instance = None

    if instance is None:
        print('Cannot find a working backend')
        exit(1)

    print('Using backend: "%s"' % backend.name)
    return instance
    

if __name__ == "__main__":

    backend = load_backend()

    elementary.init()
    elementary.need.need_efreet()

    if len(sys.argv) < 2:
        FileChooserWin()
    else:
        fname = sys.argv[1]
        fname = os.path.abspath(fname.replace("file://",""))
        MainWin(fname)

    elementary.run()
    elementary.shutdown()
