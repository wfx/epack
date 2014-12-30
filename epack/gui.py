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

from efl import ecore
from efl import elementary
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl.elementary.window import StandardWindow
from efl.elementary.innerwindow import InnerWindow
from efl.elementary.box import Box
from efl.elementary.ctxpopup import Ctxpopup
from efl.elementary.entry import Entry
from efl.elementary.icon import Icon
from efl.elementary.label import Label
from efl.elementary.frame import Frame
from efl.elementary.genlist import Genlist, GenlistItemClass, \
    ELM_GENLIST_ITEM_TREE
from efl.elementary.button import Button
from efl.elementary.table import Table
from efl.elementary.check import Check
from efl.elementary.fileselector_button import FileselectorButton
from efl.elementary.fileselector import Fileselector
from efl.elementary.popup import Popup
from efl.elementary.progressbar import Progressbar
from efl.elementary.separator import Separator

from epack.utils import pkg_resource_get, xdg_open, \
    VERSION, LICENSE, AUTHORS, INFO, GITHUB


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
EXPAND_VERT = 0.0, EVAS_HINT_EXPAND
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.0
FILL_VERT = 0.0, EVAS_HINT_FILL


def gl_fold_text_get(obj, part, item_data):
    return item_data[:-1].split('/')[-1]

def gl_fold_icon_get(obj, part, item_data):
    return Icon(obj, standard='folder')

def gl_file_text_get(obj, part, item_data):
    return item_data.split('/')[-1]


class MainWin(StandardWindow):
    def __init__(self, app):
        self.app = app
        self.post_extract_action = 'close' # or 'fm' or 'term'

        # the window
        StandardWindow.__init__(self, 'epack.py', 'Epack')
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: elementary.exit())

        # main vertical box
        vbox = Box(self, size_hint_weight=EXPAND_BOTH)
        self.resize_object_add(vbox)
        vbox.show()

        ### header horiz box (inside a padding frame)
        frame = Frame(self, style='pad_medium',
                      size_hint_weight=EXPAND_HORIZ,
                      size_hint_align=FILL_HORIZ)
        vbox.pack_end(frame)
        frame.show()

        self.header_box = Box(self, horizontal=True,
                              size_hint_weight=EXPAND_HORIZ,
                              size_hint_align=FILL_HORIZ)
        frame.content = self.header_box
        self.header_box.show()

        # genlist with archive content
        self.file_itc = GenlistItemClass(item_style="no_icon",
                                         text_get_func=gl_file_text_get)
        self.fold_itc = GenlistItemClass(item_style="one_icon",
                                         text_get_func=gl_fold_text_get,
                                         content_get_func=gl_fold_icon_get)
        self.file_list = Genlist(self, homogeneous=True,
                                 size_hint_weight=EXPAND_BOTH,
                                 size_hint_align=FILL_BOTH)
        self.file_list.callback_expand_request_add(self._gl_expand_req_cb)
        self.file_list.callback_contract_request_add(self._gl_contract_req_cb)
        self.file_list.callback_expanded_add(self._gl_expanded_cb)
        self.file_list.callback_contracted_add(self._gl_contracted_cb)
        vbox.pack_end(self.file_list)
        self.file_list.show()

        ### footer table (inside a padding frame)
        frame = Frame(self, style='pad_medium',
                      size_hint_weight=EXPAND_HORIZ,
                      size_hint_align=FILL_HORIZ)
        vbox.pack_end(frame)
        frame.show()
        
        table = Table(frame)
        frame.content = table
        table.show()

        # FileSelectorButton
        self.fsb = DestinationButton(self)
        self.fsb.callback_file_chosen_add(self.chosen_folder_cb)
        table.pack(self.fsb, 0, 0, 3, 1)
        self.fsb.show()

        sep = Separator(table, horizontal=True,
                        size_hint_weight=EXPAND_HORIZ)
        table.pack(sep, 0, 1, 3, 1)
        sep.show()

        # extract button
        btn_box = Box(table, horizontal=True)
        table.pack(btn_box, 0, 2, 1, 2)
        btn_box.show()
        
        self.btn1 = Button(table, text='Extract')
        self.btn1.callback_clicked_add(self.extract_btn_cb)
        btn_box.pack_end(self.btn1)
        self.btn1.show()

        ic = Icon(table, standard='arrow_up', size_hint_min=(17,17))
        self.btn2 = Button(table, content=ic)
        self.btn2.callback_clicked_add(self.extract_opts_cb)
        btn_box.pack_end(self.btn2)
        self.btn2.show()

        sep = Separator(table, horizontal=False)
        table.pack(sep, 1, 2, 1, 2)
        sep.show()

        # delete-archive checkbox
        self.del_chk = Check(table, text="Delete archive after extraction",
                             size_hint_weight=EXPAND_HORIZ,
                             size_hint_align=(0.0, 1.0))
        self.del_chk.callback_changed_add(self.del_check_cb)
        table.pack(self.del_chk, 2, 2, 1, 1)
        self.del_chk.show()

        # create-archive-folder checkbox
        self.create_folder_chk = Check(table, text="Create archive folder",
                                       size_hint_weight=EXPAND_HORIZ,
                                       size_hint_align=(0.0, 1.0))
        table.pack(self.create_folder_chk, 2, 3, 1, 1)
        self.create_folder_chk.callback_changed_add(
                               lambda c: self.update_fsb_label())
        self.create_folder_chk.show()

        # set the correct ui state
        self.update_ui()

        # show the window
        self.resize(300, 300)
        self.show()

    def del_check_cb(self, check):
        self.app.delete_after_extract = check.state

    def extract_opts_cb(self, bt):
        ctx = Ctxpopup(self, hover_parent=self)
        ctx.item_append('Extract and open FileManager', None,
                        self.change_post_extract_action, 'fm')
        ctx.item_append('Extract and open in Terminal', None,
                        self.change_post_extract_action, 'term')
        ctx.item_append('Extract and close', None,
                        self.change_post_extract_action, 'close')
        x, y, w, h = bt.geometry
        ctx.pos = (x + w / 2, y)
        ctx.show()

    def change_post_extract_action(self, ctx, item, action):
        self.post_extract_action = action
        if action == 'fm':
            self.btn1.text = 'Extract and open FileManager'
        elif action == 'term':
            self.btn1.text = 'Extract and open in Terminal'
        elif action == 'close':
            self.btn1.text = 'Extract'
        ctx.delete()

    def update_ui(self, listing_in_progress=False):
        self.header_box.clear()
        ui_disabled = True

        # file listing in progress
        if listing_in_progress:
            spin = Progressbar(self, style="wheel", pulse_mode=True)
            spin.pulse(True)
            spin.show()
            self.header_box.pack_end(spin)

            lb = Label(self, text="Reading archive, please wait...",
                       size_hint_weight=EXPAND_HORIZ,
                       size_hint_align=(0.0, 0.5))
            lb.show()
            self.header_box.pack_end(lb)

        # no archive loaded
        elif self.app.file_name is None:
            bt = Button(self, text='No archive loaded, click to choose a file',
                        size_hint_weight=EXPAND_HORIZ)
            bt.callback_clicked_add(lambda b: FileChooserWin(self.app))
            self.header_box.pack_end(bt)
            bt.show()

        # normal operation (archive loaded and listed)
        else:
            txt = "<b>Archive:</b> %s" % (os.path.basename(self.app.file_name))
            lb = Label(self, text=txt, size_hint_weight=EXPAND_HORIZ,
                       size_hint_align=(0.0, 0.5))
            self.header_box.pack_end(lb)
            lb.show()
            ui_disabled = False

        # always show the about button
        sep = Separator(self)
        self.header_box.pack_end(sep)
        sep.show()

        ic = Icon(self, standard='info', size_hint_min=(20,20))
        ic.callback_clicked_add(lambda i: InfoWin())
        self.header_box.pack_end(ic)
        ic.show()

        for widget in (self.btn1, self.btn2, self.fsb,
                       self.create_folder_chk, self.del_chk):
            widget.disabled = ui_disabled

        self.update_fsb_label()

    def update_fsb_label(self):
        if self.create_folder_chk.state is True:
            name = os.path.splitext(os.path.basename(self.app.file_name))[0]
            self.fsb.text = os.path.join(self.app.dest_folder, name)
        else:
            self.fsb.text = self.app.dest_folder or ''

    def show_error_msg(self, msg):
        pop = Popup(self, text=msg)
        pop.part_text_set('title,text', 'Error')

        btn = Button(self, text='Continue')
        btn.callback_clicked_add(lambda b: pop.delete())
        pop.part_content_set('button1', btn)

        btn = Button(self, text='Exit')
        btn.callback_clicked_add(lambda b: elementary.exit())
        pop.part_content_set('button2', btn)

        pop.show()

    def chosen_folder_cb(self, fsb, folder):
        if folder:
            self.app.dest_folder = folder
            self.update_fsb_label()

    def tree_populate(self, file_list=None, parent=None):
        if file_list is not None:
            self._file_list = file_list

        if parent is None:
            prefix = None # items must match this prefix to be listed
            fscount = 0   # folder must have this number of slashes
            dscount = 1   # files must have this number of slashes
        else:
            prefix = parent.data[:-1]
            fscount = prefix.count('/') + 1
            dscount = fscount + 1

        files = []
        for path in self._file_list:
            if prefix and not path.startswith(prefix):
                continue

            if path.endswith('/'):
                if path.count('/') == dscount:
                    self.file_list.item_append(self.fold_itc, path, parent,
                                               flags=ELM_GENLIST_ITEM_TREE)
            else:
                if path.count('/') == fscount:
                    files.append(path)

        for path in files:
            self.file_list.item_append(self.file_itc, path, parent)

    def _gl_expand_req_cb(self, gl, item):
        item.expanded = True

    def _gl_expanded_cb(self, gl, item):
        self.tree_populate(None, item)

    def _gl_contract_req_cb(self, gl, item):
        item.expanded = False

    def _gl_contracted_cb(self, gl, item):
        item.subitems_clear()

    def extract_btn_cb(self, btn):
        self.prog_popup = None
        self.app.dest_folder = self.fsb.text
        self.app.extract_archive()

    def build_prog_popup(self):
        pp = Popup(self)
        pp.part_text_set('title,text', 'Extracting files, please wait...')
        pp.show()

        vbox = Box(self)
        pp.part_content_set('default', vbox)
        vbox.show()

        lb = Label(self, ellipsis=True, size_hint_weight=EXPAND_HORIZ,
                   size_hint_align=FILL_HORIZ)
        vbox.pack_end(lb)
        lb.show()

        pb = Progressbar(pp, size_hint_weight=EXPAND_HORIZ,
                         size_hint_align=FILL_HORIZ)
        vbox.pack_end(pb)
        pb.show()

        bt = Button(pp, text='Cancel', disabled=True)
        # TODO make the button actually work
        pp.part_content_set('button1', bt)

        self.prog_pbar = pb
        self.prog_label = lb
        self.prog_popup = pp

    def extract_progress(self, progress, cur_name):
        if self.prog_popup is None:
            self.build_prog_popup()

        self.prog_pbar.value = progress
        self.prog_label.text = cur_name

    def extract_finished(self):
        if self.prog_popup:
            self.prog_popup.delete()
            self.prog_popup = None


class InfoWin(StandardWindow):
    def __init__(self):
        StandardWindow.__init__(self, 'epack', 'Epack', autodel=True)

        fr = Frame(self, style='pad_large', size_hint_weight=EXPAND_BOTH,
                   size_hint_align=FILL_BOTH)
        self.resize_object_add(fr)
        fr.show()

        hbox = Box(self, horizontal=True, padding=(12,12))
        fr.content = hbox
        hbox.show()

        vbox = Box(self, align=(0.0,0.0), padding=(6,6),
                   size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)
        hbox.pack_end(vbox)
        vbox.show()

        # icon + version
        ic = Icon(self, file=pkg_resource_get('epack64.png'),
                  aspect_fixed=True, resizable=(False, False))
        vbox.pack_end(ic)
        ic.show()

        lb = Label(self, text='Version: %s' % VERSION)
        vbox.pack_end(lb)
        lb.show()

        sep = Separator(self, horizontal=True)
        vbox.pack_end(sep)
        sep.show()

        # buttons
        bt = Button(self, text='Epack', size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(INFO))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text='Website',size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: xdg_open(GITHUB))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text='Authors', size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(AUTHORS))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text='License', size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(LICENSE))
        vbox.pack_end(bt)
        bt.show()

        # main text
        self.entry = Entry(self, editable=False, scrollable=True, text=INFO,
                        size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.entry.callback_anchor_clicked_add(lambda e,i: xdg_open(i.name))
        hbox.pack_end(self.entry)
        self.entry.show()

        self.resize(400, 200)
        self.show()


class DestinationButton(FileselectorButton):
    def __init__(self, parent):
        FileselectorButton.__init__(self, parent,
                    inwin_mode=False, folder_only=True,
                    size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        self._text = ''

        box = Box(self, horizontal=True, padding=(3,0))
        self.content = box
        box.show()

        icon = Icon(box, standard='folder', size_hint_min=(16,16))
        box.pack_end(icon)
        icon.show()

        self.label = Label(box, ellipsis=True,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_HORIZ)
        box.pack_end(self.label)
        self.label.show()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self.label.text = '<align=left>%s</align>' % text


class FileChooserWin(StandardWindow):
    def __init__(self, app):
        self.app = app
        StandardWindow.__init__(self, 'epack.py', 'Choose an archive')
        self.callback_delete_request_add(lambda o: self.delete())

        fs = Fileselector(self, expandable=False,
                          path=os.path.expanduser('~'),
                          size_hint_weight=EXPAND_BOTH,
                          size_hint_align=FILL_BOTH)
        fs.callback_done_add(self.done_cb)
        fs.callback_activated_add(self.done_cb)
        # TODO this filter seems not to work well...need fixing
        # fs.mime_types_filter_append(list(EXTRACT_MAP.keys()), 'Archive files')
        # fs.mime_types_filter_append(['*'], 'All files')
        fs.show()

        self.resize_object_add(fs)
        self.resize(300, 400)
        self.show()

    def done_cb(self, fs, path):
        if path is None:
            self.delete()
        elif os.path.isfile(path):
            self.app.load_file(path)
            self.delete()


