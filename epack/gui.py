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
from efl import evas
from efl import elementary
from efl.evas import EXPAND_BOTH, EXPAND_HORIZ, EXPAND_VERT, \
    FILL_BOTH, FILL_HORIZ, FILL_VERT
from efl.elementary.window import StandardWindow, DialogWindow
from efl.elementary.innerwindow import InnerWindow
from efl.elementary.box import Box
from efl.elementary.entry import Entry
from efl.elementary.icon import Icon
from efl.elementary.label import Label
from efl.elementary.frame import Frame
from efl.elementary.genlist import Genlist, GenlistItemClass, \
    ELM_GENLIST_ITEM_TREE
from efl.elementary.button import Button
from efl.elementary.table import Table
from efl.elementary.check import Check
from efl.elementary.fileselector import Fileselector
from efl.elementary.popup import Popup
from efl.elementary.progressbar import Progressbar
from efl.elementary.separator import Separator

from epack import __version__
import epack.utils as utils


class SafeIcon(Icon):
    def __init__(self, parent, icon_name, **kargs):
        Icon.__init__(self, parent, **kargs)
        try:
            self.standard = icon_name
        except:
            print("ERROR: Cannot find icon: '%s'" % icon_name)


class MainWin(StandardWindow):
    def __init__(self, app):
        self.app = app
        self.prog_popup = None

        # the window
        StandardWindow.__init__(self, 'epack', 'Epack')
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: self.app.exit())

        ### main table (inside a padding frame)
        frame = Frame(self, style='pad_small',
                      size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.resize_object_add(frame)
        frame.content = table = Table(frame)
        frame.show()

        ### header horiz box
        self.header_box = Box(self, horizontal=True,
                              size_hint_weight=EXPAND_HORIZ,
                              size_hint_align=FILL_HORIZ)
        table.pack(self.header_box, 0, 0, 3, 1)
        self.header_box.show()

        # genlist with archive content (inside a small padding frame)
        frame = Frame(self, style='pad_small',
                      size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        table.pack(frame, 0, 1, 3, 1)

        self.file_itc = GenlistItemClass(item_style="no_icon",
                                         text_get_func=self._gl_file_text_get)
        self.fold_itc = GenlistItemClass(item_style="one_icon",
                                         text_get_func=self._gl_fold_text_get,
                                         content_get_func=self._gl_fold_icon_get)
        self.file_list = Genlist(frame, homogeneous=True)
        self.file_list.callback_expand_request_add(self._gl_expand_req_cb)
        self.file_list.callback_contract_request_add(self._gl_contract_req_cb)
        self.file_list.callback_expanded_add(self._gl_expanded_cb)
        self.file_list.callback_contracted_add(self._gl_contracted_cb)
        frame.content = self.file_list
        frame.show()

        # rect hack to force a min size on the genlist
        r = evas.Rectangle(table.evas, size_hint_min=(250, 250),
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        table.pack(r, 0, 1, 3, 1)

        # FileSelectorButton
        self.fsb = DestinationButton(app, self)
        table.pack(self.fsb, 0, 2, 3, 1)
        self.fsb.show()

        sep = Separator(table, horizontal=True,
                        size_hint_weight=EXPAND_HORIZ)
        table.pack(sep, 0, 3, 3, 1)
        sep.show()

        # extract button
        self.extract_btn = Button(table, text=_('Extract'))
        self.extract_btn.callback_clicked_add(self.extract_btn_cb)
        table.pack(self.extract_btn, 0, 4, 1, 2)
        self.extract_btn.show()

        sep = Separator(table, horizontal=False)
        table.pack(sep, 1, 4, 1, 2)
        sep.show()

        # delete-archive checkbox
        self.del_chk = Check(table, text=_('Delete archive after extraction'),
                             size_hint_weight=EXPAND_HORIZ,
                             size_hint_align=(0.0, 1.0))
        self.del_chk.callback_changed_add(self.del_check_cb)
        table.pack(self.del_chk, 2, 4, 1, 1)
        self.del_chk.show()

        # create-archive-folder checkbox
        self.create_folder_chk = Check(table, text=_('Create archive folder'),
                                       size_hint_weight=EXPAND_HORIZ,
                                       size_hint_align=(0.0, 1.0))
        table.pack(self.create_folder_chk, 2, 5, 1, 1)
        self.create_folder_chk.callback_changed_add(
                               lambda c: self.update_fsb_label())
        self.create_folder_chk.show()

        # set the correct ui state
        self.update_ui()

        # show the window
        self.show()

    def del_check_cb(self, check):
        self.app.delete_after_extract = check.state

    def update_ui(self, listing_in_progress=False):
        box = self.header_box
        box.clear()
        ui_disabled = True

        # file listing in progress
        if listing_in_progress:
            spin = Progressbar(box, style='wheel', pulse_mode=True)
            spin.pulse(True)
            spin.show()
            box.pack_end(spin)

            lb = Label(box, text=_('Reading archive, please wait...'),
                       size_hint_weight=EXPAND_HORIZ,
                       size_hint_align=(0.0, 0.5))
            lb.show()
            box.pack_end(lb)

        # or header button
        else:
            if self.app.file_name is None:
                txt = _('No archive loaded, click to choose a file')
            else:
                ui_disabled = False
                txt = _('<b>Archive:</b> %s') % \
                      (os.path.basename(self.app.file_name))

            lb = Label(box, text='<align=left>%s</align>' % txt)
            bt = Button(box, content=lb, size_hint_weight=EXPAND_HORIZ,
                        size_hint_fill=FILL_HORIZ)
            bt.callback_clicked_add(lambda b: \
                        FileSelectorInwin(self, _('Choose an archive'),
                                          self._archive_selected_cb,
                                          path=os.getcwd()))
            box.pack_end(bt)
            bt.show()

        # always show the about button
        sep = Separator(box)
        box.pack_end(sep)
        sep.show()

        ic = SafeIcon(box, 'dialog-information', size_hint_min=(24,24))
        ic.callback_clicked_add(lambda i: InfoWin(self))
        box.pack_end(ic)
        ic.show()

        for widget in (self.extract_btn, self.fsb,
                       self.create_folder_chk, self.del_chk):
            widget.disabled = ui_disabled

        self.update_fsb_label()

    def _archive_selected_cb(self, path):
        if os.path.isfile(path):
            self.app.load_file(path)

    def update_fsb_label(self):
        if self.create_folder_chk.state is True:
            name = os.path.splitext(os.path.basename(self.app.file_name))[0]
            self.fsb.text = os.path.join(self.app.dest_folder, name)
        else:
            self.fsb.text = self.app.dest_folder or ''

    def show_error_msg(self, msg):
        pop = Popup(self, text=msg)
        pop.part_text_set('title,text', _('Error'))

        btn = Button(self, text=_('Continue'))
        btn.callback_clicked_add(lambda b: pop.delete())
        pop.part_content_set('button1', btn)

        btn = Button(self, text=_('Exit'))
        btn.callback_clicked_add(lambda b: self.app.exit())
        pop.part_content_set('button2', btn)

        pop.show()

    def tree_populate(self, file_list=None, parent=None):
        if file_list is not None:
            self.file_list.clear()
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

    def _gl_fold_text_get(self, obj, part, item_data):
        return item_data[:-1].split('/')[-1]

    def _gl_fold_icon_get(self, obj, part, item_data):
        return SafeIcon(obj, 'folder')

    def _gl_file_text_get(self, obj, part, item_data):
        return item_data.split('/')[-1]

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
        pp.part_text_set('title,text', _('Extracting files, please wait...'))
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

        bt = Button(pp, text=_('Cancel'))
        bt.callback_clicked_add(lambda b: self.app.abort_operation())
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

    def _open_fm_and_exit_cb(self, bt):
        utils.xdg_open(self.app.dest_folder)
        self.app.exit()

    def _open_term_and_exit_cb(self, bt):
        utils.open_in_terminal(self.app.dest_folder)
        self.app.exit()

    def ask_what_to_do_next(self):
        pop = Popup(self)
        pop.part_text_set('title,text', _('Extract completed'))

        box = Box(pop)
        pop.content = box
        box.show()

        lb = Label(pop, text=_('What to do next?'),
                   size_hint_align=FILL_HORIZ)
        box.pack_end(lb)
        lb.show()

        btn = Button(pop, text=_('Open Filemanager'),
                     size_hint_align=FILL_HORIZ)
        btn.callback_clicked_add(self._open_fm_and_exit_cb)
        box.pack_end(btn)
        btn.show()

        btn = Button(pop, text=_('Open Terminal'),
                     size_hint_align=FILL_HORIZ)
        btn.callback_clicked_add(self._open_term_and_exit_cb)
        box.pack_end(btn)
        btn.show()

        btn = Button(pop, text=_('Close this popup'),
                     size_hint_align=FILL_HORIZ)
        btn.callback_clicked_add(lambda b: pop.delete())
        box.pack_end(btn)
        btn.show()

        btn = Button(pop, text=_('Exit'),
                     size_hint_align=FILL_HORIZ)
        btn.callback_clicked_add(lambda b: self.app.exit())
        box.pack_end(btn)
        btn.show()

        pop.show()


class InfoWin(DialogWindow):
    def __init__(self, parent):
        DialogWindow.__init__(self, parent, 'epack-info', 'Epack', autodel=True)

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
        ic = SafeIcon(self, 'epack', size_hint_min=(64,64))
        vbox.pack_end(ic)
        ic.show()

        lb = Label(self, text=_('Version: %s') % __version__)
        vbox.pack_end(lb)
        lb.show()

        sep = Separator(self, horizontal=True)
        vbox.pack_end(sep)
        sep.show()

        # buttons
        bt = Button(self, text=_('Epack'), size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.INFO))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text=_('Website'),size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: utils.xdg_open(utils.GITHUB))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text=_('Authors'), size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.AUTHORS))
        vbox.pack_end(bt)
        bt.show()

        bt = Button(self, text=_('License'), size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.LICENSE))
        vbox.pack_end(bt)
        bt.show()

        # main text
        self.entry = Entry(self, editable=False, scrollable=True, text=utils.INFO,
                        size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.entry.callback_anchor_clicked_add(lambda e,i: utils.xdg_open(i.name))
        hbox.pack_end(self.entry)
        self.entry.show()

        self.resize(400, 200)
        self.show()


class DestinationButton(Button):
    def __init__(self, app, parent):
        self.app = app
        self._text = ''

        Button.__init__(self, parent,size_hint_weight=EXPAND_HORIZ,
                                     size_hint_align=FILL_HORIZ)
        self.callback_clicked_add(self._btn_clicked_cb)

        box = Box(self, horizontal=True, padding=(3,0))
        self.content = box
        box.show()

        icon = SafeIcon(box, 'folder', size_hint_min=(16,16))
        box.pack_end(icon)
        icon.show()

        self.label = Label(box, ellipsis=True,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_HORIZ)
        box.pack_end(self.label)
        self.label.show()

    def _btn_clicked_cb(self, btn):
        if os.path.isdir(self._text):
            path = self._text
        elif os.path.isdir(os.path.dirname(self._text)):
            path = os.path.dirname(self._text)
        else:
            path = os.getcwd()
        FileSelectorInwin(self.app.main_win, _('Choose destination'),
                          self._fs_done_cb, folder_only=True,
                          path=path)

    def _fs_done_cb(self, path):
        if path:
            self.app.dest_folder = path
            self.app.main_win.update_fsb_label()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self.label.text = '<align=left>%s</align>' % text


class FileSelectorInwin(Fileselector):
    def __init__(self, parent, title, done_cb, **kargs):
        self._user_cb = done_cb

        self._inwin = InnerWindow(parent)

        vbox = Box(self._inwin)
        self._inwin.content = vbox
        vbox.show()

        lb = Label(vbox, text='<b>%s</b>' % title)
        vbox.pack_end(lb)
        lb.show()

        Fileselector.__init__(self, vbox, expandable=False,
                              size_hint_weight=EXPAND_BOTH,
                              size_hint_align=FILL_BOTH, **kargs)
        self.callback_done_add(self._fileselector_done_cb)
        self.callback_activated_add(self._fileselector_done_cb)
        # TODO this filter seems not to work well...need fixing
        # fs.mime_types_filter_append(list(EXTRACT_MAP.keys()), 'Archive files')
        # fs.mime_types_filter_append(['*'], 'All files')
        vbox.pack_end(self)
        self.show()

        self._inwin.activate()

    def delete(self):
        self._inwin.delete()

    def _fileselector_done_cb(self, fs, path):
        if path is not None:
            self._user_cb(path)
        self.delete()
