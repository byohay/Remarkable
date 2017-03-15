#!usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2017 <Ben Yohay> <benyohay91@gmail.com>
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
### END LICENSE

from gi.repository import Gdk, GtkSource


class FindManager(object):
    def __init__(self, find_widget, wrap_widget, find_box_widget,
                 replace_box_widget, match_case_checkbox,
                 whole_word_checkbox, regex_checkbox):
        self.widget = find_widget
        self.search_context = None
        self.wrap_widget = wrap_widget
        self.find_box_widget = find_box_widget
        self.replace_box_widget = replace_box_widget
        self.is_searching_backwards = False
        self.text_view = None

        self.search_settings = GtkSource.SearchSettings()
        match_case_checkbox.bind_property('active', self.search_settings, 'case-sensitive')
        whole_word_checkbox.bind_property('active', self.search_settings, 'at-word-boundaries')
        regex_checkbox.bind_property('active', self.search_settings, 'regex-enabled')
        self.find_box_widget.bind_property('text', self.search_settings, 'search-text')

        self.search_settings.set_wrap_around(True)
        self.widget.connect('key-press-event', self.on_find_bar_key_press)
        self.find_box_widget.connect('key-press-event', self.on_find_box_key_press)
        self.find_box_widget.connect('key-release-event', self.on_find_box_key_release)

    def on_find_bar_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()

    def on_find_box_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            self._find_text(backwards=self.is_searching_backwards)
        elif event.keyval == Gdk.KEY_Shift_R or event.keyval == Gdk.KEY_Shift_L:
            self.is_searching_backwards = True

    def on_find_box_key_release(self, widget, event):
        if event.keyval == Gdk.KEY_Shift_R or event.keyval == Gdk.KEY_Shift_L:
            self.is_searching_backwards = False

    def hide(self):
        # self.wrap_widget.set_visible(False)
        self.widget.hide()
        self.search_context.set_highlight(False)

    def show(self):
        # self.wrap_widget.set_visible(True)
        self.find_box_widget.grab_focus()
        self.search_context.set_highlight(True)
        self.widget.show()

    def set_text_view(self, text_view):
        self.text_view = text_view
        if text_view is not None:
            self.search_context = GtkSource.SearchContext.new(
                text_view.get_buffer(),
                self.search_settings
            )
            self.search_context.set_highlight(True)
        else:
            self.search_context = None

    def on_find_next_button_clicked(self, button):
        self._find_text()

    def on_find_previous_button_clicked(self, button):
        self._find_text(backwards=True)

    def on_find_box_text_changed(self, find_box):
        self._find_text(start_at=0)

    def on_replace_button_clicked(self, replace_box):
        buffer = self.text_view.get_buffer()
        current_selection = buffer.get_selection_bounds()
        is_found = self._find_text(start_at=0)
        if not is_found:
            return
        if self._is_currently_on_matched_text(buffer, current_selection):
            self.search_context.replace(
                current_selection[0],
                current_selection[1],
                self.replace_box_widget.get_text(),
                -1
            )
            self._find_text(start_at=0)

    def _is_currently_on_matched_text(self, buffer, current_selection):
        new_selection = buffer.get_selection_bounds()
        return current_selection[0].equal(new_selection[0]) and \
            current_selection[1].equal(new_selection[1])

    def on_replace_all_button_clicked(self, replace_box):
        self.search_context.replace_all(
            self.replace_box_widget.get_text(),
            -1
        )

    def _find_text(self, backwards=False, start_at=1):
        buffer = self.text_view.get_buffer()
        current_pos_iter = buffer.get_iter_at_mark(buffer.get_insert())
        self.find_box_widget.get_style_context().remove_class("text_not_found")
        # self.wrap_widget.set_visible(False)

        if backwards:
            was_found, match_start, match_end = \
                self.search_context.backward(current_pos_iter)
            # if was_found and match_start.get_offset() > current_pos_iter.get_offset():
                # self.wrap_widget.set_visible(True)
        else:
            current_pos_iter.forward_chars(start_at)
            was_found, match_start, match_end = \
                self.search_context.forward(current_pos_iter)
            # if was_found and match_start.get_offset() < current_pos_iter.get_offset():
                # self.wrap_widget.set_visible(True)

        if not was_found:
            buffer.place_cursor(current_pos_iter)
            self.find_box_widget.get_style_context().add_class("text_not_found")
            return False

        buffer.place_cursor(match_start)
        buffer.move_mark(buffer.get_selection_bound(), match_end)
        self.text_view.scroll_to_mark(buffer.get_insert(), 0.25, True, 0.5, 0.5)
        return True
