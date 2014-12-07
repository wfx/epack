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
# ####################################################################
#
# Thanks to:
# davemds, helps me realy lot!
#


__author__ = "Wolfgang Morawetz"
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
    from efl.elementary.list import List
    from efl.elementary.button import Button
    from efl.elementary.progressbar import Progressbar
    from efl.elementary.panel import Panel, ELM_PANEL_ORIENT_LEFT
    from efl import ecore
    from efl.ecore import Exe, ECORE_EXE_PIPE_READ, ECORE_EXE_PIPE_READ_LINE_BUFFERED
except ImportError:
    printErr("ImportError: Please install Python-EFL:\n ", PY_EFL)
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
	'application/iso9660-image': 'bsdtar -tf -','application/x-iso9660-image': 'bsdtar -tf -'
}

USAGE = """epack.py %s
Usage: epack.py <archive_to_extract>
""" % __description__

def mime_type_query(fname):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return m.file(fname)

class MainWin(StandardWindow):
    def __init__(self, fname, mime):
        self.fname = fname
        self.mime_type = mime
        self.cdata = list()

        # the window
        StandardWindow.__init__(self, 'epack', 'Epack')
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: elementary.exit())


        if not EXTRACT_MAP.get(mime):
            errlb = Label(self)
            errlb.text_set("Mimetype: "+self.mime_type+" is not supported")
            errwin = InnerWindow(self, content=errlb)
            errwin.show()
        else:
            # main vertical box
            vbox = Box(self, size_hint_weight=EXPAND_BOTH)
            self.resize_object_add(vbox)
            vbox.show()

            # header lable + spinner
            hbox = Box(self, horizontal=True, align=(0.0, 0.0),
                       size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
            hbox.show()
            vbox.pack_end(hbox)

            self.spinner = Progressbar(hbox, style="wheel", pulse_mode=True)
            self.spinner.pulse(True)
            self.spinner.show()
            hbox.pack_end(self.spinner)

            self.hlabel = Label(hbox, text="Reading archive, please wait...")
            self.hlabel.show()
            hbox.pack_end(self.hlabel)

            # list with file content
            self.file_list = List(self, size_hint_weight=EXPAND_BOTH,
                                  size_hint_align=FILL_BOTH)

            cmd = LIST_MAP.get(self.mime_type)+' '+self.fname
            self.command_execute_list(cmd)
            self.file_list.show()
            vbox.pack_end(self.file_list)

            # progress bar
            self.pbar = Progressbar(self, size_hint_weight=EXPAND_HORIZ,
                                    size_hint_align=FILL_HORIZ)
            vbox.pack_end(self.pbar)
            self.pbar.show()

            # extract button
            self.btn1 = Button(self, text='extract', disabled=True)
            self.btn1.callback_clicked_add(self.extract_btn_cb)
            self.btn1.show()
            vbox.pack_end(self.btn1)

        # show the window
        self.resize(300, 200)
        self.show()

    def extract_btn_cb(self, btn):
        cmd = 'pv -n %s | %s ' % (self.fname, EXTRACT_MAP.get(self.mime_type))
        self.btn1.disabled = True
        self.command_execute(cmd)

    def command_execute_list(self, command):
        print("Executing: ", command)
        exe = ecore.Exe(command,
                        ecore.ECORE_EXE_PIPE_READ |
                        ecore.ECORE_EXE_PIPE_READ_LINE_BUFFERED
                        )
        exe.on_data_event_add(self.list_stdout)
        exe.on_del_event_add(self.list_done)

    def list_stdout(self, command, event):
        for index, item in enumerate(event.lines):
            self.file_list.item_append(item)

    def list_done(self, command, event):
        self.spinner.pulse(False)
        self.spinner.delete()
        self.hlabel.text = "Archive: " + os.path.basename(self.fname)
        self.btn1.disabled = False

    def command_execute(self, command):
        print("Executing: ", command)
        exe = ecore.Exe(command,
                        ecore.ECORE_EXE_PIPE_ERROR |
                        ecore.ECORE_EXE_PIPE_ERROR_LINE_BUFFERED
                        )
        exe.on_error_event_add(self.execute_stderr)
        exe.on_del_event_add(self.execute_done)

    def execute_stderr(self, command, event):
        line = event.lines[0]
        progress = float(line)
        self.pbar.value = progress / 100

    def execute_done(self, command, event):
        elementary.exit()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(USAGE)
        sys.exit(1)

    fname = sys.argv[1]
    fname = fname.replace("file://","")
    mime = mime_type_query(fname)

    elementary.init()
    MainWin(fname, mime)

    elementary.run()
    elementary.shutdown()
