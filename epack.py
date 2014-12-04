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
# Doubleclick on File.
#  Get archive mimetytpe (tar, zip, whatever)
#  Create from archive a file list
#  Show file list
#  Show a make folder option (label into folder)
#  show a delete after extract option (label delete archive)
#  show extract button (label extract)
#  extract:
#  test if command exist
#  start spinner
#  extract archive
#  stop spinner

__author__ = "Wolfgang Morawetz"
__copyright__ = "Copyright (C) 2014 Wolfgang Morawetz"
__version__ = "Alpha.0.2014.12.4"
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
	from efl.elementary.box import Box
	from efl.elementary.frame import Frame
	from efl.elementary.icon import Icon
	from efl.elementary.label import Label
	from efl.elementary.list import List
	from efl.elementary.button import Button
	from efl.elementary.panel import Panel, ELM_PANEL_ORIENT_LEFT
	from efl import ecore
	from efl.ecore import Exe, ECORE_EXE_PIPE_READ, ECORE_EXE_PIPE_READ_LINE_BUFFERED
except ImportError:
	printErr("ImportError: Please install Python-EFL:\n ", PY_EFL)
	exit(1)


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL


class Application(object):
	def __init__(self):
		self.userid = os.getuid()
		self.target = Target(cmdline())
		self.args = None
		self.kwargs = None
		self.wm = WinMain("epack")
		self.ui = Interface(self.wm.win)
		self.ui.data_archive_name = self.target.name
		self.ui.data_archive_type = self.target.mimetype
		self.ui.data_archive_list = None
		self.ui.bt_extract_cb = self.extract
		self.ui.bt_extract_text = "extract"
		self.ui.update()

	def extract(self, obj):
		# TODO: use a dictionary?
		if self.target.mimetype == "application/tar.gz" or self.target.mimetype == "application/x-gzip":
			self.command_execute(command="tar", arg="xzf "+self.target.name)
		elif self.target.mimetype == "application/bz2" or self.target.mimetype == "application/x-bz2":
			self.command_execute(command="bunzip2", arg=self.target.name)
		elif self.target.mimetype == "application/rar" or self.target.mimetype == "application/x-rar":
			self.command_execute(command="unrar", arg="x "+self.target.name)
		elif self.target.mimetype == "application/gz" or self.target.mimetype == "application/x-gz":
			self.command_execute(command="gunzip", arg=self.self.target.name)
		elif self.target.mimetype == "application/tar" or self.target.mimetype == "application/x-tar":
			self.command_execute(command="tar", arg="xf "+sself.target.name)
		elif self.target.mimetype == "application/tbz2" or self.target.mimetype == "application/tar.bz2":
			self.command_execute(command="tar", arg="xjf "+self.target.name)
		elif self.target.mimetype == "application/tgz" or self.target.mimetype == "application/zip" or self.target.mimetype == "application/x-zip":
			self.command_execute(command="unzip", arg=self.target.name)
		elif self.target.mimetype == "application/Z":
			self.command_execute(command="uncompress", arg=self.target.name)
		else:
			print(self.file.type + " cannot be extracted")
		elementary.exit()

	def command_execute(self, command, *args, **kwargs):

		command = command+" "+kwargs['arg']
		self.cmd = ecore.Exe(
			command,
			ecore.ECORE_EXE_PIPE_READ |
			ecore.ECORE_EXE_PIPE_ERROR |
			ecore.ECORE_EXE_PIPE_WRITE
		)
		self.cmd.on_add_event_add(self.command_started)
		self.cmd.on_error_event_add(self.command_error)
		self.cmd.on_del_event_add(self.command_done)

	def command_started(self, command, event):
		print("Start Command")

	def command_error(self, command, event):
		print("Error Command")

	def command_done(self, command, event):
		print("Command Done")

class Target(object):
	def __init__(self, target):
		self.__target_name = target
		self.__target_name = self.__target_name.replace("file://","")
		self.__target_magic = magic.open(magic.MAGIC_MIME_TYPE)
		self.__target_magic.load()
		self.__target_type = self.__target_magic.file(self.__target_name)

	def __get_target_name(self):
		return self.__target_name

	def __get_target_type(self):
		return self.__target_type

	name = property(__get_target_name)
	mimetype = property(__get_target_type)



class WinMain(object):
	def __init__(self, title):
		self.__win = None
		self.__title = title
		self.__win = StandardWindow(title, title, focus_highlight_enabled=True, autodel=True)
		self.__win.callback_delete_request_add(self.__destroy)
		self.show()

	def __set_title(self, title):
		self.win.title_set(title)

	def __get_title(self):
		return self.__title

	def __get_win(self):
		return self.__win

	def show(self):
		self.__win.show()

	def __destroy(self, obj):
		elementary.exit()

	title = property(__get_title, __set_title)
	win = property(__get_win)


class Interface(object):
	def __init__(self, win):
		self.win = win
		self.__archive_name = None
		self.__archive_type = None
		self.__archive_list = None
		self.__bt_extract_text = None
		self.__bt_extract_cb = None

	def __get_archive_name(self):
		return self.__archive_name

	def __set_archive_name(self, var):
		self.__archive_name = var

	def __get_archive_type(self):
		return self.__archive_type

	def __set_archive_type(self, var):
		self.__archive_type = var

	def __get_archive_list(self):
		return self.__archive_list

	def __set_archive_list(self, var):
		self.__archive_list = var

	def __get_bt_extract_text(self):
		return self.__bt_extract_text

	def __set_bt_extract_text(self, var):
		self.__bt_extract_text = var

	def __get_bt_extract_callback(self):
		return self.__bt_extract_cb

	def __set_bt_extract_callback(self, obj):
		self.__bt_extract_cb = obj

	def update(self):
		self.bx_main = Box(self.win, size_hint_weight=EXPAND_BOTH)
		self.win.resize_object_add(self.bx_main)
		self.bx_main.size_hint_weight = EXPAND_BOTH
		self.win.resize_object_add(self.bx_main)
		self.bx_main.show()

		self.fr_info = Frame(self.win)
		self.fr_info.text_set(self.__archive_name)
		self.bx_main.pack_end(self.fr_info)
		self.fr_info.show()

		self.lb = Label(self.win)
		self.lb.text_set(self.__archive_type)
		self.fr_info.content_set(self.lb)
		self.lb.show()

		self.bt_extract = Button(self.win, text=self.__bt_extract_text)
		self.bt_extract.callback_clicked_add(self.__bt_extract_cb)
		self.bx_main.pack_end(self.bt_extract)
		self.bt_extract.show()

	data_archive_type = property(__get_archive_type, __set_archive_type)
	data_archive_name = property(__get_archive_name, __set_archive_name)
	data_archive_list = property(__get_archive_list, __set_archive_list)
	bt_extract_text = property(__get_bt_extract_text, __set_bt_extract_text)
	bt_extract_cb = property(__get_bt_extract_callback, __set_bt_extract_callback)


def cmdline():
	file = sys.argv[1]
	return file

if __name__ == "__main__":

	elementary.init()
	Application()

	elementary.run()
	elementary.shutdown()
