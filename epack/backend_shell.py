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

import os

from efl import ecore

from epack.utils import mime_type_query

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


class ShellBackend(object):
    """ This backend use pv + bsdtar to extract archives
        Use ecore.Exe to don't block the UI.
    """
    name = "pv | bsdtar in an ecore.Exe"

    def __init__(self, archive_file):

        # TODO check if pv and bsdtar are installed

        self.mime_type = mime_type_query(archive_file)
        if not self.mime_type in EXTRACT_MAP:
            raise RuntimeError('mime-type not supported')

    def list_content(self, archive_file, done_cb):
        self._contents = list()
        cmd = '%s "%s"' % (LIST_MAP.get(self.mime_type), archive_file)
        exe = ecore.Exe(cmd, ecore.ECORE_EXE_PIPE_READ |
                             ecore.ECORE_EXE_PIPE_READ_LINE_BUFFERED)
        exe.on_data_event_add(self._list_stdout)
        exe.on_del_event_add(self._list_done, done_cb)

    def extract(self, archive_file, destination, progress_cb, done_cb):
        os.chdir(destination)
        cmd = 'pv -n "%s" | %s ' % (archive_file, EXTRACT_MAP.get(self.mime_type))
        exe = ecore.Exe(cmd, ecore.ECORE_EXE_PIPE_ERROR |
                             ecore.ECORE_EXE_PIPE_ERROR_LINE_BUFFERED)
        exe.on_error_event_add(self._extract_stderr, progress_cb)
        exe.on_del_event_add(self._extract_done, done_cb)

    def _list_stdout(self, command, event):
        self._contents.extend(event.lines)

    def _list_done(self, command, event, done_cb):
        done_cb(self._contents)

    def _extract_stderr(self, command, event, progress_cb):
        progress = float(event.lines[0]) / 100
        progress_cb(progress, '')

    def _extract_done(self, command, event, progress_cb):
        progress_cb('success')
