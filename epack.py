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

__author__ = "Wolfgang Morawetz"
__copyright__ = "Copyright (C) 2014 Wolfgang Morawetz"
__version__ = "Alpha.0.2014.12.1"
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
except ImportError:
	printErr("ImportError: Please install Python-EFL:\n ", PY_EFL)
	exit(1)

EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL

#App icon
#ic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
#ic_file = os.path.join(img_path, "logo_small.png")

class Application(object):
	def __init__(self):
		self.userid = os.getuid()

		self.file = File()

		self.win = None
		self.bx_main = None

		self.win = StandardWindow("my app", "epack", focus_highlight_enabled=True, autodel=True)
		self.win.title_set("epack")
		self.win.callback_delete_request_add(self.destroy)

		self.bx_main = Box(self.win, size_hint_weight=EXPAND_BOTH)
		self.win.resize_object_add(self.bx_main)
		self.bx_main.size_hint_weight = EXPAND_BOTH
		self.win.resize_object_add(self.bx_main)
		self.bx_main.show()

		self.fr_info = Frame(self.win)
		self.fr_info.text_set("Information")
		self.bx_main.pack_end(self.fr_info)
		self.fr_info.show()

		self.lb = Label(self.win)
		self.lb.text_set(self.file.name)
		self.fr_info.content_set(self.lb)
		self.lb.show()

		#self.bt_archive = Button(self.win, text="make archive")
		#self.bt_archive.callback_clicked_add(self.make_archive)
		#self.bx_main.pack_end(self.bt_archive)
		#self.bt_archive.show()

		self.bt_extract = Button(self.win, text="extract")
		self.bt_extract.callback_clicked_add(self.extract)
		self.bx_main.pack_end(self.bt_extract)
		self.bt_extract.show()

		self.win.show()

	def destroy(self, obj):
		elementary.exit()

	def make_archive(self, obj):
		print ("TODO: Make archive")
		elementary.exit()

	def extract(self, obj):
		if self.file.type == "application/tar.gz" or self.file.type == "application/x-gzip":
			cmd(cmd="tar", arg="xzf "+self.file.name)
		elif self.file.type == "application/bz2" or self.file.type == "application/x-bz2":
			cmd(cmd="bunzip2", arg=self.file.name)
		elif self.file.type == "application/rar" or self.file.type == "application/x-rar":
			cmd(cmd="unrar", arg="x "+self.file.name)
		elif self.file.type == "application/gz" or self.file.type == "application/x-gz":
			cmd(cmd="gunzip", arg=self.file.name)
		elif self.file.type == "application/tar" or self.file.type == "application/x-tar":
			cmd(cmd="tar", arg="xf "+self.file.name)
		elif self.file.type == "application/tbz2" or self.file.type == "application/tar.bz2":
			cmd(cmd="tar", arg="xjf "+self.file.name)
		elif self.file.type == "application/tgz" or self.file.type == "application/zip" or self.file.type == "application/x-zip":
			cmd(cmd="unzip", arg=self.file.name)
		elif self.file.type == "application/Z":
			cmd(cmd="uncompress", arg=self.file.name)
		else:
			print(self.file.type + " cannot be extracted")

		elementary.exit()

class File(object):
	def __init__(self):
		self.name = cmdline()
		self.name = self.name.replace("file://","")
		self.magic = magic.open(magic.MAGIC_MIME_TYPE)
		self.magic.load()
		self.type = self.magic.file(self.name)

def cmd(cmd="", arg=""):
	# TODO:
	# check if cmd exist
	# Execute cmd with opt
	t = os.system("which "+cmd)
	if t == 0:
		os.system(cmd+" "+arg)
	else:
		print ("Mimetype not supported")

def cmdline():
	file = sys.argv[1]
	return file

if __name__ == "__main__":

	elementary.init()
	packet = Application()
	elementary.run()
	elementary.shutdown()
