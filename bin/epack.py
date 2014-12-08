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

__authors__ = "Dave Andreoli (daveMDS) & Wolfgang Morawetz (wfx)"
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


def mime_type_query(fname):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return m.file(fname)

class MainWin(StandardWindow):
    def __init__(self, fname):
        self.fname = fname
        self.mime_type = mime_type_query(fname)
        self.dest_folder = os.path.dirname(fname)
        self.cdata = list()

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
            cmd = LIST_MAP.get(self.mime_type)+' '+self.fname
            self.command_execute_list(cmd)
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

        # show the window
        self.resize(300, 200)
        self.show()

    def update_header(self):
        self.hlabel.text = "<b>Archive:</b> %s<br><b>Destination:</b> %s" % (
                            os.path.basename(self.fname), self.dest_folder)

    def chosen_folder_cb(self, fs, folder):
        if folder:
            os.chdir(folder)
            self.dest_folder = folder
            self.update_header()

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
        self.btn1.disabled = False
        self.update_header()

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
        if self.del_chk.state == True:
            os.remove(self.fname)
        elementary.exit()


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


if __name__ == "__main__":

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
