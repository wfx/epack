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

import magic


SUPPORTED_MIME = [
    'application/gzip', 'application/x-gzip',
    'application/bzip2', 'application/x-bzip2',
    'application/bz2', 'application/x-bz2',
    'application/rar', 'application/x-rar',
    'application/gz', 'application/x-gz',
    'application/tar', 'application/x-tar',
    'application/tbz2', 'application/x-tbz2',
    'application/tar.gz', 'application/x-tar.gz',
    'application/tar.bz2', 'application/x-tar.bz2',
    'application/tgz', 'application/x-tgz',
    'application/zip', 'application/x-zip',
    'application/Z', 'application/x-Z',
    'application/xz', 'application/x-xz',
    'application/iso9660-image', 'application/x-iso9660-image'
]


def mime_type_query(fname):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return m.file(fname)

