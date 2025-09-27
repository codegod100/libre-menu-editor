#!/usr/bin/python3

# Copyright (C) 2022 Free Software Foundation, Inc.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from modules import basic
import os
import threading
import subprocess
import gi
import re
gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Pango", "1.0")
from gi.repository import Pango
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Adw


class Timeout():
    DEFAULT = 2


class Spacing():
    DEFAULT = 6
    LARGE = 11
    LARGER = 24
    LARGEST = 36


class Margin():
    SMALLEST = 2
    DEFAULT = 6
    LARGE = 11
    LARGER = 24
    LARGEST = 36


class Keyval():
    ENTER = 65293
    TAB = 65289
    ESCAPE = 65307
    LEFT = 65361
    UP = 65362
    RIGHT = 65363
    DOWN = 65364
    PAGEUP = 65365
    PAGEDOWN = 65366
    F2 = 65471


class IconNotFoundError(Exception):
    pass


class IconFinder():
    def __init__(self, app):
        self._events = basic.EventManager()
        self._events.add("changed", object)
        self._ignore_prefix = None
        self._application = app
        self._application_window = app.get_application_window()
        self._alternatives = {}
        self._legacy_icons = {}
        self._icon_theme = Gtk.IconTheme.get_for_display(self._application_window.get_display())
        self._icon_theme.connect("changed", self._on_icon_theme_changed)
        self._load_legacy_icons(*self._icon_theme.get_search_path())

    def _on_icon_theme_changed(self, icon_theme):
        self._events.trigger("changed", self)

    def _load_legacy_icons(self, *paths):
        for path in paths:
            if os.path.exists(path):
                for name in os.listdir(path):
                    icon_path = os.path.join(path, name)
                    if os.path.isfile(icon_path):
                        self._legacy_icons[".".join(name.split(".")[:-1])] = icon_path
                        self._legacy_icons[name] = icon_path

    def get_ignore_prefix(self):
        return self._ignore_prefix

    def set_ignore_prefix(self, prefix):
        self._ignore_prefix = prefix

    def get_search_paths(self):
        return self._icon_theme.get_search_path()

    def add_search_paths(self, *paths):
        for path in paths:
            if not path in self._icon_theme.get_search_path():
                self._icon_theme.add_search_path(path)
                self._load_legacy_icons(path)

    def get_alternatives(self, name):
        if name in self._alternatives:
            return list(self._alternatives[name])
        else:
            raise IconNotFoundError(name)

    def add_alternatives(self, name, *alternatives):
        if not name in self._alternatives:
            self._alternatives[name] = list(alternatives)
        else:
            for alternative in alternatives:
                self._alternatives[name].append(alternative)

    def get_image(self, icon, missing_ok=True, use_alternatives=True, allow_symbolic=True):
        image = Gtk.Image()
        self.set_image(image, icon, missing_ok=missing_ok, use_alternatives=use_alternatives,
            allow_symbolic=allow_symbolic)
        return image

    def set_image(self, image, icon, missing_ok=True, use_alternatives=True, allow_symbolic=True):
        try:
            name = self.get_name(icon, missing_ok=False, use_alternatives=use_alternatives,
                allow_symbolic=allow_symbolic)
            image.set_from_icon_name(name)
            return True
        except IconNotFoundError:
            if icon in self._legacy_icons:
                icon = self._legacy_icons[icon]
            elif not icon.endswith("-symbolic") and f"{icon}-symbolic" in self._legacy_icons:
                icon = self._legacy_icons[f"{icon}-symbolic"]
            if os.getenv("APP_RUNNING_AS_FLATPAK"):
                icon = self._application.get_flatpak_sandbox_system_path(icon)
            if os.path.exists(icon) and os.path.isfile(icon) and os.access(icon, os.R_OK):
                try:
                    texture = Gdk.Texture.new_from_filename(icon)
                except GLib.GError:
                    pass
                else:
                    image.set_from_paintable(texture)
                    return True
            elif missing_ok:
                if not os.path.sep in icon:
                    image.set_from_icon_name(icon)
                else:
                    image.set_from_file(icon)
                return False
            else:
                raise IconNotFoundError(icon)

    def get_name(self, name, missing_ok=True, use_alternatives=True, allow_symbolic=True):
        if not self._ignore_prefix or not name.startswith(self._ignore_prefix):
            theme_lookup_name = self.theme_find_name(name, allow_symbolic=allow_symbolic)
            if theme_lookup_name:
                return theme_lookup_name
            elif (
                allow_symbolic and not name.endswith("-symbolic")
                and self._icon_theme.has_icon(f"{name}-symbolic")
            ):
                return f"{name}-symbolic"
            elif use_alternatives and name in self._alternatives:
                for alternative in self._alternatives[name]:
                    if (
                        allow_symbolic and not alternative.endswith("-symbolic")
                        and self._icon_theme.has_icon(f"{alternative}-symbolic")
                    ):
                        return f"{alternative}-symbolic"
            if missing_ok:
                return name
            else:
                raise IconNotFoundError(name)
        elif missing_ok:
            return name
        else:
            raise IconNotFoundError(name)

    def has_name(self, name, use_alternatives=False, allow_symbolic=True):
        try:
            return self.get_name(name, missing_ok=False, use_alternatives=use_alternatives,
                allow_symbolic=allow_symbolic)
        except IconNotFoundError:
            return False

    def theme_find_name(self, name, allow_symbolic=True):
        if not allow_symbolic:
            alternatives = []
            if name in self._alternatives:
                alternatives = self._alternatives[name]
            paintable = self._icon_theme.lookup_icon(name, alternatives, 16, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)
            path = paintable.get_file().get_path()
            if path:
                basename = os.path.basename(path)
                for name in alternatives + [name]:
                    if basename.startswith(name):
                        return name
        elif self._icon_theme.has_icon(name):
            return name

    def get_names(self):
        names = self._icon_theme.get_icon_names()
        if self._ignore_prefix:
            return [name for name in names if not name.startswith(self._ignore_prefix)]
        else:
            return names

    def get_theme(self):
        return self._icon_theme

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class IconView(Gtk.CenterBox):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_successful = None
        self._events = basic.EventManager()
        self._events.add("updated", bool)
        self._icon_finder = app.get_icon_finder()
        self._icon_finder.hook("changed", self._on_icon_finder_changed)
        self._previous_text = ""
        self.set_image(Gtk.Image())
        self.set_hexpand(True)
        self.add_css_class("view")

    def _on_icon_finder_changed(self, event, icon_finder):
        self.update(self._previous_text)

    def _update_idle_target(self, text):
        try:
            self._icon_finder.set_image(self._icon_image, text, missing_ok=False, use_alternatives=False)
            update_successful = True
        except IconNotFoundError:
            self._icon_image.clear()
            update_successful = False
        self._update_successful = update_successful
        self._events.trigger("updated", update_successful)

    def get_image(self):
        return self._icon_image

    def set_image(self, image):
        self._icon_image = image
        self._icon_image.set_pixel_size(128)
        self._icon_image.set_margin_top(Margin.LARGER)
        self._icon_image.set_margin_bottom(Margin.LARGER)
        self.set_center_widget(self._icon_image)

    def get_update_successful(self):
        return self._update_successful

    def update(self, text):
        self._previous_text = text
        GLib.idle_add(self._update_idle_target, text)

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class IconName(GObject.Object):
    name = GObject.Property(type=str)

    def __init__(self, name):
        super().__init__()
        self.name = name


class FlowingToolbar(Gtk.Box):
    def __init__(self, max_child_width=540, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collapse_condition = None
        self._expand_condition = None
        self._max_child_width = max_child_width
        self._resize_frame = ResizeFrame()
        self._resize_frame.hook("resized", self._on_resize_frame_resized)
        self._start_clamp = Adw.Clamp()
        self._end_clamp = Adw.Clamp()
        self._spacer_child = Gtk.Box()
        self._spacer_child.set_hexpand(True)
        self._spacer_child.set_halign(Gtk.Align.FILL)
        self.set_spacing(Spacing.DEFAULT)
        self._content_box = Gtk.CenterBox()
        self._content_box.set_margin_top(Margin.LARGE)
        self._content_box.set_margin_bottom(Margin.LARGE)
        self._content_box.set_margin_start(Margin.LARGE)
        self._content_box.set_margin_end(Margin.LARGE)
        self._content_box.set_start_widget(self._start_clamp)
        self._content_box.set_center_widget(self._spacer_child)
        self._content_box.set_end_widget(self._end_clamp)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(self._resize_frame)
        self.append(self._content_box)
        self.set_margin_top = self._content_box.set_margin_top
        self.set_margin_bottom = self._content_box.set_margin_bottom
        self.set_margin_start = self._content_box.set_margin_start
        self.set_margin_end = self._content_box.set_margin_end
        self.get_margin_top = self._content_box.get_margin_top
        self.get_margin_bottom = self._content_box.get_margin_bottom
        self.get_margin_start = self._content_box.get_margin_start
        self.get_margin_end = self._content_box.get_margin_end
        self._update_clamps()

    def _on_resize_frame_resized(self, event, width, height):
        self._update_clamps()

    def _update_clamps(self):
        width = self._resize_frame.get_width()
        collapse = width < (
            (self._max_child_width * 2) +
            self._content_box.get_margin_start() +
            self._content_box.get_margin_end() +
            self.get_spacing()
        )
        GLib.idle_add(self._after_update_clamps, width, collapse, priority=GLib.PRIORITY_LOW)

    def _after_update_clamps(self, width, collapse):
        if collapse and self.get_can_collapse():
            self._content_box.set_orientation(Gtk.Orientation.VERTICAL)
        elif not collapse and self.get_can_expand():
            self._content_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        if self._content_box.get_orientation() == Gtk.Orientation.VERTICAL:
            clamp_child_width = width * 2
        else:
            clamp_child_width = self._max_child_width
        self._start_clamp.set_maximum_size(clamp_child_width)
        self._end_clamp.set_maximum_size(clamp_child_width)
        self._start_clamp.set_tightening_threshold(clamp_child_width)
        self._end_clamp.set_tightening_threshold(clamp_child_width)

    def _check_callable(self, func):
        if not callable(func):
            raise TypeError(f"not callable: {func}")

    def get_max_child_width(self):
        return self._max_child_width

    def set_max_child_width(self, value):
        self._max_child_width = value
        self._update_clamps()

    def get_spacing(self):
        return self._spacer_child.get_property("width-request")

    def set_spacing(self, spacing):
        self._spacer_child.set_property("width-request", spacing)
        self._spacer_child.set_property("height-request", spacing)

    def set_start_widget(self, widget):
        self._start_clamp.set_child(widget)

    def set_end_widget(self, widget):
        self._end_clamp.set_child(widget)

    def set_collapse_condition(self, func):
        self._check_callable(func)
        self._collapse_condition = func

    def set_expand_condition(self, func):
        self._check_callable(func)
        self._expand_condition = func

    def get_can_collapse(self):
        if self._collapse_condition:
            return self._collapse_condition()
        else:
            return True

    def get_can_expand(self):
        if self._expand_condition:
            return self._expand_condition()
        else:
            return True


class LabeledImage(Gtk.Box):
    def __init__(self, max_label_width=192, breakpoint=192, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image = Gtk.Image()
        self._label = Gtk.Label()
        self._image.set_hexpand(False)
        self._label.set_hexpand(True)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._max_label_width = max_label_width
        self._breakpoint = breakpoint
        self.append(self._image)
        self.append(self._label)

    def set_pixel_size(self, value):
        if value >= self._breakpoint:
            self.set_orientation(Gtk.Orientation.VERTICAL)
            self.set_property("width-request", value)
            self._label.set_halign(Gtk.Align.CENTER)
            self._label.set_margin_top(Margin.DEFAULT)
            self._label.set_margin_start(0)
            self._label.set_margin_end(0)
        else:
            self.set_orientation(Gtk.Orientation.HORIZONTAL)
            total_width = value + self._max_label_width + self._label.get_margin_start() + self._label.get_margin_end()
            self.set_property("width-request", total_width)
            self._label.set_halign(Gtk.Align.START)
            self._label.set_margin_top(0)
            self._label.set_margin_start(Margin.DEFAULT)
            self._label.set_margin_end(Margin.DEFAULT)
        self._image.set_pixel_size(value)

    def set_from_icon_name(self, icon_name):
        self._image.set_from_icon_name(icon_name)
        self._label.set_text(icon_name)


class IconSizeNotSupportedError(Exception):
    pass


class IconBrowser(Gtk.Box):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._events = basic.EventManager()
        self._events.add("drawing-icons")
        self._events.add("updated", object)
        self._events.add("item-selected", str)
        self._icon_sizes = [16, 24, 32, 48, 64, 96, 128, 192, 256]
        self._control_widgets_min_width = 0
        self._grid_view_list_item_border_width = 3
        self._default_inner_margin = Margin.DEFAULT
        self._image_margin = Margin.SMALLEST
        self._icon_names = []
        self._string_separator = ";"
        self._keyword_separator = " "
        self._last_text = ""
        self._search_string = ""
        self._results_cache = {}
        self._max_cached_results = 10
        self._results_key = None
        self._results_limit = 10000
        self._start_search_timeout_id = None
        self._lower_string = ""
        self._search_delay = 60
        self._name_slices = []
        self._slice_length = 10
        self._search_id = 0
        self._operations = {}
        self._current_grid_child_class = Gtk.Image
        self._current_grid_child_icon_size = 64
        self._add_new_list_store(self._search_id)
        self._factory = Gtk.SignalListItemFactory()
        self._factory.connect("setup", self._on_factory_setup)
        self._factory.connect("bind", self._on_factory_bind)
        self._factory.connect("unbind", self._on_factory_unbind)
        self._grid_view = Gtk.GridView()
        self._grid_view.set_hexpand(True)
        self._grid_view.set_halign(Gtk.Align.FILL)
        self._grid_view.set_single_click_activate(True)
        self._grid_view.set_margin_top(self._default_inner_margin)
        self._grid_view.set_margin_bottom(self._default_inner_margin)
        self._grid_view.set_margin_start(self._default_inner_margin)
        self._grid_view.set_margin_end(self._default_inner_margin)
        if hasattr(self._grid_view, "set_tab_behavior"):
            self._grid_view.set_tab_behavior(Gtk.ListTabBehavior.CELL)
        self._grid_view.connect("activate", self._on_grid_view_activate)
        self._grid_view.set_factory(self._factory)
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_child(self._grid_view)
        self._resize_frame = ResizeFrame()
        self._resize_frame.set_child(self._scrolled_window)
        self._resize_frame.set_property("height-request",
                                        self._icon_sizes[-1] +
                                        self.get_inner_margin_top() +
                                        self.get_inner_margin_bottom() +
                                        (self._grid_view_list_item_border_width * 2) +
                                        (self._image_margin * 2) +
                                        Gtk.Label().get_preferred_size()[1].height +
                                        Margin.DEFAULT
                                        )
        self._resize_frame.hook("resized", self._on_resize_frame_resized)
        self._resize_frame.add_css_class("view")
        self._icon_size_increase_button = Gtk.Button()
        self._icon_size_increase_button.set_hexpand(False)
        self._icon_size_increase_button.set_focus_on_click(False)
        self._icon_size_increase_button.add_css_class("flat")
        self._icon_size_increase_button.connect("clicked", self._on_icon_size_increase_button_clicked)
        self._icon_size_increase_button.set_child(self._icon_finder.get_image("list-add-symbolic"))
        self._icon_size_decrease_button = Gtk.Button()
        self._icon_size_decrease_button.set_hexpand(False)
        self._icon_size_decrease_button.set_focus_on_click(False)
        self._icon_size_decrease_button.add_css_class("flat")
        self._icon_size_decrease_button.connect("clicked", self._on_icon_size_decrease_button_clicked)
        self._icon_size_decrease_button.set_child(self._icon_finder.get_image("list-remove-symbolic"))
        self._icon_size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, 0, len(self._icon_sizes) - 1, 1)
        self._icon_size_scale.set_value(self._icon_sizes.index(self._current_grid_child_icon_size))
        self._icon_size_scale.set_increments(1, len(self._icon_sizes) - 1)
        self._icon_size_scale.set_round_digits(False)
        self._icon_size_scale.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._icon_size_scale.connect("value-changed", self._on_icon_size_scale_value_changed)
        self._icon_size_scale.set_hexpand(True)
        self._icon_size_scale.set_property("width-request", len(self._icon_sizes) * 10)
        self._icon_size_box = Gtk.Box()
        self._icon_size_box.append(self._icon_size_decrease_button)
        self._icon_size_box.append(self._icon_size_scale)
        self._icon_size_box.append(self._icon_size_increase_button)
        self._icon_size_box.set_hexpand(True)
        self._show_names_toggle_label = Gtk.Label()
        self._show_names_toggle_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._show_names_toggle_label.connect("notify::label", self._on_show_names_toggle_label_changed)
        self._show_names_toggle = Gtk.ToggleButton()
        self._show_names_toggle.set_hexpand(True)
        self._show_names_toggle.set_focus_on_click(False)
        self._show_names_toggle.add_css_class("flat")
        self._show_names_toggle.connect("toggled", self._on_show_names_toggle_toggled)
        self._show_names_toggle.set_child(self._show_names_toggle_label)
        self._toolbar = FlowingToolbar()
        self._toolbar.set_margin_top(self._toolbar.get_margin_top() + Margin.SMALLEST)
        self._toolbar.set_start_widget(self._icon_size_box)
        self._toolbar.set_end_widget(self._show_names_toggle)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(self._resize_frame)
        GLib.idle_add(self._update_search_data, priority=GLib.PRIORITY_LOW)
        GLib.idle_add(self._connect_icon_finder_changed, priority=GLib.PRIORITY_LOW)
        self._update_toolbar_max_child_width()

    def _on_show_names_toggle_label_changed(self, label, gparam):
        self._update_toolbar_max_child_width()

    def _on_resize_frame_resized(self, event, width, height):
        self._update_max_columns()

    def _on_icon_size_increase_button_clicked(self, button):
        self._increase_scale_value(1)

    def _on_icon_size_decrease_button_clicked(self, button):
        self._increase_scale_value(-1)

    def _on_icon_size_scale_value_changed(self, scale):
        allow_increase = int(scale.get_value()) < len(self._icon_sizes) - 1
        allow_decrease = scale.get_value()
        if (
            (not allow_increase and self._icon_size_increase_button.has_focus())
            or (not allow_decrease and self._icon_size_decrease_button.has_focus())
        ):
            self._icon_size_scale.grab_focus()
        self._icon_size_increase_button.set_sensitive(allow_increase)
        self._icon_size_decrease_button.set_sensitive(allow_decrease)
        self._update_grid_children_style()

    def _on_show_names_toggle_toggled(self, toggle_button):
        self._update_grid_children_style()

    def _increase_scale_value(self, step):
        current_size = self._icon_sizes[int(self._icon_size_scale.get_value())]
        new_value = self._icon_sizes.index(current_size) + step
        self._icon_size_scale.set_value(new_value)

    def _update_max_columns(self):
        width = self._resize_frame.get_width()
        first_child = self._grid_view.get_first_child()
        min_image_width = self._current_grid_child_icon_size + (self._image_margin * 2) + (
            self._grid_view_list_item_border_width * 2)
        item_width = 0
        if width < min_image_width:
            return
        if first_child:
            item_width = first_child.get_allocated_width()
        if item_width < min_image_width:
            item_width = min_image_width
        spots_float = (width - ((self.get_inner_margin_start() + self.get_inner_margin_end()) * 2)) / item_width
        spots_int = int(spots_float)
        if not spots_int >= spots_float:
            spots_int += 1
        if not self._grid_view.get_max_columns() == spots_int:
            self._grid_view.set_max_columns(spots_int)

    def _update_grid_children_style(self):
        show_names = self._show_names_toggle.get_active()
        icon_size = self._icon_sizes[int(self._icon_size_scale.get_value())]
        if not show_names == self.get_show_names() or not icon_size == self.get_icon_size():
            if show_names:
                self._current_grid_child_class = LabeledImage
            else:
                self._current_grid_child_class = Gtk.Image
            self._current_grid_child_icon_size = icon_size
            if self._grid_view.get_model() and len(self._grid_view.get_model().get_model()):
                self.clear()
                self._start_search()
            self._update_max_columns()

    def _update_toolbar_max_child_width(self):
        max_child_width = tuple(sorted((
            len(self._icon_sizes) * 20,
            self._show_names_toggle.get_preferred_size()[1].width,
            self._control_widgets_min_width
        )))[-1]
        self._toolbar.set_max_child_width(max_child_width)

    def _on_icon_finder_changed(self, event, icon_finder):
        self.clear()
        self._update_search_data()
        self._start_search()

    def _on_factory_setup(self, factory, list_item):
        image = self._current_grid_child_class()
        image.set_pixel_size(self._current_grid_child_icon_size)
        image.set_margin_top(self._image_margin)
        image.set_margin_bottom(self._image_margin)
        image.set_margin_start(self._image_margin)
        image.set_margin_end(self._image_margin)
        list_item.set_child(image)

    def _on_factory_bind(self, factory, list_item):
        GLib.idle_add(list_item.get_child().set_from_icon_name, list_item.get_item().name, priority=GLib.PRIORITY_LOW)

    def _on_factory_unbind(self, factory, list_item):
        list_item.get_child().set_from_icon_name("")

    def _on_grid_view_activate(self, grid_view, position):
        self._events.trigger("item-selected", grid_view.get_model().get_model()[position].name)

    def _connect_icon_finder_changed(self):
        self._icon_finder.hook("changed", self._on_icon_finder_changed)

    def _update_search_data(self):
        self._icon_names = self._icon_finder.get_names()
        self._search_string = self._string_separator.join(self._icon_names)
        self._lower_string = self._search_string.lower()

    def _add_new_list_store(self, search_id):
        list_store = Gio.ListStore()
        selection_model = Gtk.NoSelection()
        selection_model.set_model(list_store)
        self._operations[search_id] = {
            "list-store": list_store,
            "selection-model": selection_model
        }

    def _start_search(self, text=None, exclude=[]):
        if text == None:
            text = self._last_text
        else:
            self._last_text = text
        del self._operations[self._search_id]
        self._search_id += 1
        self._add_new_list_store(self._search_id)
        if self._start_search_timeout_id:
            GLib.source_remove(self._start_search_timeout_id)
        self._start_search_timeout_id = GLib.timeout_add(self._search_delay, self._start_search_thread, text,
            self._search_id, exclude)

    def _start_search_thread(self, text, search_id, exclude=[]):
        keywords = set(filter(None, text.lower().replace(self._string_separator,
            self._keyword_separator).split(self._keyword_separator)))
        results_key = self._keyword_separator.join(keywords)
        self._search_thread = threading.Thread(target=self._search_thread_target,
            args=[text, keywords, results_key, search_id], kwargs={"exclude": exclude})
        self._search_thread.start()
        self._start_search_timeout_id = None
        return GLib.SOURCE_REMOVE

    def _search_thread_target(self, text, keywords, results_key, search_id, exclude=[]):
        try:
            names = self._results_cache[results_key]["names"]
        except KeyError:
            if not len(keywords):
                names = []
            else:
                names = self._get_names(keywords, search_id, exclude=exclude)
        GLib.idle_add(self._after_search_thread, names, results_key, search_id, priority=GLib.PRIORITY_LOW)

    def _after_search_thread(self, names, results_key, search_id):
        try:
            del self._results_cache[list(self._results_cache.keys())[-self._max_cached_results]]
        except IndexError:
            pass
        try:
            if (
                self._results_key and self._results_key in self._results_cache
                and names == self._results_cache[self._results_key]["names"]
                and self._results_cache[self._results_key]["selection-model"] == self._grid_view.get_model()
            ):
                self._operations[search_id] = self._results_cache[self._results_key]
                self._after_search_finished(results_key, search_id)
            else:
                self._operations[search_id]["names"] = names
                selection_model = self._operations[search_id]["selection-model"]
                self._grid_view.set_model(selection_model)
                if len(names):
                    icon_names = [IconName(name) for n, name in zip(range(self._results_limit), names)]
                    name_slices = [icon_names[i:i+self._slice_length] for i in range(0, len(icon_names),
                        self._slice_length)]
                    self._operations[search_id]["name-slices"] = name_slices
                    GLib.idle_add(self._add_next_slice, results_key, search_id, priority=GLib.PRIORITY_LOW)
                else:
                    self._after_search_finished(results_key, search_id)
        except KeyError as error:
            if search_id in self._operations:
                raise error

    def _add_next_slice(self, results_key, search_id):
        try:
            self._events.trigger("drawing-icons")
            list_store = self._operations[search_id]["list-store"]
            name_slices = self._operations[search_id]["name-slices"]
            list_store.splice(len(list_store), 0, name_slices.pop(0))
        except IndexError:
            self._after_search_finished(results_key, search_id)
        except KeyError as error:
            if search_id in self._operations:
                raise error
        else:
            return True

    def _after_search_finished(self, results_key, search_id):
        self._results_cache[results_key] = self._operations[search_id]
        self._results_key = results_key
        list_store = self._operations[search_id]["list-store"]
        self._events.trigger("updated", list_store)

    def _get_names(self, keywords, search_id, exclude=[]):
        names = []
        for string in keywords:
            names.append([])
            start_pos = 0
            while search_id == self._search_id:
                try:
                    start_pos = self._lower_string.index(string, start_pos)
                except ValueError:
                    break
                else:
                    start_pos -= 1
                    while (
                        not self._search_string[start_pos:start_pos + len(
                        self._string_separator)] == self._string_separator
                    ):
                        start_pos -= 1
                        if start_pos < 1:
                            start_pos = 0
                            break
                    else:
                        start_pos += 1
                    try:
                        end_pos = self._search_string.index(self._string_separator, start_pos)
                    except ValueError:
                        name = self._search_string[start_pos:]
                        if not name in exclude:
                            names[-1].append(name)
                        break
                    else:
                        name = self._search_string[start_pos:end_pos]
                        if not name in exclude:
                            names[-1].append(name)
                        start_pos = end_pos + len(self._string_separator)
                        if not len(self._search_string) > start_pos:
                            break
            else:
                return []
        else:
            return self._get_matching_names(names)

    def _get_matching_names(self, lists):
        first_list = lists.pop(0)
        first_list = set(first_list)
        for remaining_list in lists:
            first_list = first_list.intersection(remaining_list)
        else:
            return first_list

    def get_show_names(self):
        return self._current_grid_child_class == LabeledImage

    def set_show_names(self, value):
        self._show_names_toggle.set_active(value)

    def get_icon_size(self):
        return self._current_grid_child_icon_size

    def set_icon_size(self, value):
        try:
            self._icon_size_scale.set_value(self._icon_sizes.index(value))
        except ValueError:
            raise IconSizeNotSupportedError(value)

    def get_show_names_toggle_label(self):
        return self._show_names_toggle_label.get_text()

    def set_show_names_toggle_label(self, text):
        self._show_names_toggle_label.set_text(text)

    def get_inner_margin_top(self):
        return self._grid_view.get_margin_top()

    def set_inner_margin_top(self, value):
        self._grid_view.set_margin_top(value)

    def get_inner_margin_bottom(self):
        return self._grid_view.get_margin_bottom()

    def set_inner_margin_bottom(self, value):
        self._grid_view.set_margin_bottom(value)

    def get_inner_margin_start(self):
        return self._grid_view.get_margin_start()

    def set_inner_margin_start(self, value):
        self._grid_view.set_margin_start(value)

    def get_inner_margin_end(self):
        return self._grid_view.get_margin_end()

    def set_inner_margin_end(self, value):
        self._grid_view.set_margin_end(value)

    def get_results(self):
        return self._grid_view.get_model().get_model()

    def get_toolbar(self):
        return self._toolbar

    def update(self, text, exclude=[]):
        self._start_search(text, exclude=exclude)

    def clear(self):
        self._results_cache.clear()
        self._grid_view.set_model(None)
        self._results_key = None

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class RevealerRow(Adw.PreferencesRow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignore_toggle_button_toggled = False
        self._toggle_button = Gtk.ToggleButton()
        self._toggle_button.connect("toggled", self._on_toggle_button_toggled)
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(90)
        self._revealer_box = Gtk.Box()
        self._revealer_box.set_vexpand(True)
        self._revealer_box.set_orientation(Gtk.Orientation.VERTICAL)
        self._revealer_box.append(self._stack)
        self._revealer = Gtk.Revealer()
        self._revealer.set_transition_duration(300)
        self._revealer.connect("notify::reveal-child", self._on_revealer_reveal_child_changed)
        self._revealer.connect("notify::child-revealed", self._on_revealer_child_revealed_changed)
        self._revealer.set_child(self._revealer_box)
        self.set_activatable(False)
        self.set_active(True)
        self.set_child(self._revealer)

    def _on_toggle_button_toggled(self, toggle_button):
        if not self._ignore_toggle_button_toggled:
            self._revealer.set_reveal_child(toggle_button.get_active())

    def _on_revealer_reveal_child_changed(self, revealer, gparam):
        self._ignore_toggle_button_toggled = True
        self._toggle_button.set_active(self._revealer.get_reveal_child())
        self._ignore_toggle_button_toggled = False
        if self._revealer.get_reveal_child():
            self.show()

    def _on_revealer_child_revealed_changed(self, revealer, gparam):
        if not self._revealer.get_child_revealed():
            self.hide()

    def get_active(self):
        return self._revealer.get_reveal_child()

    def set_active(self, value):
        self._revealer.set_reveal_child(value)

    def get_page(self):
        return self._stack.get_visible_child()

    def set_page(self, child):
        if isinstance(child, Gtk.StackPage):
            child = child.get_child()
        self._stack.set_visible_child(child)

    def add_page(self, child):
        self._stack.add_named(child, str(child))

    def remove_page(self, child):
        self._stack.remove(child)

    def get_revealer(self):
        return self._revealer

    def get_stack(self):
        return self._stack

    def get_toggle_button(self):
        return self._toggle_button

    def append(self, widget):
        self._revealer_box.append(widget)

    def remove(self, widget):
        self._revealer_box.remove(widget)


class IconViewRow(RevealerRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon_view = IconView(app)
        self._prefix_box = Gtk.Box()
        self._suffix_box = Gtk.Box()
        for box in [self._prefix_box, self._suffix_box]:
            box.set_margin_top(Margin.LARGE)
            box.set_margin_bottom(Margin.LARGE)
            box.set_margin_start(Margin.LARGE)
            box.set_margin_end(Margin.LARGE)
            box.set_spacing(Spacing.DEFAULT)
        self.remove(self._stack)
        self._center_box = Gtk.CenterBox()
        self._center_box.set_start_widget(self._prefix_box)
        self._center_box.set_end_widget(self._suffix_box)
        self._center_box.set_center_widget(self._stack)
        self._revealer.set_child(self._center_box)
        self.add_css_class("view")
        self.add_page(self._icon_view)

    def get_icon_view(self):
        return self._icon_view

    def add_prefix(self, child):
        self._prefix_box.append(child)

    def add_suffix(self, child):
        self._suffix_box.append(child)


class IconBrowserRow(RevealerRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._icon_browser = IconBrowser(app)
        self._icon_browser.set_vexpand(True)
        self._bottom_separator = Gtk.Separator()
        self._bottom_separator.set_vexpand(False)
        self._toolbar = self._icon_browser.get_toolbar()
        self._toolbar.set_vexpand(False)
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.connect("notify::dark", self._on_style_manager_dark_changed)
        self._stack.connect("notify::visible-child", self._on_stack_visible_child_changed)
        self.add_page(self._icon_browser)
        self.append(self._bottom_separator)
        self.append(self._toolbar)
        self._default_inner_margin_bottom = self._icon_browser.get_inner_margin_bottom()
        self._update_bottom_separator_visibility()

    def _on_style_manager_dark_changed(self, style_manager, gparam):
        self._update_bottom_separator_visibility()

    def _update_bottom_separator_visibility(self):
        dark_mode_enabled = self._style_manager.get_dark()
        self._bottom_separator.set_visible(dark_mode_enabled == False)
        self._icon_browser.set_inner_margin_bottom(self._default_inner_margin_bottom * (bool(dark_mode_enabled)))

    def _on_stack_visible_child_changed(self, stack, gparam):
        self._toolbar.set_sensitive(self._stack.get_visible_child() == self._icon_browser)

    def get_icon_browser(self):
        return self._icon_browser


class EntryRow(Adw.EntryRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._events = basic.EventManager()
        self._events.add("text-changed", object, str)
        self._event_controller_focus = Gtk.EventControllerFocus()
        self._event_controller_focus.connect("leave", self._on_event_controller_focus_leave)
        self._editable = self.get_delegate()
        self._editable.add_controller(self._event_controller_focus)
        self.set_enable_undo(True)
        self.connect("changed", self._on_changed)

    def _on_event_controller_focus_leave(self, controller):
        self.select_region(0, 0)

    def _on_changed(self, editable):
        text = editable.get_text()
        self._events.trigger("text-changed", self, text)

    def _get_placeholder_image_hack_1(self):
        try:
            gizmo = self.get_child().get_first_child().get_next_sibling()
            if type(gizmo).__name__ == "AdwGizmo":
                image = gizmo.get_next_sibling().get_next_sibling().get_next_sibling()
                if isinstance(image, Gtk.Image):
                    return image
        except:
            pass

    def _get_placeholder_image_hack_2(self):
        try:
            gizmo = self.get_child().get_first_child().get_next_sibling()
            if type(gizmo).__name__ == "AdwGizmo":
                child = gizmo.get_first_child()
                for n in range(100):
                    if not child == None:
                        if isinstance(child, Gtk.Image):
                            return child
                        else:
                            child = child.get_next_sibling()
                    else:
                        break
        except:
            pass

    def get_placeholder_image(self):
        methods = [
            self._get_placeholder_image_hack_1,
            self._get_placeholder_image_hack_2
        ]
        for method in methods:
            image = method()
            if not image == None:
                return image

    def set_placeholder_image(self, icon_name, ignore_errors=True):
        try:
            self.get_placeholder_image().set_from_icon_name(icon_name)
        except Exception as e:
            if not ignore_errors:
                raise e

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class PathChooserRow(EntryRow):
    def __init__(self, app, action, show_placeholder_image=False, button_image="document-open-symbolic", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._application_window = app.get_application_window()
        self._default_image = self._icon_finder.get_image(button_image)
        self._chooser_button_event_controller_key = Gtk.EventControllerKey()
        self._chooser_button_event_controller_key.connect(
            "key-pressed", self._on_chooser_button_event_controller_key_pressed
        )
        self._chooser_button = Gtk.Button()
        self._chooser_button.set_focus_on_click(False)
        self._chooser_button.add_css_class("flat")
        self._chooser_button.set_valign(Gtk.Align.CENTER)
        self._chooser_button.connect("clicked", self._on_chooser_button_clicked)
        self._chooser_button.add_controller(self._chooser_button_event_controller_key)
        self._chooser_button.set_child(self._default_image)
        self._dialog_accept_button = Gtk.Button()
        self._dialog_accept_button.add_css_class("suggested-action")
        self._dialog_cancel_button = Gtk.Button()
        if not os.getenv("APP_RUNNING_AS_FLATPAK") == "true" or os.getenv("USE_NATIVE_DIALOGS") == "true":
            self._file_chooser_dialog = Gtk.FileChooserNative(action=action)
        else:
            self._file_chooser_dialog = Gtk.FileChooserDialog(action=action)
            self._file_chooser_dialog.add_action_widget(self._dialog_accept_button, Gtk.ResponseType.ACCEPT)
            self._file_chooser_dialog.add_action_widget(self._dialog_cancel_button, Gtk.ResponseType.CANCEL)
            self._file_chooser_dialog.set_default_response(Gtk.ResponseType.ACCEPT)
            try:
                self._file_chooser_dialog.connect("show", self._on_file_chooser_dialog_show)
                self._file_chooser_dialog.connect("close-request", self._on_file_chooser_dialog_close_request)
            except TypeError:
                pass
        self._file_chooser_dialog.connect("response", self._on_file_chooser_dialog_response)
        self._file_chooser_dialog.set_transient_for(self._application_window)
        self._file_chooser_dialog.set_modal(True)
        self.add_suffix(self._chooser_button)
        if not show_placeholder_image:
            try:
                self.get_placeholder_image().unparent()
                self.get_placeholder_image().unparent()
            except:
                pass

    def _on_chooser_button_event_controller_key_pressed(self, controller, keyval, keycode, state):
        text = self._editable.get_text()
        if not keyval == Keyval.ENTER:
            self._editable.set_position(-1)
            controller.forward(self._editable)
            if not text == self._editable.get_text():
                if not self._editable.has_focus():
                    self._editable.grab_focus_without_selecting()
                return True

    def _on_file_chooser_dialog_show(self, dialog):
        self._file_chooser_dialog.set_current_folder(Gio.File.new_for_path(GLib.get_home_dir()))

    def _on_file_chooser_dialog_response(self, dialog, response):
        self._file_chooser_dialog.hide()
        if response == Gtk.ResponseType.ACCEPT:
            self.set_text(self._file_chooser_dialog.get_file().get_path())

    def _on_file_chooser_dialog_close_request(self, dialog):
        self._file_chooser_dialog.hide()
        return True

    def _on_chooser_button_clicked(self, button):
        self._file_chooser_dialog.show()

    def get_dialog_accept_button_label(self, text):
        return self._dialog_accept_button.get_label()

    def set_dialog_accept_button_label(self, text):
        self._dialog_accept_button.set_label(text)

    def get_dialog_cancel_button_label(self):
        return self._dialog_cancel_button.get_label()

    def set_dialog_cancel_button_label(self, text):
        self._dialog_cancel_button.set_label(text)

    def set_dialog_title(self, text):
        self._file_chooser_dialog.set_title(text)

    def get_dialog_title(self):
        return self._file_chooser_dialog.get_title()

    def get_chooser_button(self):
        return self._chooser_button


class FileChooserRow(PathChooserRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, action=Gtk.FileChooserAction.OPEN, *args, **kwargs)


class DirectoryChooserRow(PathChooserRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, action=Gtk.FileChooserAction.SELECT_FOLDER, button_image="folder-open-symbolic", *args, **kwargs)
        self._fallback_path = None
        self._has_focus = False
        self._event_controller_focus = Gtk.EventControllerFocus()
        self._event_controller_focus.connect("enter", self._on_event_controller_focus_enter)
        self._event_controller_focus.connect("leave", self._on_event_controller_focus_leave)
        self.add_controller(self._event_controller_focus)

    def _on_changed(self, editable):
        text = editable.get_text()
        self._events.trigger("text-changed", self, text)
        if len(text):
            if os.path.exists(text) and os.path.isdir(text) and os.access(text, os.R_OK):
                self.remove_css_class("error")
            else:
                self.add_css_class("error")
        else:
            self.remove_css_class("error")

    def _update_fallback_path_visible(self):
        if not len(self.get_text()) and not self._has_focus:
            self.set_text(self._fallback_path)

    def _on_event_controller_focus_leave(self, controller):
        self._has_focus = False
        self._update_fallback_path_visible()

    def _on_event_controller_focus_enter(self, controller):
        self._has_focus = True
        self._update_fallback_path_visible()

    def get_fallback_path(self):
        return self._fallback_path

    def set_fallback_path(self, path):
        self._fallback_path = path
        self._update_fallback_path_visible()


class IconChooserRow(FileChooserRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, show_placeholder_image=True, *args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._ignore_text_changed = False
        self._default_entry_title = None
        self._search_entry_title = None
        self._ignore_first_empty_text = False
        self._search_mode = False
        self._previous_text = ""
        self._help_status_page = Adw.StatusPage()
        self._help_status_page.set_can_focus(False)
        self._help_status_page.add_css_class("view")
        self._none_status_page = Adw.StatusPage()
        self._none_status_page.set_can_focus(False)
        self._none_status_page.add_css_class("view")
        self._icon_view_row = IconViewRow(app)
        self._icon_view_row.set_active(True)
        self._icon_view_row.set_visible(True)
        self._icon_view = self._icon_view_row.get_icon_view()
        self._icon_view.hook("updated", self._on_icon_view_updated)
        self._icon_browser_row = IconBrowserRow(app)
        self._icon_browser_row.set_active(False)
        self._icon_browser_row.set_visible(False)
        self._icon_browser = self._icon_browser_row.get_icon_browser()
        self._icon_browser.hook("drawing-icons", self._on_icon_browser_drawing_icons)
        self._icon_browser.hook("updated", self._on_icon_browser_updated)
        self._icon_browser.hook("item-selected", self._on_icon_browser_item_selected)
        self._icon_browser_row.add_page(self._help_status_page)
        self._icon_browser_row.add_page(self._none_status_page)
        self.remove(self._chooser_button)
        self._chooser_button.set_valign(Gtk.Align.START)
        self._chooser_button.connect("clicked", self._on_chooser_button_clicked)
        self._toggle_button = self._icon_browser_row.get_toggle_button()
        self._toggle_button.set_focus_on_click(False)
        self._toggle_button.connect("toggled", self._on_toggle_button_toggled)
        self._toggle_button.set_icon_name(self._icon_finder.get_name("system-search-symbolic"))
        self._toggle_button.set_valign(Gtk.Align.START)
        self._toggle_button.add_css_class("flat")
        self._icon_view_row.add_prefix(self._chooser_button)
        self._icon_view_row.add_suffix(self._toggle_button)
        self._entry_event_controller_key = Gtk.EventControllerKey()
        self._entry_event_controller_key.connect("key-pressed", self._on_event_controllers_key_pressed)
        self._view_event_controller_key = Gtk.EventControllerKey()
        self._view_event_controller_key.connect("key-pressed", self._on_event_controllers_key_pressed)
        self._browser_event_controller_key = Gtk.EventControllerKey()
        self._browser_event_controller_key.connect("key-pressed", self._on_event_controllers_key_pressed)
        self._icon_view_row.add_controller(self._view_event_controller_key)
        self._icon_browser_row.add_controller(self._browser_event_controller_key)
        self.add_controller(self._entry_event_controller_key)
        self.get_delegate().connect("activate", self._on_activate)

    def _on_chooser_button_clicked(self, button):
        self.set_search_mode(False)
        FileChooserRow._on_chooser_button_clicked(self, button)

    def _on_event_controllers_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Keyval.ESCAPE and state == 0:
            self.set_search_mode(self.get_search_mode() == False)
            self.grab_focus_without_selecting()

    def _on_toggle_button_toggled(self, toggle_button):
        self.set_search_mode(self._toggle_button.get_active())
        self.grab_focus_without_selecting()

    def _on_activate(self, entry):
        if not self.get_search_mode():
            self.set_search_mode(True)
        else:
            if self._icon_browser_row.get_page() == self._icon_browser and len(self._icon_browser.get_results()):
                self._icon_browser_row.grab_focus()
            else:
                self.set_search_mode(False)

    def _on_changed(self, entry):
        text = entry.get_text()
        if not len(text) and self._ignore_first_empty_text:
            self._ignore_first_empty_text = False
            return
        if not self._search_mode:
            self._previous_text = text
            self._events.trigger("text-changed", self, text)
            self._icon_view.update(text)
        elif not self._ignore_text_changed:
            self._icon_browser.update(text)
        else:
            self._ignore_text_changed = False

    def _on_icon_view_updated(self, event, update_successful):
        if self._icon_view.get_update_successful():
            self.remove_css_class("warning")
        else:
            self.add_css_class("warning")

    def _on_icon_browser_updated(self, event, results):
        if self._search_mode:
            if len(results):
                self.remove_css_class("warning")
                self._icon_browser_row.set_page(self._icon_browser)
            else:
                if len(self.get_text()):
                    self.add_css_class("warning")
                    self._icon_browser_row.set_page(self._none_status_page)
                else:
                    self.remove_css_class("warning")
                    self._icon_browser_row.set_page(self._help_status_page)

    def _on_icon_browser_drawing_icons(self, event):
        self.remove_css_class("warning")
        self._icon_browser_row.set_page(self._icon_browser)

    def _on_icon_browser_item_selected(self, event, text):
        self._previous_text = text
        self.set_search_mode(False)
        self.grab_focus_without_selecting()

    def get_search_mode(self):
        return self._search_mode

    def set_search_mode(self, value):
        self._search_mode = value
        if value:
            self._ignore_text_changed = True
            self.set_text("")
            self._ignore_text_changed = False
            self.remove_css_class("warning")
            if self._search_entry_title:
                self.set_title(self._search_entry_title)
            self._icon_browser_row.set_page(self._help_status_page)
            self._icon_browser_row.set_active(True)
        else:
            if not len(self.get_text()):
                self.add_css_class("warning")
            if self._default_entry_title:
                self.set_title(self._default_entry_title)
            self._icon_browser_needs_cleanup = True
            self._icon_browser_row.set_active(False)
            self.set_text(self._previous_text)

    def get_default_entry_title(self):
        return self._default_entry_title

    def set_default_entry_title(self, text):
        self._default_entry_title = text
        if not self._search_mode:
            self.set_title(text)

    def get_search_entry_title(self):
        return self._search_entry_title

    def set_search_entry_title(self, text):
        self._search_entry_title = text
        if self._search_mode:
            self.set_title(text)

    def get_icon_view_row(self):
        return self._icon_view_row

    def get_icon_browser_row(self):
        return self._icon_browser_row

    def get_help_status_page(self):
        return self._help_status_page

    def get_none_status_page(self):
        return self._none_status_page

    def set_text(self, text):
        if len(text):
            self._ignore_first_empty_text = True
        EntryRow.set_text(self, text)
        self._ignore_first_empty_text = False

    def grab_focus_without_selecting(self):
        self.grab_focus()
        self.set_position(-1)

    def reset(self):
        self._previous_text = ""
        self.set_search_mode(False)


class FocusGroup():
    def __init__(self):
        self._events = basic.EventManager()
        self._events.add("changed", bool)
        self._focused = False
        self._widgets = {}

    def _on_focus_enter(self, controller):
        GLib.idle_add(self._after_focus_event)

    def _on_focus_leave(self, controller):
        GLib.idle_add(self._after_focus_event)

    def _after_focus_event(self):
        for widget in self._widgets:
            if widget.get_focus_child():
                focused = True
                break
        else:
            focused = False
        state_changed = not focused == self._focused
        self._focused = focused
        if state_changed:
            self._events.trigger("changed", focused)

    def get_focused(self):
        return self._focused

    def add(self, *widgets):
        for widget in widgets:
            self._widgets[widget] = {}
            controller = Gtk.EventControllerFocus()
            controller.connect("enter", self._on_focus_enter)
            controller.connect("leave", self._on_focus_leave)
            widget.add_controller(controller)
            self._widgets[widget]["controller"] = controller

    def remove(self, *widgets):
        for widget in widgets:
            del self._widgets[widget]

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class LinkConverterRow(Gtk.Box):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._application = app
        self._icon_finder = app.get_icon_finder()
        self._group_focused = False
        self._entry_connection_id = None
        self._entry = None
        self._url_regex_patterns = [
            r"((http|ftp|https)://)?(([a-zA-Z0-9]{1,}[_-]{1})*[a-zA-Z0-9]{1,}\.)+([a-zA-Z0-9]{2,}){1}" +
            r"(/[a-zA-Z0-9\@\%\&\#\=\~\+\-\_\.\,\;\:\?\!\'\*\$()\[\]\/]+)?$",
        ]
        self._url_open_commands = [
            "xdg-open",
            "open",
            "x-www-browser",
            "gnome-open",
            "kde-open"
        ]
        for command in self._url_open_commands:
            if app.get_command_exists(command):
                self._url_open_command = command
                break
        else:
            self._url_open_command = None
        self._button_label = Gtk.Label()
        self._button_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._button_image = self._icon_finder.get_image("system-run-symbolic")
        self._button_image.set_margin_end(Margin.DEFAULT)
        self._center_box = Gtk.CenterBox()
        self._center_box.set_margin_start(Margin.LARGE)
        self._center_box.set_margin_end(Margin.LARGE)
        self._center_box.set_start_widget(self._button_image)
        self._center_box.set_center_widget(self._button_label)
        self._button = Gtk.Button()
        self._button.add_css_class("accent")
        self._button.add_css_class("circular")
        self._button.set_focus_on_click(False)
        self._button.connect("clicked", self._on_button_clicked)
        self._button.set_child(self._center_box)
        self._clamp = Adw.Clamp(maximum_size=480, tightening_threshold=380)
        self._clamp.set_margin_top(Margin.LARGE)
        self._clamp.set_margin_bottom(Margin.LARGE)
        self._clamp.set_child(self._button)
        self._revealer = Gtk.Revealer()
        self._revealer.set_child(self._clamp)
        self._revealer.connect("notify::reveal-child", self._on_revealer_reveal_child_changed)
        self._revealer.connect("notify::child-revealed", self._on_revealer_child_revealed_changed)
        self._focus_group = FocusGroup()
        self._focus_group.hook("changed", self._on_focus_group_changed)
        self._focus_group.add(self)
        self.set_visible(False)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(self._revealer)

    def _on_focus_group_changed(self, event, focused):
        self._group_focused = focused
        self._update_widgets()

    def _on_button_clicked(self, button):
        self._convert_url_to_command()
        self._update_widgets()

    def _on_entry_changed(self, entry):
        self._update_widgets()

    def _on_revealer_reveal_child_changed(self, revealer, gparam):
        if self._revealer.get_reveal_child():
            self.show()

    def _on_revealer_child_revealed_changed(self, revealer, gparam):
        if not self._revealer.get_child_revealed():
            self.hide()

    def _update_widgets(self):
        if self._url_open_command:
            text = self._entry.get_text()
            if self._application.get_command_exists(text, desktop_entry=True):
                self._revealer.set_reveal_child(False)
                self._entry.remove_css_class("error")
                if not text.split(" ")[0] in self._url_open_commands and self._group_focused:
                    self._revealer.set_reveal_child(True)
            else:
                self._revealer.set_reveal_child(True)
                self._entry.add_css_class("error")
            if self._get_string_is_valid_url(text.strip()):
                self._entry.add_css_class("warning")
                self._entry.remove_css_class("error")
                self._button.add_css_class("accent")
                self.set_sensitive(True)
            else:
                self._entry.remove_css_class("warning")
                self._button.remove_css_class("accent")
                self.set_sensitive(False)

    def _convert_url_to_command(self):
        text = self._entry.get_text().strip()
        if text.startswith("http://"):
            text = text.replace("http://", "https://")
        elif not text.startswith("https://"):
            text = f"https://{text}"
        self._entry.set_text(f"{self._url_open_command} {text}")
        if hasattr(self._entry, "grab_focus_without_selecting"):
            self._entry.grab_focus_without_selecting()
        else:
            self._entry.grab_focus()
        self._entry.set_position(-1)

    def _get_string_is_valid_url(self, text):
        if not " " in text and not self._application.get_command_exists(text, desktop_entry=True, include_lookup_cwd=True):
            for pattern in self._url_regex_patterns:
                if re.match(pattern, text):
                    return True

    def get_entry(self, entry):
        return self._entry

    def set_entry(self, entry):
        if not self._entry == None:
            self._entry.dicsonnect(self._entry_connection_id)
        self._entry = entry
        self._entry_connection_id = self._entry.connect("changed", self._on_entry_changed)
        self._focus_group.add(entry)
        self._on_entry_changed(self._entry)

    def get_label(self):
        return self._button_label.get_text()

    def set_label(self, text):
        self._button_label.set_text(text)


class CommandChooserRow(FileChooserRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._application = app
        self._command_arg_escaper = basic.DesktopEntryCommandArgEscaper()
        self.add_css_class("error")

    def _on_file_chooser_dialog_response(self, dialog, response):
        self._file_chooser_dialog.hide()
        if response == Gtk.ResponseType.ACCEPT:
            path = self._file_chooser_dialog.get_file().get_path()
            escaped_path = self._command_arg_escaper.get_escaped_arg(path)
            self.set_text(escaped_path)

    def _on_changed(self, editable):
        text = editable.get_text()
        self._events.trigger("text-changed", self, text)
        if not len(text.strip()):
            self.add_css_class("error")
        elif not self._application.get_command_exists(text, desktop_entry=True, skip_empty_path=True, include_lookup_cwd=True):
            self.add_css_class("error")
        else:
            self.remove_css_class("error")


class DeleteRow(Adw.ActionRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon_finder = app.get_icon_finder()
        self._delete_button = Gtk.Button()
        self._delete_button.set_icon_name(self._icon_finder.get_name("edit-delete-symbolic"))
        self._delete_button.add_css_class("flat")
        self._delete_button.set_can_focus(False)
        self._delete_button.set_can_target(False)
        self._delete_button.set_valign(Gtk.Align.CENTER)
        self.add_css_class("warning")
        self.set_activatable(True)
        self.add_suffix(self._delete_button)

    def get_text(self, text):
        return self.get_subtitle()

    def set_text(self, text):
        if len(text):
            self.add_css_class("property")
        else:
            self.remove_css_class("property")
        self.set_subtitle(text)


class SwitchRow(Adw.ActionRow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._events.add("value-changed", object, bool)
        self._switch = Gtk.Switch()
        self._switch.set_can_focus(False)
        self._switch.set_valign(Gtk.Align.CENTER)
        self._switch.connect("notify::active", self._on_switch_active_changed)
        self.set_activatable(True)
        self.connect("activated", self._on_activated)
        self.add_suffix(self._switch)

    def _on_activated(self, action_row):
        self._switch.activate()

    def _on_switch_active_changed(self, switch, property):
        self._events.trigger("value-changed", self, switch.get_active())

    def get_switch(self):
        return self._switch

    def set_switch(self, switch):
        self._remove(self._switch)
        self._add_suffix(switch)
        self._switch = switch

    def get_active(self):
        return self._switch.get_active()

    def set_active(self, value):
        self._switch.set_active(value)

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class MultiListBox(Gtk.Box):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._events.add("row-activated", object, object)
        self._sort_data = {}
        self._order = []
        self._sections = {}
        self.set_orientation(Gtk.Orientation.VERTICAL)

    def _on_row_activated(self, list_box, row):
        self._events.trigger("row-activated", list_box, row)

    def _do_list_box_sort(self, row_1, row_2):
        items = [
            self._sort_data[row_1],
            self._sort_data[row_2]
        ]
        if items[0] == items[1]:
            return 0
        else:
            if sorted(items, key=str.lower)[0] == items[0]:
                return -1
            else:
                return 1

    def _update_separator_visible(self):
        sections_left = list(self._order)
        for section in reversed(self._order):
            has_children = self._sections[section]["list_box"].get_first_child()
            if section == sections_left[-1]:
                show_separator = False
            else:
                show_separator = has_children
            if not has_children:
                sections_left.remove(section)
            self._sections[section]["separator"].set_visible(show_separator)

    def get_visible_children(self):
        children = []
        for section in self._order:
            list_box = self._sections[section]["list_box"]
            child = list_box.get_first_child()
            if child:
                children.append(child)
                while True:
                    child = child.get_next_sibling()
                    if child:
                        children.append(child)
                    else:
                        break
        else:
            return children

    def get_first_child(self):
        for section in self._order:
            first_child = self._sections[section]["list_box"].get_first_child()
            if first_child:
                return first_child
        else:
            return None

    def get_pixel_height_for_n_rows(self, n_rows):
        first_child = self.get_first_child()
        if first_child:
            child_height = first_child.get_preferred_size()[1].height
        else:
            child_height = 0
        return child_height * n_rows

    def has_section(self, section):
        return section in self._sections

    def has_row(self, row, section):
        return row.get_parent() == self._sections[section]["list_box"]

    def append_section(self, name):
        if not name in self._sections:
            self._sections[name] = {
                "list_box": Gtk.ListBox(),
                "separator": Gtk.Separator(),
                "sort_data": []
            }
            self._order.append(name)
            self.append(self._sections[name]["list_box"])
            self.append(self._sections[name]["separator"])
            self._sections[name]["list_box"].set_sort_func(self._do_list_box_sort)
            self._sections[name]["list_box"].connect("row-activated", self._on_row_activated)
            self._update_separator_visible()
        else:
            raise ItemAlreadyExistingError(name)

    def remove_section(self, name):
        if name in self._sections:
            self.remove(self._sections[name]["list_box"])
            self.remove(self._sections[name]["separator"])
            del self._sections[name]
            self._order.remove(name)
            self._update_separator_visible()
        else:
            raise ItemNotFoundError(name)

    def append_row(self, widget, section, sort_data=None):
        if not self.has_row(widget, section):
            list_box = self._sections[section]["list_box"]
            self._sort_data[widget] = str(sort_data)
            list_box.append(widget)
            self._update_separator_visible()
        else:
            raise ItemAlreadyExistingError(widget)

    def remove_row(self, widget, section):
        if self.has_row(widget, section):
            list_box = self._sections[section]["list_box"]
            del self._sort_data[widget]
            list_box.remove(widget)
            self._update_separator_visible()
        else:
            raise ItemNotFoundError(widget)

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class ComboRow(Adw.ActionRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._events.add("item-selected", object, str)
        self._icon_finder = app.get_icon_finder()
        self._icon_finder.hook("changed", self._on_icon_finder_changed)
        self._display_n_buttons = 10
        self._flow_row = None
        self._buttons = {}
        self._multi_list_box = MultiListBox()
        self._multi_list_box.hook("row-activated", self._on_multi_list_box_row_activated)
        self._multi_list_box.set_margin_top(Margin.DEFAULT)
        self._multi_list_box.set_margin_bottom(Margin.DEFAULT)
        self._multi_list_box.set_margin_start(Margin.DEFAULT)
        self._multi_list_box.set_margin_end(Margin.DEFAULT)
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_propagate_natural_height(True)
        self._scrolled_window.set_propagate_natural_width(True)
        self._scrolled_window.set_child(self._multi_list_box)
        self._popover = Gtk.Popover()
        self._popover.set_offset(-Margin.DEFAULT, 0)
        self._popover.set_valign(Gtk.Align.END)
        self._popover.add_css_class("menu")
        self._popover.connect("show", self._on_popover_show)
        self._popover.connect("closed", self._on_popover_closed)
        self._popover.set_child(self._scrolled_window)
        self._menu_button = Gtk.MenuButton()
        self._menu_button.add_css_class("flat")
        self._menu_button.set_icon_name(self._icon_finder.get_name("list-add-symbolic"))
        self._menu_button.set_direction(Gtk.ArrowType.LEFT)
        self._menu_button.set_valign(Gtk.Align.CENTER)
        self._menu_button.set_popover(self._popover)
        self.add_suffix(self._menu_button)
        self.connect("activated", self._on_activate)
        self.set_activatable(True)

    def _on_popover_show(self, popover):
        child = self._popover.get_child()
        self._popover.set_child(None)
        self._popover.set_child(child)
        self._update_buttons_sensitive()
        first_button = self._multi_list_box.get_first_child()
        if first_button:
            first_button.grab_focus()
        self._update_scrolled_window_height()

    def _on_popover_closed(self, popover):
        if self._menu_button.get_sensitive():
            self._menu_button.grab_focus()
        elif self._flow_row:
            self._flow_row.grab_focus()
        else:
            self.grab_focus()
        self._update_scrolled_window_height()

    def _on_icon_finder_changed(self, event, icon_finder):
        GLib.idle_add(self._update_buttons_icon_names)

    def _on_activate(self, *args):
        self._popover.popup()

    def _on_multi_list_box_row_activated(self, event, list_box, row):
        self._update_buttons_sensitive()
        self._events.trigger("item-selected", row.name, row.label.get_text())
        self._popover.popdown()

    def _on_flow_row_text_changed(self, event, child, data):
        self._update_buttons_sensitive()
        GLib.idle_add(self._update_buttons_icon_names)

    def _update_buttons_icon_names(self):
        ignore_prefix = self._icon_finder.get_ignore_prefix()
        available_names = {}
        for original_name in self._buttons.keys():
            available_name = self._icon_finder.has_name(self._buttons[original_name].icon_name,
                use_alternatives=True, allow_symbolic=False)
            available_names[original_name] = available_name
        if (
            False in available_names.values()
            or True in [available_name.startswith(ignore_prefix) for available_name in available_names.values()]
        ):
            for name in self._buttons:
                icon_name = f"{ignore_prefix}{self._buttons[name].icon_name}"
                self._buttons[name].image.set_from_icon_name(icon_name)
        else:
            for original_name in available_names:
                self._buttons[original_name].image.set_from_icon_name(available_names[original_name])
        buttons = {}
        for button in self._buttons.values():
            buttons[button.label.get_text()] = button
        tags = {}
        for tag in self._flow_row.get_tags():
            tags[tag.get_text()] = tag
        for text in tags:
            if text in buttons:
                tags[text].set_icon_name(buttons[text].image.get_icon_name())
        self._update_scrolled_window_height()

    def _update_scrolled_window_height(self):
        height = self._multi_list_box.get_pixel_height_for_n_rows(self._display_n_buttons)
        self._scrolled_window.set_max_content_height(height + (2 * Margin.DEFAULT))

    def _update_buttons_sensitive(self):
        tag_texts = [tag.get_text() for tag in self._flow_row.get_tags()]
        for name in self._buttons:
            button = self._buttons[name]
            if not button.label.get_text() in tag_texts:
                if not self._multi_list_box.has_row(button, button.section):
                    self._multi_list_box.append_row(button, button.section, sort_data=button.label.get_text())
            else:
                if self._multi_list_box.has_row(button, button.section):
                    self._multi_list_box.remove_row(button, button.section)
        self._menu_button.set_sensitive(len(self._multi_list_box.get_visible_children()))

    def get_display_n_buttons(self):
        return self._display_n_buttons

    def set_display_n_buttons(self, n_buttons):
        self._display_n_buttons = value
        self._update_scrolled_window_height()

    def add_button(self, name, text, icon_name=None, section="default"):
        button = Gtk.ListBoxRow()
        button.image = Gtk.Image()
        button.image.set_margin_end(Margin.DEFAULT)
        button.label = Gtk.Label()
        button.label.set_text(text)
        button.box = Gtk.Box()
        button.box.append(button.image)
        button.box.append(button.label)
        button.set_child(button.box)
        button.set_activatable(True)
        button.name = name
        button.icon_name = icon_name
        button.section = section
        self._buttons[name] = button
        if not self._multi_list_box.has_section(section):
            self._multi_list_box.append_section(section)
        self._update_buttons_icon_names()
        self._update_buttons_sensitive()

    def remove_button(self, name, section="default"):
        button = self._buttons.pop(name)
        try:
            self._multi_list_box.remove_row(button, section)
        except ItemNotFoundError:
            pass
        self._update_buttons_sensitive()

    def get_buttons(self):
        return list(self._buttons.keys())

    def get_flow_row(self):
        return self._flow_row

    def set_flow_row(self, flow_row):
        flow_row.hook("text-changed", self._on_flow_row_text_changed)
        self._flow_row = flow_row

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class ResizeFrame(Gtk.Box):
    def __init__(self):
        super().__init__()
        self._events = basic.EventManager()
        self._events.add("resized", int, int)
        self._last_width = 0
        self._last_height = 0
        self._widget = None
        self._drawing_area = Gtk.DrawingArea()
        self._drawing_area.connect("resize", self._on_drawing_area_resize)
        self._size_group = Gtk.SizeGroup()
        self._size_group.add_widget(self._drawing_area)
        self._overlay = Gtk.Overlay()
        self._overlay.set_child(self._drawing_area)
        self._overlay.set_hexpand(True)
        self._overlay.set_vexpand(True)
        self._overlay.set_halign(Gtk.Align.FILL)
        self._overlay.set_valign(Gtk.Align.FILL)
        self.append(self._overlay)

    def _on_drawing_area_resize(self, drawing_area, width, height):
        if not width == self._last_width or not height == self._last_height:
            self._last_width = width
            self._last_height = height
            self._events.trigger("resized", width, height)

    def get_child(self):
        return self._widget

    def set_child(self, widget):
        if self._widget:
            self._overlay.remove_overlay(self._widget)
            self._size_group.remove_widget(self._widget)
        self._widget = widget
        self._size_group.add_widget(widget)
        self._overlay.add_overlay(widget)

    def get_width(self):
        return self._last_width

    def get_height(self):
        return self._last_height

    def hook(self, event, callback, *args):
        self._events.hook(event, callback, *args)

    def release(self, id):
        self._events.release(id)


class ScrolledSqueezer(Gtk.Box):
    def __init__(self):
        super().__init__()
        self._widget = None
        self._max_height = 0
        self._scrolled_window = Gtk.ScrolledWindow()
        self._drawing_area = Gtk.DrawingArea()
        self._drawing_area.connect("realize", self._on_drawing_area_realize)
        self._drawing_area.connect("resize", self._on_drawing_area_resize)
        self._size_group = Gtk.SizeGroup()
        self._size_group.add_widget(self._drawing_area)
        self._overlay = Gtk.Overlay()
        self._overlay.add_overlay(self._scrolled_window)
        self._overlay.set_child(self._drawing_area)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(self._overlay)

    def _on_drawing_area_realize(self, drawing_area):
        self._update_content_height()

    def _on_drawing_area_resize(self, drawing_area, width, height):
        self._update_content_height()

    def _after_update_content_height(self):
        if self._widget:
            additional_height = self._widget.get_margin_top() + self._widget.get_margin_bottom()
            height = self._widget.get_allocated_height() + additional_height
            max_height = self._max_height + additional_height
            if not height > max_height:
                self._scrolled_window.set_min_content_height(height)
                self._overlay.set_property("height-request", height)
            else:
                self._scrolled_window.set_min_content_height(max_height)
                self._overlay.set_property("height-request", max_height)

    def _update_content_height(self):
        self._after_update_content_height()
        GLib.idle_add(self._after_update_content_height)

    def get_max_height(self):
        return self._max_height

    def set_max_height(self, value):
        self._max_height = value
        self._update_content_height()

    def get_child(self):
        return self._widget

    def set_child(self, widget):
        if self._widget:
            self._widget.unparent()
            self._scrolled_window.set_child(None)
            self._size_group.remove_widget(self._widget)
        self._widget = widget
        self._widget.set_valign(Gtk.Align.START)
        self._size_group.add_widget(self._widget)
        self._scrolled_window.set_child(widget)
        self._update_content_height()


class TaggedRowTag(Gtk.FlowBoxChild):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._application = app
        self._icon_finder = app.get_icon_finder()
        self._timeout_id = None
        self._flow_row = None
        self._show_warning = False
        self._tag_dark_css_class = "background"
        self._icon_image = Gtk.Image()
        self._button_label = Gtk.Label()
        self._button_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._button_image = self._icon_finder.get_image("window-close-symbolic")
        self._button_image.set_margin_start(Margin.DEFAULT)
        self._center_box = Gtk.CenterBox()
        self._center_box.set_margin_start(Margin.LARGE)
        self._center_box.set_margin_end(Margin.LARGE)
        self._center_box.set_start_widget(self._icon_image)
        self._center_box.set_center_widget(self._button_label)
        self._center_box.set_end_widget(self._button_image)
        self._tag_button = Gtk.Button()
        self._tag_button.add_css_class("circular")
        self._tag_button.connect("clicked", self._on_tag_button_clicked)
        self._tag_button.set_child(self._center_box)
        self.set_focusable(False)
        self.set_child(self._tag_button)
        self.set_focus_child(self._tag_button)
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.connect("notify::dark", self._on_style_manager_dark_changed)
        self._update_tag_button_style()

    def _on_tag_button_clicked(self, button):
        if self._flow_row:
            self._flow_row.remove(self)
        else:
            self.get_parent().remove(self)

    def _on_style_manager_dark_changed(self, style_manager, gparam):
        self._update_tag_button_style()

    def _update_tag_button_style(self):
        if self._show_warning:
            self._tag_button.add_css_class("warning")
            self._tag_button.remove_css_class(self._tag_dark_css_class)
        else:
            self._tag_button.remove_css_class("warning")
            if self._style_manager.get_dark():
                self._tag_button.add_css_class(self._tag_dark_css_class)
            else:
                self._tag_button.remove_css_class(self._tag_dark_css_class)

    def _stop_warning(self):
        self._show_warning = False
        self._update_tag_button_style()
        self._timeout_id = None
        return GLib.SOURCE_REMOVE

    def get_icon_name(self):
        return self._icon_image.get_icon_name()

    def set_icon_name(self, icon_name):
        self._icon_image.set_from_icon_name(icon_name)

    def get_text(self):
        return self._button_label.get_text()

    def set_text(self, text):
        self._button_label.set_text(text)

    def get_flow_row(self):
        return self._flow_row

    def set_flow_row(self, flow_row):
        self._flow_row = flow_row

    def get_show_warning(self):
        return self._show_warning

    def set_show_warning(self, value, timeout=None):
        if value and timeout:
            if self._timeout_id:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None
            self._timeout_id = GLib.timeout_add_seconds(timeout, self._stop_warning)
        self._show_warning = value
        self._update_tag_button_style()


class TagNotFoundError(Exception):
    pass


class TaggedFlowRow(Adw.PreferencesRow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._events.add("text-changed", object, str)
        self._application = app
        self._icon_finder = app.get_icon_finder()
        self._ends_with_delimiter = None
        self._duplicate_tag_warnings = []
        self._delimiters = [";"]
        self._entry_row = None
        self._entry_row_default_values = {}
        self._entry_row_connection_ids = []
        self._flow_box_extra_margin = 1
        self._flow_box = Gtk.FlowBox()
        self._flow_box.set_sort_func(self._do_flow_box_sort)
        self._flow_box.set_margin_top(Margin.DEFAULT)
        self._flow_box.set_margin_bottom(Margin.DEFAULT)
        self._flow_box.set_margin_start(Margin.DEFAULT + self._flow_box_extra_margin)
        self._flow_box.set_margin_end(Margin.DEFAULT + self._flow_box_extra_margin)
        self._flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._scrolled_squeezer = ScrolledSqueezer()
        self._scrolled_squeezer.set_child(self._flow_box)
        self._scrolled_squeezer.set_max_height(480)
        self._revealer = Gtk.Revealer()
        self._revealer.connect("notify::reveal-child", self._on_revealer_reveal_child_changed)
        self._revealer.connect("notify::child-revealed", self._on_revealer_child_revealed_changed)
        self._revealer.set_child(self._scrolled_squeezer)
        self.set_activatable(False)
        self.set_visible(False)
        self.set_child(self._revealer)

    def _do_flow_box_sort(self, tag_1, tag_2):
        labels = [
            tag_1.get_text(),
            tag_2.get_text()
        ]
        if labels[0] == labels[1]:
            return 0
        else:
            if sorted(labels, key=str.lower)[0] == labels[0]:
                return -1
            else:
                return 1

    def _on_tag_event_controller_key_pressed(self, controller, keyval, keycode, state):
        if (
            (keyval == Keyval.LEFT or keyval == Keyval.UP or keyval == Keyval.PAGEUP)
            and self._flow_box.get_focus_child() == self._flow_box.get_first_child()
        ):
            self.grab_focus()
            return True

    def _on_revealer_reveal_child_changed(self, revealer, gparam):
        if self._revealer.get_reveal_child():
            self.show()

    def _on_revealer_child_revealed_changed(self, revealer, gparam):
        if not self._revealer.get_child_revealed():
            self.hide()

    def _on_entry_row_apply(self, entry_row):
        self.add_tags(entry_row.get_text(), allow_duplicates=False)
        self._entry_row.set_text("")

    def _on_entry_row_changed(self, editable):
        self._update_entry_row()

    def _do_flow_box_children_changed(self):
        self._events.trigger("text-changed", self, self.get_text())
        self._update_reveal_child()
        self._update_entry_row()

    def _update_reveal_child(self):
        self._revealer.set_reveal_child(self._flow_box.get_first_child())

    def _update_entry_row(self):
        if self._entry_row:
            text = self._entry_row.get_text()
            strings = self._split_text(text)
            duplicate_strings, duplicate_tags = self._get_duplicates(*strings, mark_duplicates=True)
            if not len(strings):
                self._entry_row.set_show_apply_button(False)
                self._entry_row.set_show_apply_button(True)

    def _split_text(self, *strings):
        for string in strings:
            for delimiter in self._delimiters:
                pieces = []
                for string in strings:
                    pieces += string.split(delimiter)
                strings = pieces
        else:
            return list(filter(None, strings))

    def _get_duplicates(self, *strings, mark_duplicates=False, warning_timeout=None):
        duplicate_strings, duplicate_tags = [], []
        for string in strings:
            if not string in duplicate_strings:
                for tag in self.get_tags():
                    if string == tag.get_text():
                        duplicate_tags.append(tag)
                        if not string in duplicate_strings:
                            duplicate_strings.append(string)
        else:
            if mark_duplicates:
                if not warning_timeout:
                    for tag in self._duplicate_tag_warnings:
                        tag.set_show_warning(False)
                    self._duplicate_tag_warnings = duplicate_tags
                for tag in duplicate_tags:
                    tag.set_show_warning(True, timeout=warning_timeout)
            return duplicate_strings, duplicate_tags

    def get_entry_row(self):
        return self._entry_row

    def set_entry_row(self, entry_row):
        if self._entry_row:
            for connection_id in self._entry_row_connection_ids:
                self._entry_row.disconnect(connection_id)
            self._entry_row.set_show_apply_button(self._entry_row_default_values["show-apply-button"])
        self._entry_row = entry_row
        self._entry_row_default_values["show-apply-button"] = entry_row.get_show_apply_button()
        entry_row.set_show_apply_button(True)
        self._entry_row_connection_ids.append(entry_row.connect("apply", self._on_entry_row_apply))
        self._entry_row_connection_ids.append(entry_row.connect("changed", self._on_entry_row_changed))

    def get_delimiters(self):
        return self._delimiters

    def set_delimiters(self, *strings):
        self._delimiters = list(*strings)

    def get_text(self):
        return self._delimiters[0].join([tag.get_text() for tag in self.get_tags()]) + int(
            bool(self._ends_with_delimiter)) * ";"

    def set_text(self, *strings):
        self._ends_with_delimiter = strings[-1].endswith(self._delimiters[0])
        for tag in self.get_tags():
            self._flow_box.remove(tag)
        self._update_reveal_child()
        self._update_entry_row()
        self.add_tags(*strings)

    def get_tags(self):
        tags = [self._flow_box.get_first_child()]
        if tags[0]:
            while True:
                next_sibling = tags[-1].get_next_sibling()
                if next_sibling:
                    tags.append(next_sibling)
                else:
                    return tags
        else:
            return []

    def add_tags(self, *strings, allow_duplicates=True, warning_timeout=None):
        strings = self._split_text(*strings)
        if not allow_duplicates:
            duplicate_strings, duplicate_tags = self._get_duplicates(*strings, mark_duplicates=True,
                warning_timeout=warning_timeout)
            strings = [string for string in strings if not string in duplicate_strings]
        for string in strings:
            self.add(string, send_signals=False)
        if len(strings):
            self._do_flow_box_children_changed()

    def add(self, text, send_signals=True):
        if isinstance(text, TaggedRowTag):
            tag = text
        else:
            tag = TaggedRowTag(self._application)
            tag.set_text(text)
        event_controller_key = Gtk.EventControllerKey()
        event_controller_key.connect("key-pressed", self._on_tag_event_controller_key_pressed)
        tag.add_controller(event_controller_key)
        tag.set_flow_row(self)
        self._flow_box.insert(tag, -1)
        if send_signals:
            self._do_flow_box_children_changed()

    def remove(self, text):
        if isinstance(text, TaggedRowTag):
            self._flow_box.remove(text)
            self._do_flow_box_children_changed()
        else:
            for tag in self.get_tags():
                if tag.get_text() == text:
                    self._flow_box.remove(tag)
                    self._do_flow_box_children_changed()
                    break
            else:
                raise TagNotFoundError(text)

    def reset(self):
        if self._entry_row:
            self._entry_row.set_text("")
        if self._flow_box.get_first_child():
            for tag in self.get_tags():
                self._flow_box.remove(tag)
            self._do_flow_box_children_changed()
        self._update_reveal_child()

    def hook(self, event, callback):
        return self._events.hook(event, callback)

    def release(self, id):
        self._events.release(id)


class ItemAlreadyExistingError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


class SearchList(Gtk.Box):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._events.add("item-activated", str)
        self._names = {}
        self._children = {}
        self._last_activated = None
        self._ignore_selection = False
        self._reset_by_unfocus = False
        self._icon_finder = app.get_icon_finder()
        self._icon_finder.hook("changed", self._on_icon_finder_changed)
        self._application_window = app.get_application_window()
        self._toggle_button = Gtk.ToggleButton()
        self._toggle_button.set_icon_name(self._icon_finder.get_name("system-search-symbolic"))
        self._toggle_button.connect("toggled", self._on_toggle_button_toggled)
        self._search_entry_event_controller_focus = Gtk.EventControllerFocus()
        self._search_entry_event_controller_focus.connect("leave", self._on_search_entry_event_controller_focus_leave)
        self._search_entry_event_controller_key = Gtk.EventControllerKey()
        self._search_entry_event_controller_key.connect("key-pressed", self._on_search_entry_controller_key_pressed)
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_hexpand(True)
        self._search_entry.add_controller(self._search_entry_event_controller_focus)
        self._search_entry.add_controller(self._search_entry_event_controller_key)
        self._search_entry.connect("search-changed", self._on_search_entry_search_changed)
        self._search_bar = Gtk.SearchBar()
        self._search_bar.set_key_capture_widget(self._application_window)
        self._search_bar.connect("notify::search-mode-enabled", self._on_search_bar_search_mode_enabled_changed)
        self._search_bar.set_child(self._search_entry)
        self._search_bar_box = Gtk.Box()
        self._search_revealer = self._search_bar.get_child().get_parent().get_parent()
        self._search_revealer.set_child(self._search_bar_box)
        self._search_bar_box.append(self._search_entry)
        self._search_bar.connect_entry(self._search_entry)
        self._list_box_event_controller_key = Gtk.EventControllerKey()
        self._list_box_event_controller_key.connect("key-pressed", self._on_list_box_controller_key_pressed)
        self._list_box = Gtk.ListBox()
        self._list_box.set_sort_func(self._do_list_box_sort)
        self._list_box.add_css_class("navigation-sidebar")
        self._list_box.set_selection_mode(Gtk.SelectionMode.BROWSE)
        self._list_box.connect("selected-rows-changed", self._on_list_box_selected_rows_changed)
        self._list_box.add_controller(self._list_box_event_controller_key)
        self._list_box.connect("row-activated", self._on_list_box_row_activated)
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_vexpand(True)
        self._scrolled_window.set_kinetic_scrolling(True)
        self._scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.set_child(self._list_box)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.append(self._search_bar)
        self.append(self._scrolled_window)

    def _on_icon_finder_changed(self, event, icon_finder):
        for name in self._children:
            GLib.idle_add(self._update_item_image, self._children[name]["image"], self._children[name]["icon"])

    def _on_toggle_button_toggled(self, button):
        self._search_bar.set_search_mode(button.get_active())

    def _on_search_entry_search_changed(self, search_entry):
        if not len(self._search_entry.get_text()) and not self._search_bar.get_focus_child():
            self._search_bar.set_search_mode(False)
        self._update_search_results()

    def _on_search_bar_search_mode_enabled_changed(self, search_bar, property):
        value = self._search_bar.get_search_mode()
        if self._reset_by_unfocus and self._application_window.get_focus() == self._toggle_button:
            self._reset_by_unfocus = False
        else:
            self._toggle_button.set_active(value)
        if not value and self._search_bar.get_focus_child():
            self._list_box.child_focus(Gtk.DirectionType.DOWN)

    def _on_search_entry_event_controller_focus_leave(self, controller):
        if self._search_bar.get_search_mode() and not len(self._search_entry.get_text()):
            self._reset_by_unfocus = True
            GLib.idle_add(self._search_bar.set_search_mode, False)

    def _on_search_entry_controller_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Keyval.ESCAPE:
            self._search_bar.set_search_mode(False)
            return True
        elif keyval == Keyval.UP or keyval == Keyval.PAGEUP:
            self._toggle_button.grab_focus()
            if not len(self._search_entry.get_text()):
                self._toggle_button.set_active(False)
            return True
        elif keyval == Keyval.DOWN or keyval == Keyval.PAGEDOWN:
            if not len(self._search_entry.get_text()):
                self._search_bar.set_search_mode(False)
            else:
                self._list_box.child_focus(Gtk.DirectionType.DOWN)
            return True
        elif (
            keyval == Keyval.TAB and self._last_activated
            and not self._children[self._last_activated]["widget"].get_visible()
        ):
            self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
            self._list_box.set_selection_mode(Gtk.SelectionMode.BROWSE)

    def _on_list_box_controller_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Keyval.ESCAPE and self._search_bar.get_search_mode():
            self._search_bar.grab_focus()
            self._search_bar.set_search_mode(False)
            return True
        elif (
            (keyval == Keyval.UP or keyval == Keyval.PAGEUP)
            and self._list_box.get_focus_child() == self._list_box.get_first_child()
        ):
            if not self._search_bar.get_search_mode():
                self._search_bar.set_search_mode(True)
            self._search_entry.grab_focus()
            return True

    def _on_list_box_selected_rows_changed(self, listbox):
        if not self._ignore_selection:
            self._list_box.unselect_all()
            if self._last_activated in self._children:
                self._list_box.select_row(self._children[self._last_activated]["widget"])
            else:
                self._list_box.select_row(None)

    def _on_list_box_row_activated(self, list_box, row):
        self._ignore_selection = True
        if self._events.trigger("item-activated", self._names[row]):
            self._last_activated = self._names[row]
        self._list_box.select_row(row)
        self._ignore_selection = False

    def _do_list_box_sort(self, row_1, row_2):
        labels = [
            self._children[self._names[row_1]]["label"].get_text(),
            self._children[self._names[row_2]]["label"].get_text()
        ]
        if labels[0] == labels[1]:
            return 0
        else:
            if sorted(labels, key=str.lower)[0] == labels[0]:
                return -1
            else:
                return 1

    def _get_visible_children(self):
        children = []
        for child in list(reversed(self._children.values())):
            if child["widget"].get_visible():
                children.append(child["widget"])
        return children

    def _update_search_results(self):
        text = self._search_entry.get_text().lower()
        for name in self._children:
            for keyword in self._children[name]["keywords"]:
                if text in keyword:
                    self._children[name]["widget"].set_visible(True)
                    break
            else:
                self._children[name]["widget"].set_visible(False)

    def _update_item_image(self, image, icon):
        try:
            self._icon_finder.set_image(image, icon, missing_ok=False, use_alternatives=False)
        except IconNotFoundError:
            image.clear()

    def get_active_item(self):
        return self._last_activated

    def set_active_item(self, name, activate=True):
        if name is None:
            self._list_box.unselect_all()
            self._last_activated = None
        else:
            item = self._children[name]["widget"]
            if not item in self._list_box.get_selected_rows():
                self._list_box.select_row(item)
                if activate:
                    item.activate()

    def get_search_mode(self):
        return self._search_bar.get_search_mode()

    def set_search_mode(self, value):
        self._search_bar.set_search_mode(value)

    def get_search_bar(self):
        return self._search_bar

    def get_search_button(self):
        return self._toggle_button

    def get_search_entry(self):
        return self._search_entry

    def get_visible_items(self):
        children = []
        child = self._list_box.get_first_child()
        while True:
            if not child == None:
                children.append(child)
                child = children[-1].get_next_sibling()
            else:
                break
        return [self._names[child] for child in children if child.get_visible()]
        items = []
        for child in self._children:
            if self._children[child]["widget"].get_visible():
                items.append(child)
        else:
            return items

    def list(self):
        return list(self._children)

    def clear(self):
        for name in self.list():
            self.remove(name)

    def update(self, name, text, icon, keywords, invalidate_sort=True):
        if name in self._children:
            image = self._children[name]["image"]
            label = self._children[name]["label"]
            self._children[name]["icon"] = icon
            GLib.idle_add(self._update_item_image, image, icon)
            label.set_text(text)
            self._children[name]["keywords"] = [keyword.lower() for keyword in keywords]
            if invalidate_sort:
                self._list_box.invalidate_sort()
            self._update_search_results()
        else:
            raise ItemNotFoundError(name)

    def add(self, name, text, icon=None, keywords=None):
        if not name in self._children:
            image = Gtk.Image()
            image.set_pixel_size(48)
            label = Gtk.Label()
            label.set_ellipsize(Pango.EllipsizeMode.END)
            box = Gtk.Box()
            box.set_margin_top(Margin.DEFAULT)
            box.set_margin_bottom(Margin.DEFAULT)
            box.set_margin_start(Margin.DEFAULT)
            box.set_margin_end(Margin.DEFAULT)
            box.set_spacing(Spacing.DEFAULT)
            box.append(image)
            box.append(label)
            child = Gtk.ListBoxRow()
            child.set_child(box)
            self._names[child] = name
            self._children[name] = {}
            self._children[name]["widget"] = child
            self._children[name]["image"] = image
            self._children[name]["label"] = label
            if not isinstance(keywords, list):
                keywords = [text]
            self.update(name, text, icon, keywords, invalidate_sort=False)
            self._list_box.prepend(child)
            self._update_search_results()
        else:
            raise ItemAlreadyExistingError(name)

    def remove(self, name):
        if name in self._children:
            child = self._children[name]["widget"]
            self._list_box.remove(child)
            del self._names[child]
            del self._children[name]
            self._update_search_results()
        else:
            raise ItemNotFoundError(name)

    def hook(self, event, callback):
        return self._events.hook(event, callback)

    def release(self, id):
        self._events.release(id)

    def grab_focus(self):
        if not self._search_bar.get_search_mode():
            self._search_bar.set_search_mode(True)
        self._search_entry.grab_focus()


class ItemNotSwitchError(Exception):
    pass


class Menu(Gio.Menu):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = basic.EventManager()
        self._application_window = app.get_application_window()
        self._names = {}
        self._widgets = {}

    def _on_action_event(self, action, property):
        self._events.trigger(self._names[action])

    def get_switch_state(self, name):
        if isinstance(self._widgets[name], Gtk.Switch):
            return self._widgets[name].get_active()
        else:
            raise ItemNotSwitchError(name)

    def set_switch_state(self, name, value):
        if isinstance(self._widgets[name], Gtk.Switch):
            self._widgets[name].set_active(value)
        else:
            raise ItemNotSwitchError(name)

    def _add_action(self, action, widget, name, label):
        self.append(label, "win.%s" % name)
        self._events.add(name)
        self._names[action] = name
        self._widgets[name] = widget
        self._application_window.add_action(action)

    def get_enabled(self, name):
        for action in self._names:
            if self._names[action] == name:
                return action.get_enabled()
        else:
            raise ItemNotFoundError(name)

    def set_enabled(self, name, value):
        for action in self._names:
            if self._names[action] == name:
                action.set_enabled(value)
                break
        else:
            raise ItemNotFoundError(name)

    def add_button(self, name, label):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", self._on_action_event)
        self._add_action(action, None, name, label)

    def add_switch(self, name, label):
        widget = Gtk.Switch()
        action = Gio.PropertyAction.new(name, widget, "active")
        action.connect("notify", self._on_action_event)
        self._add_action(action, widget, name, label)

    def hook(self, name, callback):
        return self._events.hook(name, callback)

    def release(self, id):
        self._events.release(id)


class Application(Adw.Application):
    def __init__(self, project_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._application_window = Adw.ApplicationWindow()
        self._project_dir = os.path.abspath(os.path.realpath(project_dir))
        self._app_name = os.path.basename(self._project_dir)
        self._config_dir = os.path.join(GLib.get_user_data_dir(), self._app_name)
        self._cache_dir = os.path.join(GLib.get_user_cache_dir(), self._app_name)
        self._flatpak_filesystem_prefix = os.path.join(os.path.sep, "run", "host")
        if os.getenv("APP_RUNNING_AS_FLATPAK") == "true":
            home_var = self.get_flatpak_host_environment_variable("HOME")
            if home_var:
                self._flatpak_real_home = os.path.abspath(home_var)
            else:
                self._flatpak_real_home = os.path.join(os.path.sep, "home", os.getenv("USER"))
        else:
            self._flatpak_real_home = None
        self._command_arg_escaper = basic.DesktopEntryCommandArgEscaper()
        self._config_manager = basic.ConfigManager(
            os.path.join(self._project_dir, "default.json"),
            os.path.join(self._config_dir, "config.json")
        )
        self._locale_manager = basic.LocaleManager(
            os.path.join(self._project_dir, "locales")
        )
        self._icon_finder = IconFinder(self)
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
        if os.getenv("APP_RUNNING_AS_FLATPAK") == "true":
            self._system_data_dirs = [
                os.path.join(GLib.get_user_data_dir(), "flatpak", "exports", "share"),
                os.path.join(os.path.sep, "var", "lib", "flatpak", "exports", "share"),
                os.path.join(os.path.sep, "var", "lib", "snapd", "desktop"),
                os.path.join(self._flatpak_filesystem_prefix, "usr", "local", "share"),
                os.path.join(self._flatpak_filesystem_prefix, "usr", "share")
            ]
            try:
                for path in self.get_flatpak_host_environment_variable("XDG_DATA_DIRS").split(":"):
                    if path.startswith("~"):
                        path = self._join_path_prefix(self._flatpak_real_home, path[1:])
                    if path.startswith(self._flatpak_real_home) and not path in self._system_data_dirs:
                        self._system_data_dirs.append(path)
                    path = self._join_path_prefix(self._flatpak_filesystem_prefix, path)
                    if not path in self._system_data_dirs:
                        self._system_data_dirs.append(path)
            except AttributeError as e:
                if self.get_flatpak_host_environment_variable("XDG_DATA_DIRS"):
                    raise e
            self._icon_search_dirs = [
                self._join_path_prefix(self._flatpak_filesystem_prefix, self._flatpak_real_home, ".local", "share",
                    "icons"),
                self._join_path_prefix(self._flatpak_filesystem_prefix, self._flatpak_real_home, ".local", "share",
                    "pixmaps"),
                self._join_path_prefix(self._flatpak_filesystem_prefix, self._flatpak_real_home, ".icons"),
                self._join_path_prefix(self._flatpak_filesystem_prefix, self._flatpak_real_home, ".pixmaps")
            ]
            for path in self._system_data_dirs:
                self._icon_search_dirs.append(os.path.join(path, "icons"))
                self._icon_search_dirs.append(os.path.join(path, "pixmaps"))
        else:
            self._system_data_dirs = [
                os.path.join(GLib.get_user_data_dir(), "flatpak", "exports", "share"),
                os.path.join(os.path.sep, "var", "lib", "flatpak", "exports", "share"),
                os.path.join(os.path.sep, "var", "lib", "snapd", "desktop"),
                os.path.join(os.path.sep, "usr", "local", "share"),
                os.path.join(os.path.sep, "usr", "share")
            ]
            try:
                for path in os.getenv("XDG_DATA_DIRS").split(":"):
                    if path.startswith("~"):
                        path = self._join_path_prefix(GLib.get_home_dir(), path[1:])
                    if not path in self._system_data_dirs:
                        self._system_data_dirs.append(path)
            except AttributeError as e:
                if os.getenv("XDG_DATA_DIRS"):
                    raise e
            self._icon_search_dirs = [
                os.path.join(GLib.get_user_data_dir(), "icons"),
                os.path.join(GLib.get_user_data_dir(), "pixmaps"),
                os.path.join(GLib.get_home_dir(), ".icons"),
                os.path.join(GLib.get_home_dir(), ".pixmaps")
            ]
            for path in self._system_data_dirs:
                self._icon_search_dirs.append(os.path.join(path, "icons"))
                self._icon_search_dirs.append(os.path.join(path, "pixmaps"))
        self._icon_search_dirs.append(os.path.join(self.get_project_dir(), "icons"))
        self._icon_finder.add_search_paths(*self._icon_search_dirs)
        self._command_dirs = []
        if os.getenv("APP_RUNNING_AS_FLATPAK") == "true":
            self._command_lookup_cwd = self._flatpak_real_home
            try:
                for path in self.get_flatpak_host_environment_variable("PATH").split(":"):
                    if path.startswith("~"):
                        path = self._join_path_prefix(self._flatpak_real_home, path[1:])
                    if path.startswith(self._flatpak_real_home) and not path in self._command_dirs:
                        self._command_dirs.append(path)
                    path = self._join_path_prefix(self._flatpak_filesystem_prefix, path)
                    if not path in self._command_dirs:
                        self._command_dirs.append(path)
            except AttributeError as e:
                if self.get_flatpak_host_environment_variable("PATH"):
                    raise e
        else:
            self._command_lookup_cwd = GLib.get_home_dir()
            try:
                for path in os.getenv("PATH").split(":"):
                    if path.startswith("~"):
                        path = self._join_path_prefix(GLib.get_home_dir(), path[1:])
                    if not path in self._command_dirs:
                        self._command_dirs.append(path)
            except AttributeError as e:
                if os.getenv("PATH"):
                    raise e
        self.connect("activate", self._on_activate)
        self.connect("shutdown", self._on_shutdown)

    def _on_activate(self, app):
        GLib.set_prgname(self._app_name)
        self._application_window.set_default_size(
            self._config_manager.get("window.width"),
            self._config_manager.get("window.height")
        )
        if self._config_manager.get("window.maximized"):
            self._application_window.maximize()
        self._application_window.set_application(self)
        self._application_window.show()

    def _on_shutdown(self, app):
        self._config_manager.set("window.width", self._application_window.get_default_size()[0])
        self._config_manager.set("window.height", self._application_window.get_default_size()[1])
        self._config_manager.set("window.maximized", self._application_window.is_maximized())
        self._config_manager.save()

    def _join_path_prefix(self, *paths):
        names = [""]
        for path in paths:
            names.append(os.path.sep.join(list(filter(None, path.split(os.path.sep)))))
        return os.path.sep.join(names)

    def get_application_window(self):
        return self._application_window

    def get_project_dir(self):
        return self._project_dir

    def get_app_name(self):
        return self._app_name

    def get_config_dir(self):
        return self._config_dir

    def get_cache_dir(self):
        return self._cache_dir

    def get_config_manager(self):
        return self._config_manager

    def get_locale_manager(self):
        return self._locale_manager

    def get_icon_finder(self):
        return self._icon_finder

    def get_flatpak_host_system_path(self, path):
        if path.startswith(self._flatpak_filesystem_prefix):
            return os.path.join(os.path.sep, path[len(self._flatpak_filesystem_prefix):])
        else:
            return path

    def get_flatpak_sandbox_system_path(self, path):
        if not os.path.exists(path):
            target = path
            while True:
                if os.path.islink(target):
                    target = os.path.realpath(path)
                test = os.path.join(self._join_path_prefix(self._flatpak_filesystem_prefix, target))
                if os.path.exists(test):
                    return test
                elif os.path.islink(test):
                    target = os.path.realpath(test)
                else:
                    return path
        else:
            return path

    def get_flatpak_host_environment_variable(self, variable):
        printenv_commands = [
            ["flatpak-spawn", "--host", "printenv", variable],
            ["flatpak-spawn", "--host", "sh", "-c", f"echo ${variable}"]
        ]
        for command in printenv_commands:
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if not process.returncode:
                decoded_stdout = stdout.decode().split("\n")[0]
                if len(decoded_stdout):
                    return decoded_stdout

    def get_command_exists(self, text, desktop_entry=False, skip_empty_path=False, include_lookup_cwd=False):
        if len(text):
            first_arg = self._command_arg_escaper.get_first_arg_from_command(text)
            if desktop_entry:
                if (self._command_arg_escaper.get_has_quotes(first_arg)
                    and self._command_arg_escaper.get_has_escaped_chars(first_arg)
                ):
                    executable = self._command_arg_escaper.get_unescaped_arg(first_arg)
                else:
                    executable = first_arg
            else:
                executable = first_arg
            if os.path.sep in executable:
                if executable.startswith(os.path.sep):
                    if os.getenv("APP_RUNNING_AS_FLATPAK") == "true" and not executable.startswith(self._flatpak_real_home):
                        executable = self._join_path_prefix(self._flatpak_filesystem_prefix, executable)
                        executable = self.get_flatpak_sandbox_system_path(executable)
                elif include_lookup_cwd:
                    executable = os.path.join(self._command_lookup_cwd, executable)
                if os.access(executable, os.X_OK) and os.path.isfile(executable):
                    return executable
            elif skip_empty_path and not len(self._command_dirs):
                return True
            elif len(executable):
                command_dirs = self._command_dirs
                if include_lookup_cwd:
                    command_dirs.append(self._command_lookup_cwd)
                for command_dir in command_dirs:
                    path = self._join_path_prefix(command_dir, executable)
                    if os.getenv("APP_RUNNING_AS_FLATPAK") == "true" and not path.startswith(self._flatpak_real_home):
                        path = self.get_flatpak_sandbox_system_path(path)
                    if os.access(path, os.X_OK) and os.path.isfile(path):
                        return path

    def get_flatpak_real_home(self):
        return self._flatpak_real_home
