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

from __future__ import absolute_import, print_function

from efl import ecore


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
