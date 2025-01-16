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


import os, sys, string, random, shutil, subprocess, datetime, gi

gi.require_version("Adw", "1")

gi.require_version("Gtk", "4.0")

gi.require_version("Gdk", "4.0")

gi.require_version("Gio", "2.0")

gi.require_version("GLib", "2.0")

from gi.repository import Adw

from gi.repository import Gtk

from gi.repository import Gdk

from gi.repository import Gio

from gi.repository import GLib

from configparser import ConfigParser

from modules import gui, basic


class NoAccessError(Exception):

    pass


class DesktopParser():

    def __init__(self, app, load_path, save_path):

        self._application = app

        self._config_parser = ConfigParser(interpolation=None, strict=False)

        self._config_parser.optionxform = str

        self._system_locale_names = list(filter(None, [

            os.getenv("LANG").split(".")[0].split("_")[0],

            os.getenv("LANG").split(".")[0],

            os.getenv("LANG")

            ]))

        self._load_path = load_path

        self._save_path = save_path

        self.load()

    def _get_action_from_section(self, section):

        return section[len("Desktop Action "):]

    def _get_section_from_action(self, action):

        return "Desktop Action %s" % action

    def _get_str(self, key, section="Desktop Entry", localized=False, value=""):

        if self._config_parser.has_section(section):

            if localized:

               for locale in self._system_locale_names:

                    localized_key = "%s[%s]" % (key, locale)

                    if self._config_parser.has_option(section, localized_key):

                        return self._config_parser.get(section, localized_key)

            if self._config_parser.has_option(section, key):

                return self._config_parser.get(section, key)

        return value

    def _get_bool(self, key, section="Desktop Entry"):

        if self._config_parser.has_section(section):

            if self._config_parser.has_option(section, key):

                try:

                    return self._config_parser.getboolean(section, key)

                except ValueError as error:

                    self._application.log(error, error=error)

                    return False

            else:

                return False

        else:

            return False

    def _set(self, key, value, section="Desktop Entry", localized=False):

        if isinstance(value, bool):

            if value:

                value = "true"

            else:

                value = "false"

        if len(value):

            if section == "Desktop Entry" and not self._config_parser.has_section(section):

                self._config_parser.add_section(section)

            self._config_parser.set(section, key, value)

            if localized:

                for locale in self._system_locale_names:

                    localized_key = "%s[%s]" % (key, locale)

                    self._config_parser.set(section, localized_key, value)

        else:

            if self._config_parser.has_option(section, key):

                self._config_parser.remove_option(section, key)

            if localized:

                for locale in self._system_locale_names:

                    localized_key = "%s[%s]" % (key, locale)

                    if self._config_parser.has_option(section, localized_key):

                        self._config_parser.remove_option(section, localized_key)

    def get_action_name(self, action):

        return self.get_name(section=self._get_section_from_action(action))

    def set_action_name(self, action, name):

        self.set_name(name, section=self._get_section_from_action(action))

    def get_action_command(self, action):

        return self.get_command(section=self._get_section_from_action(action))

    def set_action_command(self, action, command):

        self.set_command(command, section=self._get_section_from_action(action))

    def get_name(self, section="Desktop Entry"):

        return self._get_str("Name", section=section, localized=True)

    def set_name(self, name, section="Desktop Entry"):

        self._set("Name", name, section=section, localized=True)

    def get_comment(self, section="Desktop Entry"):

        return self._get_str("Comment", section=section, localized=True)

    def set_comment(self, comment, section="Desktop Entry"):

        self._set("Comment", comment, section=section, localized=True)

    def get_keywords(self, section="Desktop Entry"):

        return self._get_str("Keywords", section=section, localized=True)

    def set_keywords(self, comment, section="Desktop Entry"):

        self._set("Keywords", comment, section=section, localized=True)

    def get_only_show_in(self, section="Desktop Entry"):

        return self._get_str("OnlyShowIn", section=section)

    def set_only_show_in(self, comment, section="Desktop Entry"):

        self._set("OnlyShowIn", comment, section=section)

    def get_not_show_in(self, section="Desktop Entry"):

        return self._get_str("NotShowIn", section=section)

    def set_not_show_in(self, comment, section="Desktop Entry"):

        self._set("NotShowIn", comment, section=section)

    def get_categories(self, section="Desktop Entry"):

        return self._get_str("Categories", section=section)

    def set_categories(self, comment, section="Desktop Entry"):

        self._set("Categories", comment, section=section)

    def get_icon(self, section="Desktop Entry"):

        return self._get_str("Icon", section=section)

    def set_icon(self, icon, section="Desktop Entry"):

        self._set("Icon", icon, section=section)

    def get_command(self, section="Desktop Entry"):

        return self._get_str("Exec", section=section)

    def set_command(self, command, section="Desktop Entry"):

        self._set("Exec", command, section=section)

    def get_disabled(self, section="Desktop Entry"):

        return self._get_bool("Hidden", section=section)

    def set_disabled(self, value, section="Desktop Entry"):

        self._set("Hidden", value, section=section)

    def get_hidden(self, section="Desktop Entry"):

        return self._get_bool("NoDisplay", section=section)

    def set_hidden(self, value, section="Desktop Entry"):

        self._set("NoDisplay", value, section=section)

    def get_visible(self, section="Desktop Entry"):

        return not self.get_hidden() and not self.get_disabled()

    def set_visible(self, value, section="Desktop Entry"):

        if value:

            self.set_disabled(False)

            self.set_hidden(False)

        else:

            self.set_hidden(True)

    def get_notify(self, section="Desktop Entry"):

        return self._get_bool("StartupNotify", section=section)

    def set_notify(self, value, section="Desktop Entry"):

        self._set("StartupNotify", value, section=section)

    def get_terminal(self, section="Desktop Entry"):

        return self._get_bool("Terminal", section=section)

    def set_terminal(self, value, section="Desktop Entry"):

        self._set("Terminal", value, section=section)

    def get_mimetypes(self):

        if self._config_parser.has_option("Desktop Entry", "MimeType"):

            return list(filter(None, self._config_parser.get("Desktop Entry", "MimeType").split(";")))

        else:

            return []

    def get_load_path(self):

        return self._load_path

    def set_load_path(self, path):

        self._load_path = path

    def get_save_path(self):

        return self._save_path

    def set_save_path(self, path):

        self._save_path = path

    def get_search_data(self):

        data = []

        data.append(self.get_name())

        data.append(self.get_icon())

        data.append(self.get_command())

        data.append(self.get_keywords())

        data.append(self.get_categories())

        data.append(self.get_only_show_in())

        data.append(self.get_not_show_in())

        data.append(self._get_str("MimeType"))

        data.append(os.path.basename(self._load_path))

        return list(filter(None, data))

    def get_actions(self):

        actions = []

        for section in self._config_parser.sections():

            if section.startswith("Desktop Action "):

                actions.append(self._get_action_from_section(section))

        return actions

    def add_action(self, action):

        section = self._get_section_from_action(action)

        if not self._config_parser.has_section(section):

            self._config_parser.add_section(section)

    def remove_action(self, action):

        self._config_parser.remove_section(self._get_section_from_action(action))

    def check_read(self, path=None):

        if path is None:

            path = self._load_path

        if os.path.exists(path):

            try:

                with open(path, "r") as file:

                    pass

            except Exception as e:

                raise NoAccessError(e)

        else:

            OSError(f"not found: {path}")

    def check_write(self, path=None):

        if path is None:

            path = self._save_path

        while True:

            if os.path.exists(path):

                if os.path.isdir(path):

                    if not os.access(path, os.W_OK):

                        raise NoAccessError(f"no access: {path}")

                    else:

                        return

                else:

                    break

            else:

                dirname = os.path.dirname(path)

                if not os.path.abspath(dirname) == os.path.abspath(path):

                    path = dirname

                else:

                    raise NoAccessError(f"no access: {path}")

        else:

            raise NoAccessError(f"no access: {path}")

        try:

            with open(path, "a") as file:

                pass

        except Exception as e:

            raise NoAccessError(e)

    def load(self, path=None):

        self.check_read(path=path)

        if path is None:

            path = self._load_path

        self._config_parser.clear()

        self._config_parser.read(path)

    def save(self, path=None):

        self.check_write(path=path)

        if path is None:

            path = self._save_path

        actions = self.get_actions()

        self._set("Actions", f"{';'.join(actions)}{bool(len(actions))*';'}")

        if not os.path.exists(path):

            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        else:

            os.remove(path)

        with open(path, "w") as file:

            self._config_parser.write(file, space_around_delimiters=False)


class DefaultTextEditor():

    def __init__(self, app):

        self._application = app

        self._locale_manager = app.get_locale_manager()

        self._application.connect("shutdown", self._on_application_shutdown)

        self._events = basic.EventManager()

        self._events.add("update", str)

        self._parsers = {}

        self._edit_dir = os.path.join(app.get_cache_dir(), "text-editor-links")

        self._path_inspector = basic.PathInspector()

        self._path_inspector.hook("changed", self._on_path_inspector_changed)

        self._path_inspector.hook("created", self._on_path_inspector_created)

        self._path_inspector.hook("deleted", self._on_path_inspector_deleted)

        self._external_launch_apps = [

            Gio.AppInfo.get_default_for_type("text/plain", False)

            ]

        for app in Gio.AppInfo.get_recommended_for_type("text/plain"):

            self._external_launch_apps.append(app)

        for app in Gio.AppInfo.get_fallback_for_type("text/plain"):

            self._external_launch_apps.append(app)

        for app in Gio.AppInfo.get_all_for_type("text/plain"):

            self._external_launch_apps.append(app)

    def _on_application_shutdown(self, app):

        self.exit()

    def _on_path_inspector_changed(self, event, edit_path, timestamp):

        name = self._get_name_from_edit_path(edit_path)

        GLib.idle_add(self._trigger_update_event, name)

    def _on_path_inspector_created(self, event, edit_path, timestamp):

        name = self._get_name_from_edit_path(edit_path)

        GLib.idle_add(self._trigger_update_event, name)

    def _on_path_inspector_deleted(self, event, edit_path, timestamp):

        GLib.idle_add(self._path_inspector.remove, edit_path)

        name = self._get_name_from_edit_path(edit_path)

        del self._original_paths[name]

    def _get_name_from_edit_path(self, edit_path):

        return os.path.relpath(edit_path, self._edit_dir)[:-len(".ini")].strip(os.path.sep)

    def _get_files_identical(self, first, second):

        if os.path.exists(first) and os.path.exists(second):

            with open(first, "r") as first_file:

                with open(second, "r") as second_file:

                    if first_file.read().replace("\n\n", "\n") == second_file.read().replace("\n\n", "\n"):

                        return True

    def _get_copy_source_path(self, parser):

        if os.path.exists(parser.get_save_path()):

            return parser.get_save_path()

        else:

            return parser.get_load_path()

    def _trigger_update_event(self, name):

        parser = self._parsers[name]["parser"]

        edit_path = self._parsers[name]["edit-path"]

        if not self._get_files_identical(parser.get_save_path(), edit_path):

            self._events.trigger("update", name)

    def get_path(self, name):

        return self._parsers[name]["edit-path"]

    def get_names(self):

        return list(self._parsers.keys())

    def get_parser(self, name):

        return self._parsers[name]["parser"]

    def launch(self, name, parser):

        full_path = os.path.join(self._edit_dir, name)

        if not os.path.exists(os.path.dirname(full_path)):

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

        edit_path = os.path.join(f"{full_path}.ini")

        self._parsers[name] = {

            "parser": parser,

            "edit-path": edit_path

            }

        source_path = self._get_copy_source_path(parser)

        if not self._get_files_identical(source_path, edit_path):

            if os.path.exists(edit_path):

                os.remove(edit_path)

            shutil.copy(source_path, edit_path)

        if not edit_path in self._path_inspector.get_paths():

            self._path_inspector.add(edit_path)

        for app in self._external_launch_apps:

            try:

                app.launch([Gio.File.new_for_path(edit_path)], None)

            except:

                pass

            else:

                break

        else:

            subprocess.run(["xdg-open", edit_path], check=True)

    def save(self, name):

        parser = self._parsers[name]["parser"]

        edit_path = self._parsers[name]["edit-path"]

        parser.check_write()

        parser.load(path=edit_path)

        parser.save()

    def exit(self):

        for path in self._path_inspector.get_paths():

            self._path_inspector.remove(path)

        self._path_inspector.set_active(False)

        for name in self._parsers:

            edit_path = self._parsers[name]["edit-path"]

            if os.path.abspath(edit_path).startswith(os.path.abspath(self._edit_dir)):

                os.remove(os.path.join(edit_path))

        else:

            for dirpath, dirnames, filenames in os.walk(self._edit_dir, topdown=False):

                for dirname in dirnames:

                    try:

                        os.rmdir(os.path.join(dirpath, dirname))

                    except OSError as error:

                        self._application.log(error, error=error)

            else:

                if os.path.exists(self._edit_dir) and not len(os.listdir(self._edit_dir)):

                    os.rmdir(self._edit_dir)

    def hook(self, event, callback):

        return self._events.hook(event, callback)

    def release(self, id):

        self._events.release(id)


class DebugLog():

    def __init__(self, app):

        self._application = app

        self._raise_errors = False

        self._messages = []

        self._system_info = []

        self._system_info.append(str(subprocess.getstatusoutput("cat /etc/*-release")[-1]))

        self._system_info.append("")

        self._system_info.append(str(subprocess.getstatusoutput("uname -a")[-1]))

        self._system_info.append("")

        self._system_info.append("XDG_SESSION_DESKTOP={}".format(str(os.getenv("XDG_SESSION_DESKTOP"))))

        self._system_info.append("XDG_CURRENT_DESKTOP={}".format(str(os.getenv("XDG_CURRENT_DESKTOP"))))

        self._system_info.append("XDG_SESSION_TYPE={}".format(str(os.getenv("XDG_SESSION_TYPE"))))

        self._system_info.append("")

        self._system_info.append("LANG={}".format(str(os.getenv("LANG"))))

        self._system_info.append("XDG_DATA_DIRS={}".format(str(os.getenv("XDG_DATA_DIRS"))))

        self._system_info.append("")

        self._system_info.append("APP_RUNNING_AS_FLATPAK={}".format(str(os.getenv("APP_RUNNING_AS_FLATPAK"))))

    def get_raise_errors(self):

        return self._raise_errors

    def set_raise_errors(self, value):

        self._raise_errors = value

    def add(self, text, error=None):

        if not error is None:

            if self._raise_errors:

                raise error

        now = datetime.datetime.now()

        message = "[{}][{}:{}:{}] {}".format(

            self._application.get_app_name(),

            now.strftime("%H"),

            now.strftime("%M"),

            now.strftime("%S"),

            text

            )

        self._messages.append(message)

        sys.stdout.write(f"{message}\n")

    def get(self):

        if len(self._messages):

            return "\n".join(self._messages + [""] + self._system_info)

        else:

            return "\n".join(self._system_info)


class DesktopActionGroup(Adw.PreferencesGroup):

    def __init__(self, app, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._application_window = app.get_application_window()

        self._locale_manager = app.get_locale_manager()

        self._events = basic.EventManager()

        self._events.add("data-changed", object, tuple)

        self._events.add("row-deleted", object)

        self._children = []

        self._delete_mode_enabled  = False

        self._delete_row_placeholder_text = self._locale_manager.get("UNNAMED_ACTION_PLACEHOLDER_TEXT")

        self._entry_row = gui.EntryRow(app)

        self._entry_row.set_title(self._locale_manager.get("ACTION_NAME_ENTRY_ROW_TITLE"))

        self._entry_row.hook("text-changed", self._on_child_row_text_changed)

        self._command_chooser_row = gui.CommandChooserRow(app)

        self._command_chooser_row.set_title(self._locale_manager.get("COMMAND_CHOOSER_ROW_TITLE"))

        self._command_chooser_row.set_dialog_title(self._locale_manager.get("COMMAND_CHOOSER_ROW_DIALOG_TITLE"))

        self._command_chooser_row.set_dialog_accept_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_ACCEPT_BUTTON_LABEL"))

        self._command_chooser_row.set_dialog_cancel_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_CANCEL_BUTTON_LABEL"))

        self._command_chooser_row.hook("text-changed", self._on_child_row_text_changed)

        self._link_converter_row = gui.LinkConverterRow(app)

        self._link_converter_row.set_entry(self._command_chooser_row)

        self._link_converter_row.set_label(self._locale_manager.get("LINK_CONVERTER_ROW_LABEL"))

        self._delete_row = gui.DeleteRow(app)

        self._delete_row.connect("activated", self._on_delete_row_activated)

        self.add(self._entry_row)

        self.add(self._command_chooser_row)

        self.add(self._link_converter_row)

    def _on_delete_row_activated(self, action_row):

        self._events.trigger("row-deleted", self)

    def _on_child_row_text_changed(self, event, child, text):

        data = self._entry_row.get_text(), self._command_chooser_row.get_text()

        self._events.trigger("data-changed", self, data)

    def get_name(self):

        return self._entry_row.get_text()

    def set_name(self, name):

        self._entry_row.set_text(name)

    def get_command(self):

        return self._command_chooser_row.get_text()

    def set_command(self, command):

        self._command_chooser_row.set_text(command)

    def get_delete_mode_enabled(self):

        return self._delete_mode_enabled

    def set_delete_mode_enabled(self, value):

        if value and not self._delete_mode_enabled:

            self.remove(self._entry_row)

            self.remove(self._command_chooser_row)

            self.remove(self._link_converter_row)

            name_text = self._entry_row.get_text()

            if not len(name_text):

                name_text = self._delete_row_placeholder_text

            self._delete_row.set_title(name_text)

            self._delete_row.set_text(self._command_chooser_row.get_text())

            self.add(self._delete_row)

        elif not value and self._delete_mode_enabled:

            self.remove(self._delete_row)

            self.add(self._entry_row)

            self.add(self._command_chooser_row)

            self.add(self._link_converter_row)

        self._delete_mode_enabled = value

    def add(self, child):

        self._children.append(child)

        Adw.PreferencesGroup.add(self, child)

    def remove(self, child):

        self._children.remove(child)

        Adw.PreferencesGroup.remove(self, child)

    def hook(self, event, callback, *args):

        self._events.hook(event, callback, *args)

    def release(self, id):

        self._events.release(id)

    def grab_focus(self):

        if not self._delete_mode_enabled:

            self._entry_row.grab_focus()

        else:

            self._delete_row.grab_focus()

    def reset(self):

        for hook in list(self._events.get_hooks()):

            self._events.release(hook)

        self.set_name("")

        self.set_command("")

        self.set_sensitive(True)

        self.set_delete_mode_enabled(False)

        self.set_header_suffix(None)

        self.set_title("")


class KeywordsFilter():

    def __init__(self, app):

        self._events = basic.EventManager()

        self._events.add("text-changed", object, str)

        self._flow_row = None

        self._flow_row_connection_id = None

        self._current_default_text = ""

        self._delimiter = ";"

    def _on_flow_row_text_changed(self, event, child, text):

        self._events.trigger("text-changed", self, self._get_unfiltered_text(text))

    def _get_unfiltered_text(self, text):

        if not sorted(filter(None, text.split(self._delimiter))) == sorted(filter(None, self._current_default_text.split(self._delimiter))):

            return text

        else:

            return self._current_default_text

    def get_flow_row(self):

        return self._flow_row

    def set_flow_row(self, widget):

        if self._flow_row_connection_id:

            self._flow_row.disconnect(self._flow_row_connection_id)

        self._flow_row = widget

        self._flow_row_connection_id = self._flow_row.hook("text-changed", self._on_flow_row_text_changed)

    def get_text(self):

        return self._get_unfiltered_text(self._flow_row.get_text())

    def set_text(self, text):

        self._current_default_text = text

        self._flow_row.set_text(text)

    def hook(self, event, callback):

        return self._events.hook(event, callback)

    def release(self, id):

        self._events.release(id)

    def reset(self):

        self._current_default_text = ""

        self._flow_row.reset()


class ComboFilter():

    def __init__(self, app):

        self._events = basic.EventManager()

        self._events.add("text-changed", object, str)

        self._locale_manager = app.get_locale_manager()

        self._icon_finder = app.get_icon_finder()

        self._unknown_values_history = set()

        self._show_unknown_values = False

        self._ends_with_delimiter = None

        self._combo_row = None

        self._flow_row = None

        self._combo_row_connection_id = None

        self._flow_row_connection_id = None

        self._current_default_text = ""

        self._delimiter = ";"

        self._options_dict = {}

    def _on_combo_row_item_selected(self, event, name, label):

        self._flow_row.add_tags(label, allow_duplicates=False, warning_timeout=1)

    def _on_flow_row_text_changed(self, event, child, text):

        self._events.trigger("text-changed", self, self._filtered_to_default(text))

    def _join_text(self, strings):

        return self._delimiter.join(strings)

    def _split_text(self, text):

        return list(filter(None, text.split(self._delimiter)))

    def _default_to_filtered(self, text, join_text=True):

        labels = []

        for item in self._split_text(text):

            if item in self._options_dict:

                label = self._options_dict[item]["label"]

                if not label in labels:

                    labels.append(label)

            elif self._show_unknown_values:

                labels.append(item)

        if join_text:

            return self._join_text(labels) + int(bool(self._ends_with_delimiter)) * ";"

        else:

            return labels

    def _filtered_to_default(self, text):

        old_items = self._split_text(self._current_default_text)

        old_labels = self._default_to_filtered(self._current_default_text, join_text=False)

        new_labels = self._split_text(text)

        if sorted(old_labels) == sorted(new_labels):

            return self._current_default_text

        else:

            if not self._show_unknown_values:

                old_unknown_items = [item for item in old_items if not item in self._options_dict]

            else:

                old_unknown_items = []

            new_items = []

            for label in new_labels:

                label_found = False

                for item in self._options_dict:

                    if self._options_dict[item]["label"] == label:

                        new_items.append(item)

                        label_found = True

                else:

                    if not label_found and self._show_unknown_values:

                        new_items.append(label)

            return self._join_text(sorted(new_items + old_unknown_items)) + int(bool(self._ends_with_delimiter)) * ";"

    def _update_combo_row_buttons(self):

        if self._show_unknown_values:

            history = self._unknown_values_history

            current_names = self._split_text(self._current_default_text)

            buttons = self._combo_row.get_buttons()

            for name in current_names:

                if not name in self._options_dict:

                    if not name in history:

                        history.add(name)

            for name in buttons:

                if not name in self._options_dict and not name in history:

                    self._combo_row.remove_button(name, section="unknown")

            for name in history:

                if not name in buttons:

                    self._combo_row.add_button(name, name, self._fallback_icon_name, section="unknown")

    def get_combo_row(self):

        return self._combo_row

    def set_combo_row(self, widget):

        if self._combo_row_connection_id:

            for name in self._combo_row.get_buttons():

                self._combo_row.remove_button(name)

            self._combo_row.disconnect(self._combo_row_connection_id)

        self._combo_row = widget

        added_labels = set()

        for name in self._options_dict:

            label = self._options_dict[name]["label"]

            if not label in added_labels:

                added_labels.add(label)

                self._combo_row.add_button(name, label, self._options_dict[name]["icon-name"])

        self._combo_row_connection_id = self._combo_row.hook("item-selected", self._on_combo_row_item_selected)

        self._update_combo_row_buttons()

    def get_fallback_icon_name(self):

        return self._fallback_icon_name

    def set_fallback_icon_name(self, icon_name):

        self._fallback_icon_name = icon_name

        if self._combo_row:

            self._update_combo_row_buttons()

    def get_default_options(self):

        return self._options_dict

    def add_default_option(self, name, data):

        self._options_dict[name] = data

    def get_show_unknown_values(self):

        return self._show_unknown_values

    def set_show_unknown_values(self, value):

        self._show_unknown_values = value

    def get_flow_row(self):

        return self._flow_row

    def set_flow_row(self, widget):

        if self._flow_row_connection_id:

            self._flow_row.disconnect(self._flow_row_connection_id)

        self._flow_row = widget

        self._flow_row_connection_id = self._flow_row.hook("text-changed", self._on_flow_row_text_changed)

    def get_text(self):

        return self._filtered_to_default(self._flow_row.get_text())

    def set_text(self, text):

        self._current_default_text = text

        self._ends_with_delimiter = text.endswith(self._delimiter)

        self._flow_row.set_text(self._default_to_filtered(text))

        self._update_combo_row_buttons()

    def get_unknown_values_history(self):

        return self._unknown_values_history

    def set_unknown_values_history(self, history):

        self._unknown_values_history = history

    def hook(self, event, callback):

        return self._events.hook(event, callback)

    def release(self, id):

        self._events.release(id)

    def reset(self):

        self._current_default_text = ""

        self._flow_row.reset()

class CategoriesFilter(ComboFilter):

    def __init__(self, app):

        super().__init__(app)

        self._options_dict = {

            "AudioVideo": {

                "label": self._locale_manager.get("MULTIMEDIA_CATEGORY_LABEL"),

                "icon-name": "applications-multimedia"

                },

            "Development": {

                "label": self._locale_manager.get("DEVELOPMENT_CATEGORY_LABEL"),

                "icon-name": "applications-development"

                },

            "Education":  {

                "label": self._locale_manager.get("EDUCATION_CATEGORY_LABEL"),

                "icon-name": "applications-education"

                },

            "Game": {

                "label": self._locale_manager.get("GAME_CATEGORY_LABEL"),

                "icon-name": "applications-games"

                },

            "Graphics": {

                "label": self._locale_manager.get("GRAPHICS_CATEGORY_LABEL"),

                "icon-name": "applications-graphics"

                },

            "Network": {

                "label": self._locale_manager.get("NETWORK_CATEGORY_LABEL"),

                "icon-name": "applications-network"

                },

            "Office": {

                "label": self._locale_manager.get("OFFICE_CATEGORY_LABEL"),

                "icon-name": "applications-office"

                },

            "Science": {

                "label": self._locale_manager.get("SCIENCE_CATEGORY_LABEL"),

                "icon-name": "applications-science"

                },

            "Settings": {

                "label": self._locale_manager.get("SETTINGS_CATEGORY_LABEL"),

                "icon-name": "applications-settings"

                },

            "System": {

                "label": self._locale_manager.get("SYSTEM_CATEGORY_LABEL"),

                "icon-name": "applications-system"

                },

            "Utility": {

                "label": self._locale_manager.get("UTILITY_CATEGORY_LABEL"),

                "icon-name": "applications-utilities"

                }

            }


class ShowInFilter(ComboFilter):

    def __init__(self, app):

        super().__init__(app)

        self.set_show_unknown_values(True)

        self.set_fallback_icon_name("desktop-environment-nologo")

        for name in ["Budgie"]:

            self.add_default_option(name, {

                "label": "Budgie",

                "icon-name": "desktop-environment-budgie"

                })

        for name in ["X-Cinnamon"]:

            self.add_default_option(name, {

                "label": "Cinnamon",

                "icon-name": "desktop-environment-cinnamon"

                })

        for name in ["COSMIC"]:

            self.add_default_option(name, {

                "label": "COSMIC",

                "icon-name": "desktop-environment-cosmic"

                })

        for name in ["DDE"]:

            self.add_default_option(name, {

                "label": "Deepin",

                "icon-name": "desktop-environment-deepin"

                })

        for name in ["Endless"]:

            self.add_default_option(name, {

                "label": "Endless",

                "icon-name": "desktop-environment-endless"

                })

        for name in ["GNOME"]:

            self.add_default_option(name, {

                "label": "GNOME",

                "icon-name": "desktop-environment-gnome"

                })

        for name in ["KDE"]:

            self.add_default_option(name, {

                "label": "KDE",

                "icon-name": "desktop-environment-kde"

                })

        for name in ["LXDE"]:

            self.add_default_option(name, {

                "label": "LXDE",

                "icon-name": "desktop-environment-lxde"

                })

        for name in ["LXQt"]:

            self.add_default_option(name, {

                "label": "LXQt",

                "icon-name": "desktop-environment-lxqt"

                })

        for name in ["MATE"]:

            self.add_default_option(name, {

                "label": "MATE",

                "icon-name": "desktop-environment-mate"

                })

        for name in ["Pantheon"]:

            self.add_default_option(name, {

                "label": "Pantheon",

                "icon-name": "desktop-environment-pantheon"

                })

        for name in ["TDE"]:

            self.add_default_option(name, {

                "label": "Trinity",

                "icon-name": "desktop-environment-tde"

                })

        for name in ["Unity"]:

            self.add_default_option(name, {

                "label": "Unity",

                "icon-name": "desktop-environment-unity"

                })

        for name in ["XFCE"]:

            self.add_default_option(name, {

                "label": "XFCE",

                "icon-name": "desktop-environment-xfce"

                })


class SettingsPage(Gtk.Box):

    def __init__(self, app, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._events = basic.EventManager()

        self._events.add("changed-changed", bool, bool)

        self._locale_manager = app.get_locale_manager()

        self._icon_finder = app.get_icon_finder()

        self._application = app

        self._clamp_limit = 1200

        self._clamp_threshold = 240

        self._reload_button_fade_duration = 45

        self._reload_button_fade_timeout_id = None

        self._loading_desktop_starter = False

        self._changed = False

        self._current_name = None

        self._current_parser = None

        self._delete_mode_enabled = False

        self._always_show_save_button = False

        self._desktop_action_groups_cache = []

        self._current_desktop_actions = []

        self._current_desktop_action_groups = {}

        self._input_children_changes = {}

        self._show_in_filter_histories = {}

        ###############################################################################################################

        self._save_button = Gtk.Button()

        self._reload_button = Gtk.Button()

        ###############################################################################################################

        if hasattr(Adw, "Banner"):

            self._banner_event_controller_key = Gtk.EventControllerKey()

            self._banner_event_controller_key.connect("key-pressed", self._on_banner_event_controller_key_pressed)

            self._banner = Adw.Banner()

            self._banner.set_title(self._locale_manager.get("BANNER_LABEL_TEXT"))

            self._banner.set_button_label(self._locale_manager.get("BANNER_CANCEL_BUTTON_LABEL"))

            self._banner.connect("button-clicked", self._on_banner_button_clicked)

            self._banner.add_controller(self._banner_event_controller_key)

            self.append(self._banner)

        ###############################################################################################################

        self._icon_chooser_row = gui.IconChooserRow(app)

        self._icon_chooser_row.set_default_entry_title(self._locale_manager.get("ICON_CHOOSER_ROW_TITLE"))

        self._icon_chooser_row.set_search_entry_title(self._locale_manager.get("ICON_CHOOSER_ROW_SEARCH_MODE_TITLE"))

        self._icon_chooser_row.set_dialog_title(self._locale_manager.get("ICON_CHOOSER_ROW_DIALOG_TITLE"))

        self._icon_chooser_row.set_dialog_accept_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_ACCEPT_BUTTON_LABEL"))

        self._icon_chooser_row.set_dialog_cancel_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_CANCEL_BUTTON_LABEL"))

        self._icon_chooser_row.hook("text-changed", self._on_input_child_data_changed)

        ###############################################################################################################

        self._icon_browser_row = self._icon_chooser_row.get_icon_browser_row()

        self._icon_browser_row.set_margin_top(1)

        self._icon_view_row = self._icon_chooser_row.get_icon_view_row()

        ###############################################################################################################

        self._icon_browser_help_status_page = self._icon_chooser_row.get_help_status_page()

        self._icon_browser_help_status_page.add_css_class("compact")

        self._icon_browser_help_status_page.set_title(self._locale_manager.get("ICON_CHOOSER_ROW_STATUS_PAGE_HELP_HEAD"))

        self._icon_browser_help_status_page.set_description(self._locale_manager.get("ICON_CHOOSER_ROW_STATUS_PAGE_HELP_BODY"))

        ###############################################################################################################

        self._icon_browser_none_status_page = self._icon_chooser_row.get_none_status_page()

        self._icon_browser_none_status_page.add_css_class("compact")

        self._icon_browser_none_status_page.set_title(self._locale_manager.get("ICON_CHOOSER_ROW_STATUS_PAGE_NONE_HEAD"))

        self._icon_browser_none_status_page.set_description(self._locale_manager.get("ICON_CHOOSER_ROW_STATUS_PAGE_NONE_BODY"))

        ###############################################################################################################

        self._appearance_preferences_group = Adw.PreferencesGroup()

        self._appearance_preferences_group.set_title(self._locale_manager.get("APPEARANCE_GROUP_TITLE"))

        self._appearance_preferences_group.add(self._icon_view_row)

        self._appearance_preferences_group.add(self._icon_chooser_row)

        self._appearance_preferences_group.add(self._icon_browser_row)

        ###############################################################################################################

        self._name_entry_row = gui.EntryRow(app)

        self._name_entry_row.set_title(self._locale_manager.get("NAME_ENTRY_ROW_TITLE"))

        self._name_entry_row.hook("text-changed", self._on_input_child_data_changed)

        self._comment_entry_row = gui.EntryRow(app)

        self._comment_entry_row.set_title(self._locale_manager.get("COMMENT_ENTRY_ROW_TITLE"))

        self._comment_entry_row.hook("text-changed", self._on_input_child_data_changed)

        self._description_preferences_group = Adw.PreferencesGroup()

        self._description_preferences_group.set_title(self._locale_manager.get("DESCRIPTION_GROUP_TITLE"))

        self._description_preferences_group.add(self._name_entry_row)

        self._description_preferences_group.add(self._comment_entry_row)

        ###############################################################################################################

        self._keywords_entry_row = gui.EntryRow(app)

        self._keywords_entry_row.set_placeholder_image(self._icon_finder.get_name("list-add-symbolic"))

        self._keywords_entry_row.set_title(self._locale_manager.get("KEYWORDS_ENTRY_ROW_TITLE"))

        self._keywords_flow_row = gui.TaggedFlowRow(app)

        self._keywords_flow_row.hook("text-changed", self._on_input_child_data_changed)

        self._keywords_flow_row.set_entry_row(self._keywords_entry_row)

        self._keywords_filter = KeywordsFilter(app)

        self._keywords_filter.set_flow_row(self._keywords_flow_row)

        self._keywords_filter.hook("text-changed", self._on_input_child_data_changed)

        self._keywords_preferences_group = Adw.PreferencesGroup()

        self._keywords_preferences_group.set_title(self._locale_manager.get("DISCOVERY_GROUP_TITLE"))

        self._keywords_preferences_group.add(self._keywords_entry_row)

        self._keywords_preferences_group.add(self._keywords_flow_row)

        ###############################################################################################################

        self._command_chooser_row = gui.CommandChooserRow(self._application)

        self._command_chooser_row.set_title(self._locale_manager.get("COMMAND_CHOOSER_ROW_DEFAULT_TITLE"))

        self._command_chooser_row.set_dialog_title(self._locale_manager.get("COMMAND_CHOOSER_ROW_DIALOG_TITLE"))

        self._command_chooser_row.set_dialog_accept_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_ACCEPT_BUTTON_LABEL"))

        self._command_chooser_row.set_dialog_cancel_button_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_CANCEL_BUTTON_LABEL"))

        self._command_chooser_row.hook("text-changed", self._on_input_child_data_changed)

        self._link_converter_row = gui.LinkConverterRow(self._application)

        self._link_converter_row.set_entry(self._command_chooser_row)

        self._link_converter_row.set_label(self._locale_manager.get("LINK_CONVERTER_ROW_LABEL"))

        ###############################################################################################################

        self._primary_event_controller_key = Gtk.EventControllerKey()

        self._primary_action_create_button = Gtk.Button()

        self._primary_action_create_button.set_icon_name(self._icon_finder.get_name("list-add-symbolic"))

        self._primary_action_create_button.add_css_class("flat")

        self._primary_action_create_button.connect("clicked", self._on_action_create_button_clicked)

        self._primary_action_delete_button = Gtk.Button()

        self._primary_action_delete_button.set_icon_name(self._icon_finder.get_name("list-remove-symbolic"))

        self._primary_action_delete_button.add_css_class("flat")

        self._primary_action_delete_button.connect("clicked", self._on_action_delete_button_clicked)

        self._primary_header_suffix_box = Gtk.Box()

        self._primary_header_suffix_box.set_spacing(gui.Spacing.DEFAULT)

        self._primary_header_suffix_box.append(self._primary_action_create_button)

        self._primary_header_suffix_box.append(self._primary_action_delete_button)

        self._primary_header_suffix_box.add_controller(self._primary_event_controller_key)

        ###############################################################################################################

        self._execution_preferences_group = Adw.PreferencesGroup()

        self._execution_preferences_group.set_title(self._locale_manager.get("EXECUTION_GROUP_TITLE"))

        self._execution_preferences_group.add(self._command_chooser_row)

        self._execution_preferences_group.add(self._link_converter_row)

        self._execution_preferences_group.set_header_suffix(self._primary_header_suffix_box)

        ###############################################################################################################

        self._categories_flow_row = gui.TaggedFlowRow(app)

        self._categories_combo_row = gui.ComboRow(app)

        self._categories_combo_row.set_title(self._locale_manager.get("CATEGORIES_COMBO_ROW_TITLE"))

        self._categories_combo_row.set_flow_row(self._categories_flow_row)

        self._categories_filter = CategoriesFilter(app)

        self._categories_filter.set_flow_row(self._categories_flow_row)

        self._categories_filter.set_combo_row(self._categories_combo_row)

        self._categories_filter.hook("text-changed", self._on_input_child_data_changed)

        self._categories_preferences_group = Adw.PreferencesGroup()

        self._categories_preferences_group.set_title(self._locale_manager.get("MENU_GROUP_TITLE"))

        self._categories_preferences_group.add(self._categories_combo_row)

        self._categories_preferences_group.add(self._categories_flow_row)

        ###############################################################################################################

        self._terminal_switch_row = gui.SwitchRow()

        self._terminal_switch_row.set_title(self._locale_manager.get("TERMINAL_SWITCH_ROW_TITLE"))

        self._terminal_switch_row.hook("value-changed", self._on_input_child_data_changed)

        self._notify_switch_row = gui.SwitchRow()

        self._notify_switch_row.set_title(self._locale_manager.get("NOTIFY_SWITCH_ROW_TITLE"))

        self._notify_switch_row.hook("value-changed", self._on_input_child_data_changed)

        self._window_preferences_group = Adw.PreferencesGroup()

        self._window_preferences_group.set_title(self._locale_manager.get("WINDOW_GROUP_TITLE"))

        self._window_preferences_group.add(self._terminal_switch_row)

        self._window_preferences_group.add(self._notify_switch_row)

        ###############################################################################################################

        self._visible_switch_row = gui.SwitchRow()

        self._visible_switch_row.set_title(self._locale_manager.get("VISIBLE_SWITCH_ROW_TITLE"))

        self._visible_switch_row.hook("value-changed", self._on_input_child_data_changed)

        self._visible_switch_row.hook("value-changed", self._on_visibility_widgets_changed)

        self._only_show_in_flow_row = gui.TaggedFlowRow(app)

        self._only_show_in_combo_row = gui.ComboRow(app)

        self._only_show_in_combo_row.set_title(self._locale_manager.get("ONLYSHOWIN_COMBO_ROW_TITLE"))

        self._only_show_in_combo_row.set_flow_row(self._only_show_in_flow_row)

        self._only_show_in_filter = ShowInFilter(app)

        self._only_show_in_filter.set_flow_row(self._only_show_in_flow_row)

        self._only_show_in_filter.set_combo_row(self._only_show_in_combo_row)

        self._only_show_in_filter.hook("text-changed", self._on_input_child_data_changed)

        self._only_show_in_filter.hook("text-changed", self._on_visibility_widgets_changed)

        self._not_show_in_flow_row = gui.TaggedFlowRow(app)

        self._not_show_in_combo_row = gui.ComboRow(app)

        self._not_show_in_combo_row.set_title(self._locale_manager.get("NOTSHOWIN_COMBO_ROW_TITLE"))

        self._not_show_in_combo_row.set_flow_row(self._not_show_in_flow_row)

        self._not_show_in_filter = ShowInFilter(app)

        self._not_show_in_filter.set_flow_row(self._not_show_in_flow_row)

        self._not_show_in_filter.set_combo_row(self._not_show_in_combo_row)

        self._not_show_in_filter.hook("text-changed", self._on_input_child_data_changed)

        self._not_show_in_filter.hook("text-changed", self._on_visibility_widgets_changed)

        ###############################################################################################################

        self._visible_preferences_group = Adw.PreferencesGroup()

        self._visible_preferences_group.set_title(self._locale_manager.get("VISIBLE_GROUP_TITLE"))

        self._visible_preferences_group.add(self._visible_switch_row)

        self._visible_preferences_group.add(self._only_show_in_combo_row)

        self._visible_preferences_group.add(self._only_show_in_flow_row)

        self._visible_preferences_group.add(self._not_show_in_combo_row)

        self._visible_preferences_group.add(self._not_show_in_flow_row)

        ###############################################################################################################

        self._edit_file_action_row_image = self._icon_finder.get_image("adw-external-link-symbolic")

        self._edit_file_action_row_button = Gtk.Button()

        self._edit_file_action_row_button.add_css_class("flat")

        self._edit_file_action_row_button.set_valign(Gtk.Align.CENTER)

        self._edit_file_action_row_button.set_child(self._edit_file_action_row_image)

        self._edit_file_action_row_button.set_can_focus(False)

        self._edit_file_action_row_button.set_can_target(False)

        self._edit_file_action_row = Adw.ActionRow()

        self._edit_file_action_row.set_activatable(True)

        self._edit_file_action_row.set_title(self._locale_manager.get("EDIT_FILE_ACTION_ROW_TITLE"))

        self._edit_file_action_row.add_suffix(self._edit_file_action_row_button)

        self._advanced_preferences_group = Adw.PreferencesGroup()

        self._advanced_preferences_group.set_title(self._locale_manager.get("ADVANCED_GROUP_TITLE"))

        self._advanced_preferences_group.add(self._edit_file_action_row)

        ###############################################################################################################

        self._page_event_controller_key = Gtk.EventControllerKey()

        self._page_event_controller_key.connect("key-pressed", self._on_page_controller_key_pressed)

        ###############################################################################################################

        self._top_box = Gtk.Box()

        self._top_box.set_spacing(gui.Spacing.LARGER)

        self._top_box.set_orientation(Gtk.Orientation.VERTICAL)

        self._top_box.append(self._appearance_preferences_group)

        self._top_box.append(self._description_preferences_group)

        self._top_box.append(self._execution_preferences_group)

        self._action_box = Gtk.Box()

        self._action_box.set_spacing(gui.Spacing.LARGER)

        self._action_box.set_orientation(Gtk.Orientation.VERTICAL)

        self._bottom_box = Gtk.Box()

        self._bottom_box.set_spacing(gui.Spacing.LARGER)

        self._bottom_box.set_orientation(Gtk.Orientation.VERTICAL)

        self._bottom_box.append(self._keywords_preferences_group)

        self._bottom_box.append(self._window_preferences_group)

        self._bottom_box.append(self._visible_preferences_group)

        self._bottom_box.append(self._categories_preferences_group)

        self._bottom_box.append(self._advanced_preferences_group)

        self._main_box = Gtk.Box()

        self._main_box.set_spacing(gui.Spacing.LARGER)

        self._main_box.set_orientation(Gtk.Orientation.VERTICAL)

        self._main_box.append(self._top_box)

        self._main_box.append(self._action_box)

        self._main_box.append(self._bottom_box)

        self._clamp = Adw.Clamp(maximum_size=self._clamp_limit, tightening_threshold=self._clamp_threshold)

        self._clamp.set_margin_top(gui.Margin.LARGER)

        self._clamp.set_margin_bottom(gui.Margin.LARGER)

        self._clamp.set_margin_start(gui.Margin.LARGER)

        self._clamp.set_margin_end(gui.Margin.LARGER)

        self._clamp.set_child(self._main_box)

        self._scrolled_window = Gtk.ScrolledWindow()

        self._scrolled_window.set_child(self._clamp)

        self._scrolled_window.set_vexpand(True)

        ###############################################################################################################

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.append(self._scrolled_window)

        ###############################################################################################################

        self._update_action_children_sensitive(False)

        self._update_top_desktop_action_group_header()

    def _on_visibility_widgets_changed(self, event, child, data):

        self._update_visibility_widgets()

    def _on_page_controller_key_pressed(self, controller, keyval, keycode, state):

        if keyval == gui.Keyval.ESCAPE:

            if self._delete_mode_enabled:

                self.set_delete_mode_enabled(False)

                return True

    def _on_banner_button_clicked(self, banner):

        self.set_delete_mode_enabled(False)

    def _on_action_create_button_clicked(self, button):

        while True:

            action = ''.join(random.choices(string.digits, k=6))

            if not action in self._current_desktop_actions:

                self._add_desktop_action(action, set_focus=True)

                break

    def _on_action_delete_button_clicked(self, button):

        self.set_delete_mode_enabled(True)

    def _on_banner_event_controller_key_pressed(self, controller, keyval, keycode, state):

        if keyval == gui.Keyval.DOWN or keyval == gui.Keyval.PAGEDOWN:

            self._current_desktop_action_groups[self._current_desktop_actions[0]].grab_focus()

            return True

        elif keyval == gui.Keyval.ESCAPE:

            self.set_delete_mode_enabled(False)

    def _on_desktop_action_group_row_deleted(self, event, desktop_action_group):

        index = list(self._current_desktop_action_groups.values()).index(desktop_action_group)

        action = self._current_desktop_actions[index]

        self._remove_desktop_action(action, set_focus=True)

    def _on_input_child_data_changed(self, event, child, data):

        if not isinstance(child, DesktopActionGroup):

            if child == self._icon_chooser_row:

                self._input_children_changes[child] = data == self._current_parser.get_icon()

            elif child == self._name_entry_row:

                self._input_children_changes[child] = data == self._current_parser.get_name()

            elif child == self._comment_entry_row:

                self._input_children_changes[child] = data == self._current_parser.get_comment()

            elif child == self._keywords_filter:

                self._input_children_changes[child] = data == self._current_parser.get_keywords()

            elif child == self._categories_filter:

                self._input_children_changes[child] = data == self._current_parser.get_categories()

            elif child == self._only_show_in_filter:

                self._input_children_changes[child] = data == self._current_parser.get_only_show_in()

            elif child == self._not_show_in_filter:

                self._input_children_changes[child] = data == self._current_parser.get_not_show_in()

            elif child == self._command_chooser_row:

                self._input_children_changes[child] = data == self._current_parser.get_command()

            elif child == self._visible_switch_row:

                self._input_children_changes[child] = data == self._current_parser.get_visible()

            elif child == self._notify_switch_row:

                self._input_children_changes[child] = data == self._current_parser.get_notify()

            elif child == self._terminal_switch_row:

                self._input_children_changes[child] = data == self._current_parser.get_terminal()

        self._update_action_children_sensitive()

    def _get_input_children_changed(self):

        if False in self._input_children_changes.values():

            value = True

        else:

            value = self._get_desktop_action_groups_changed()

        if not value == self._changed:

            self._events.trigger("changed-changed", self._changed, bool(value))

        self._changed = bool(value)

        return value

    def _get_desktop_action_groups_changed(self):

        try:

            parser_actions = self._current_parser.get_actions()

        except AttributeError:

            return False

        if not self._current_desktop_actions == parser_actions:

            parser_actions_count = len(parser_actions)

            if len(self._current_desktop_actions) > parser_actions_count:

                for n, current_action in enumerate(self._current_desktop_actions[:parser_actions_count]):

                    current_name = self._current_desktop_action_groups[current_action].get_name()

                    parser_name = self._current_parser.get_action_name(parser_actions[n])

                    if not current_name == parser_name:

                        return True

                    current_command = self._current_desktop_action_groups[current_action].get_command()

                    parser_command = self._current_parser.get_action_command(parser_actions[n])

                    if not current_command == parser_command:

                        return True

                else:

                    for action in self._current_desktop_actions[parser_actions_count:]:

                        desktop_action_group = self._current_desktop_action_groups[action]

                        if len(desktop_action_group.get_name()) or len(desktop_action_group.get_command()):

                            return True

            else:

                return True

        else:

            for action in self._current_desktop_actions:

                name = self._current_desktop_action_groups[action].get_name()

                if not name == self._current_parser.get_action_name(action):

                    return True

                command = self._current_desktop_action_groups[action].get_command()

                if not command == self._current_parser.get_action_command(action):

                    return True

    def _create_new_desktop_action_group(self):

        try:

            desktop_action_group = self._desktop_action_groups_cache.pop(0)

        except IndexError:

            desktop_action_group = DesktopActionGroup(self._application)

        finally:

            desktop_action_group.hook("row-deleted", self._on_desktop_action_group_row_deleted)

            desktop_action_group.hook("data-changed", self._on_input_child_data_changed)

            return desktop_action_group

    def _add_desktop_action(self, action, set_focus=False):

        desktop_action_group = self._create_new_desktop_action_group()

        if action in self._current_parser.get_actions():

            desktop_action_group.set_name(self._current_parser.get_action_name(action))

            desktop_action_group.set_command(self._current_parser.get_action_command(action))

        self._current_desktop_action_groups[action] = desktop_action_group

        self._current_desktop_actions.append(action)

        self._action_box.append(desktop_action_group)

        if set_focus:

            GLib.idle_add(desktop_action_group.grab_focus)

        self._update_top_desktop_action_group_header()

        self._update_action_children_sensitive()

    def _remove_desktop_action(self, action, set_focus=False):

        index = self._current_desktop_actions.index(action)

        desktop_action_group = self._current_desktop_action_groups[action]

        del self._current_desktop_action_groups[action]

        self._current_desktop_actions.remove(action)

        if not len(self._current_desktop_actions):

            self.set_delete_mode_enabled(False)

        if set_focus:

            if not len(self._current_desktop_actions):

                self._primary_action_create_button.grab_focus()

            elif index < len(self._current_desktop_actions):

                self._current_desktop_action_groups[self._current_desktop_actions[index]].grab_focus()

            else:

                self._current_desktop_action_groups[self._current_desktop_actions[-1]].grab_focus()

        self._action_box.remove(desktop_action_group)

        desktop_action_group.reset()

        self._desktop_action_groups_cache.append(desktop_action_group)

        self._update_top_desktop_action_group_header()

        self._update_action_children_sensitive()

    def _update_visibility_widgets(self):

        rows_sensitive = self._visible_switch_row.get_active()

        self._only_show_in_combo_row.set_sensitive(rows_sensitive)

        self._only_show_in_flow_row.set_sensitive(rows_sensitive)

        self._not_show_in_combo_row.set_sensitive(rows_sensitive)

        self._not_show_in_flow_row.set_sensitive(rows_sensitive)

        if len(self._only_show_in_flow_row.get_tags()):

            self._not_show_in_combo_row.set_sensitive(False)

            self._not_show_in_flow_row.set_sensitive(False)

        elif len(self._not_show_in_flow_row.get_tags()):

            self._only_show_in_combo_row.set_sensitive(False)

    def _update_top_desktop_action_group_header(self):

        self._primary_action_delete_button.set_sensitive(len(self._current_desktop_action_groups))

        self._action_box.set_visible(len(self._current_desktop_action_groups))

    def _update_input_children_sensitive(self, value=True):

        self._action_box.set_sensitive(value)

        if self._delete_mode_enabled:

            value = False

        self._primary_header_suffix_box.set_sensitive(value)

        self._top_box.set_sensitive(value)

        self._bottom_box.set_sensitive(value)

    def _update_action_children_sensitive(self, value=True, skip_reload_button=False):

        input_children_changed = self._get_input_children_changed()

        if not self._loading_desktop_starter:

            if value and not input_children_changed:

                value = False

            if value or self._always_show_save_button:

                self._save_button.set_sensitive(True)

                self._save_button.add_css_class("suggested-action")

            else:

                self._save_button.set_sensitive(False)

                self._save_button.remove_css_class("suggested-action")

            if not skip_reload_button:

                if self._reload_button_fade_timeout_id:

                    GLib.source_remove(self._reload_button_fade_timeout_id)

                if value:

                    self._reload_button.set_visible(True)

                    self._reload_button_fade_timeout_id = GLib.timeout_add(self._reload_button_fade_duration, self._after_reload_button_show)

                else:

                    self._reload_button.set_sensitive(False)

                    self._reload_button_fade_timeout_id = GLib.timeout_add(self._reload_button_fade_duration, self._after_reload_button_hide)

    def _after_reload_button_show(self):

        self._reload_button.set_sensitive(True)

        self._reload_button_fade_timeout_id = None

        return GLib.SOURCE_REMOVE

    def _after_reload_button_hide(self):

        self._reload_button.set_visible(False)

        self._reload_button_fade_timeout_id = None

        return GLib.SOURCE_REMOVE

    def get_delete_mode_enabled(self):

        return self._delete_mode_enabled

    def set_delete_mode_enabled(self, value):

        if not value == self._delete_mode_enabled:

            self._delete_mode_enabled = value

            if hasattr(self, "_banner"):

                self._banner.set_revealed(value)

            for action in self._current_desktop_actions:

                desktop_action_group = self._current_desktop_action_groups[action]

                desktop_action_group.set_delete_mode_enabled(value)

            self._update_input_children_sensitive()

            if value:

                self._current_desktop_action_groups[self._current_desktop_actions[0]].grab_focus()

    def load_desktop_starter(self, name, parser):

        self._loading_desktop_starter = True

        self.reset(reset_data=False)

        self._current_name = name

        self._current_parser = parser

        for action in list(self._current_desktop_actions):

            self._remove_desktop_action(action)

        for action in self._current_parser.get_actions():

            self._add_desktop_action(action)

        if not self._current_name in self._show_in_filter_histories:

            self._show_in_filter_histories[self._current_name] = set()

        history = self._show_in_filter_histories[self._current_name]

        self._only_show_in_filter.set_unknown_values_history(history)

        self._not_show_in_filter.set_unknown_values_history(history)

        self._icon_chooser_row.set_text(self._current_parser.get_icon())

        self._name_entry_row.set_text(self._current_parser.get_name())

        self._comment_entry_row.set_text(self._current_parser.get_comment())

        self._keywords_filter.set_text(self._current_parser.get_keywords())

        self._categories_filter.set_text(self._current_parser.get_categories())

        self._only_show_in_filter.set_text(self._current_parser.get_only_show_in())

        self._not_show_in_filter.set_text(self._current_parser.get_not_show_in())

        self._command_chooser_row.set_text(self._current_parser.get_command())

        self._visible_switch_row.set_active(self._current_parser.get_visible())

        self._notify_switch_row.set_active(self._current_parser.get_notify())

        self._terminal_switch_row.set_active(self._current_parser.get_terminal())

        self._loading_desktop_starter = False

        self._update_action_children_sensitive(False)

        self._update_visibility_widgets()

    def save_desktop_starter(self):

        for action in self._current_parser.get_actions():

            if not action in self._current_desktop_actions:

                self._current_parser.remove_action(action)

        for action in list(self._current_desktop_actions):

            desktop_action_group = self._current_desktop_action_groups[action]

            if not len(desktop_action_group.get_name()) and not len(desktop_action_group.get_command()):

                if action in self._current_parser.get_actions():

                    self._current_parser.remove_action(action)

                self._remove_desktop_action(action)

            else:

                if not action in self._current_parser.get_actions():

                    self._current_parser.add_action(action)

                self._current_parser.set_action_name(action, desktop_action_group.get_name())

                self._current_parser.set_action_command(action, desktop_action_group.get_command())

        self._current_parser.set_icon(self._icon_chooser_row.get_text())

        self._current_parser.set_name(self._name_entry_row.get_text())

        self._current_parser.set_comment(self._comment_entry_row.get_text())

        self._current_parser.set_keywords(self._keywords_filter.get_text())

        self._current_parser.set_categories(self._categories_filter.get_text())

        self._current_parser.set_only_show_in(self._only_show_in_filter.get_text())

        self._current_parser.set_not_show_in(self._not_show_in_filter.get_text())

        self._current_parser.set_command(self._command_chooser_row.get_text())

        self._current_parser.set_visible(self._visible_switch_row.get_active())

        self._current_parser.set_notify(self._notify_switch_row.get_active())

        self._current_parser.set_terminal(self._terminal_switch_row.get_active())

        self._current_parser.save()

        self.reset(reset_data=False)

    def get_always_show_save_button(self):

        return self._always_show_save_button

    def set_always_show_save_button(self, value):

        self._always_show_save_button = value

        self._update_action_children_sensitive(skip_reload_button=True)

    def get_edit_file_action_row(self):

        return self._edit_file_action_row

    def get_save_button(self):

        return self._save_button

    def get_reload_button(self):

        return self._reload_button

    def get_changed(self):

        return self._changed

    def reset(self, reset_data=True):

        if reset_data:

            for action in list(self._current_desktop_actions):

                self._remove_desktop_action(action)

            self._name_entry_row.set_text("")

            self._comment_entry_row.set_text("")

            self._command_chooser_row.set_text("")

            self._visible_switch_row.set_active(False)

            self._notify_switch_row.set_active(False)

            self._terminal_switch_row.set_active(False)

            self._keywords_filter.reset()

            self._categories_filter.reset()

            self._only_show_in_filter.reset()

            self._not_show_in_filter.reset()

            self._icon_chooser_row.reset()

        self._icon_chooser_row.set_search_mode(False)

        self._keywords_entry_row.set_text("")

        self._update_action_children_sensitive(False)

        self._input_children_changes.clear()

        self.set_delete_mode_enabled(False)

        self._changed = False

    def hook(self, event, callback):

        return self._events.hook(event, callback)

    def release(self, id):

        self._events.release(id)

    def grab_focus(self):

        if self._delete_mode_enabled:

            self._current_desktop_action_groups[self._current_desktop_actions[0]].grab_focus()

        elif not self.get_focus_child():

            self._icon_view_row.grab_focus()


class StarterAlreadyExistingError(Exception):

    pass


class StarterNotFoundError(Exception):

    pass


class Application(gui.Application):

    def __init__(self, *args, **kwargs):

        ###############################################################################################################

        self._debug_log = DebugLog(self)

        if len(args) and "--debug" in sys.argv:

            self._debug_log.set_raise_errors(True)

            sys.stdout.write(self._debug_log.get())

            sys.argv.remove("--debug")

        ###############################################################################################################

        super().__init__(*args, **kwargs)

        self._application_window.install_action("toast.details", None, self._on_toast_details_button_clicked)

        self._current_desktop_starter_name = None

        self._desktop_starter_parsers = {}

        self._unsaved_custom_starters = {}

        self._ignore_show_hidden_switch_changes = False

        self._previous_discard_dialog = None

        ###############################################################################################################

        self._back_button_fade_timeout_id = None

        self._back_button_fade_duration = 45

        ###############################################################################################################

        xdg_current_desktop = os.getenv("XDG_CURRENT_DESKTOP")

        if isinstance(xdg_current_desktop, str):

            self._xdg_current_desktop_values = set(filter(None, xdg_current_desktop.split(":")))

        else:

            self._xdg_current_desktop_values = set()

        ###############################################################################################################

        ignore_prefix = "page.codeberg.libre_menu_editor.LibreMenuEditor.fallback."

        self._icon_finder.set_ignore_prefix(ignore_prefix)

        self._icon_finder.add_alternatives(

            "system-search-symbolic",

            "search-symbolic",

            "edit-find-symbolic",

            f"{ignore_prefix}system-search-symbolic"

            )

        self._icon_finder.add_alternatives(

            "document-open-symbolic",

            f"{ignore_prefix}document-open-symbolic"

            )

        self._icon_finder.add_alternatives(

            "action-unavailable-symbolic",

            f"{ignore_prefix}action-unavailable-symbolic"

            )

        self._icon_finder.add_alternatives(

            "open-menu-symbolic",

            "application-menu-symbolic",

            f"{ignore_prefix}open-menu-symbolic"

            )

        self._icon_finder.add_alternatives(

            "list-add-symbolic",

            "add-symbolic",

            f"{ignore_prefix}list-add-symbolic"

            )

        self._icon_finder.add_alternatives(

            "list-remove-symbolic",

            "remove-symbolic",

            f"{ignore_prefix}list-remove-symbolic"

            )

        self._icon_finder.add_alternatives(

            "view-refresh-symbolic",

            f"{ignore_prefix}view-refresh-symbolic"

            )

        self._icon_finder.add_alternatives(

            "dialog-warning-symbolic",

            f"{ignore_prefix}dialog-warning-symbolic"

            )

        self._icon_finder.add_alternatives(

            "edit-find-replace-symbolic",

            f"{ignore_prefix}edit-find-replace-symbolic"

            )

        self._icon_finder.add_alternatives(

            "system-run-symbolic",

            f"{ignore_prefix}system-run-symbolic"

            )

        self._icon_finder.add_alternatives(

            "window-close-symbolic",

            f"{ignore_prefix}window-close-symbolic"

            )

        self._icon_finder.add_alternatives(

            "page.codeberg.libre_menu_editor.LibreMenuEditor",

            f"{ignore_prefix}libre-menu-editor"

            )

        self._icon_finder.add_alternatives(

            "applications-multimedia",

            f"{ignore_prefix}applications-multimedia"

            )

        self._icon_finder.add_alternatives(

            "applications-development",

            f"{ignore_prefix}applications-development"

            )

        self._icon_finder.add_alternatives(

            "applications-education",

            f"{ignore_prefix}applications-education"

            )

        self._icon_finder.add_alternatives(

            "applications-games",

            f"{ignore_prefix}applications-games"

            )

        self._icon_finder.add_alternatives(

            "applications-graphics",

            f"{ignore_prefix}applications-graphics"

            )

        self._icon_finder.add_alternatives(

            "applications-network",

            "applications-internet",

            f"{ignore_prefix}applications-network"

            )

        self._icon_finder.add_alternatives(

            "applications-office",

            f"{ignore_prefix}applications-office"

            )

        self._icon_finder.add_alternatives(

            "applications-science",

            f"{ignore_prefix}applications-science"

            )

        self._icon_finder.add_alternatives(

            "applications-settings",

            "preferences-system",

            f"{ignore_prefix}applications-settings"

            )

        self._icon_finder.add_alternatives(

            "applications-system",

            f"{ignore_prefix}applications-system"

            )

        self._icon_finder.add_alternatives(

            "applications-utilities",

            "applications-accessories",

            f"{ignore_prefix}applications-utilities"

            )

        ###############################################################################################################

        self._desktop_starter_custom_create_name = "custom-desktop-starter"

        self._desktop_starter_template_path = os.path.join(self.get_project_dir(), "default.desktop")

        self._desktop_starter_override_dir = os.path.join(GLib.get_user_data_dir(), "applications")

        ###############################################################################################################

        if os.getenv("APP_RUNNING_AS_FLATPAK") == "true":

            subprocess.Popen([

                "flatpak-spawn", "--host", "touch",

                os.path.join(self.get_flatpak_real_home(), ".config", "mimeapps.list")

                ])

        ###############################################################################################################

        self._start_page = Adw.StatusPage()

        self._start_page.set_title(self._locale_manager.get("START_PAGE_HEAD"))

        self._start_page.set_description(self._locale_manager.get("START_PAGE_BODY"))

        self._start_page.set_icon_name(self._icon_finder.get_name("edit-find-replace-symbolic"))

        ###############################################################################################################

        self._settings_page = SettingsPage(self)

        self._settings_page.hook("changed-changed", self._on_settings_page_changed_changed)

        self._settings_page.get_edit_file_action_row().connect("activated", self._on_edit_file_button_clicked)

        ###############################################################################################################

        self._search_list = gui.SearchList(self)

        self._search_list.hook("item-activated", self._on_search_list_item_activated)

        ###############################################################################################################

        self._save_settings_button = self._settings_page.get_save_button()

        self._save_settings_button.set_label(self._locale_manager.get("SAVE_SETTINGS_BUTTON_LABEL"))

        self._save_settings_button.set_focus_on_click(False)

        self._save_settings_button.connect("clicked", self._on_save_settings_button_clicked)

        self._reload_settings_button = self._settings_page.get_reload_button()

        self._reload_settings_button.add_css_class("flat")

        self._reload_settings_button.set_icon_name(self._icon_finder.get_name("view-refresh-symbolic"))

        self._reload_settings_button.set_focus_on_click(False)

        self._reload_settings_button.connect("clicked", self._on_reload_settings_button_clicked)

        self._search_button = self._search_list.get_search_button()

        ###############################################################################################################

        self._view_menu_section = gui.Menu(self)

        self._view_menu_section.add_switch("show_hidden", self._locale_manager.get("SHOW_HIDDEN_SWITCH_LABEL"))

        self._view_menu_section.set_switch_state("show_hidden", self._config_manager.get("show.hidden"))

        self._view_menu_section.hook("show_hidden", self._on_show_hidden_switch_changed)

        ###############################################################################################################

        self._add_menu_section = gui.Menu(self)

        self._add_menu_section.add_button("new_starter", self._locale_manager.get("NEW_STARTER_MENU_BUTTON_LABEL"))

        self._add_menu_section.hook("new_starter", self._on_new_starter_button_clicked)

        self._add_menu_section.add_button("open_file", self._locale_manager.get("OPEN_FILE_MENU_BUTTON_LABEL"))

        self._add_menu_section.hook("open_file", self._on_open_file_button_clicked)

        ###############################################################################################################

        self._reset_starter_menu_section = gui.Menu(self)

        self._delete_starter_menu_section = gui.Menu(self)

        self._discard_starter_menu_section = gui.Menu(self)

        self._reset_starter_menu_section.add_button("reset_starter", self._locale_manager.get("RESET_STARTER_MENU_BUTTON_LABEL"))

        self._reset_starter_menu_section.hook("reset_starter", self._on_reset_starter_button_clicked)

        self._delete_starter_menu_section.add_button("delete_starter", self._locale_manager.get("DELETE_STARTER_MENU_BUTTON_LABEL"))

        self._delete_starter_menu_section.hook("delete_starter", self._on_delete_starter_button_clicked)

        self._discard_starter_menu_section.add_button("discard_starter", self._locale_manager.get("DISCARD_STARTER_MENU_BUTTON_LABEL"))

        self._discard_starter_menu_section.hook("discard_starter", self._on_discard_starter_button_clicked)

        ###############################################################################################################

        self._help_menu_section = gui.Menu(self)

        self._help_menu_section.add_button("show_shortcuts", self._locale_manager.get("SHOW_SHORTCUTS_MENU_BUTTON_LABEL"))

        self._help_menu_section.hook("show_shortcuts", self._on_show_shortcuts_button_clicked)

        self._help_menu_section.add_button("show_about", self._locale_manager.get("SHOW_ABOUT_MENU_BUTTON_LABEL"))

        self._help_menu_section.hook("show_about", self._on_show_about_button_clicked)

        ###############################################################################################################

        for name in ["greeter", "big_start", "small_start", "big_reset_starter", "small_reset_starter", "big_delete_starter", "small_delete_starter", "big_discard_starter", "small_discard_starter"]:

            setattr(self, f"_{name}_menu", gui.Menu(self))

        ###############################################################################################################

        for name in ["big_start", "small_start", "big_reset_starter", "big_delete_starter", "big_discard_starter"]:

            getattr(self, f"_{name}_menu").append_section(None, self._view_menu_section)

        ###############################################################################################################

        for name in ["big_reset_starter", "small_reset_starter", "big_start"]:

            getattr(self, f"_{name}_menu").append_section(None, self._reset_starter_menu_section)

        for name in ["big_delete_starter", "small_delete_starter"]:

            getattr(self, f"_{name}_menu").append_section(None, self._delete_starter_menu_section)

        for name in ["big_discard_starter", "small_discard_starter"]:

            getattr(self, f"_{name}_menu").append_section(None, self._discard_starter_menu_section)

        ###############################################################################################################

        for name in ["big_start", "small_start", "big_reset_starter", "small_reset_starter", "big_delete_starter", "small_delete_starter", "big_discard_starter", "small_discard_starter"]:

            getattr(self, f"_{name}_menu").append_section(None, self._add_menu_section)

        ###############################################################################################################

        for name in ["greeter", "big_start", "small_start", "big_reset_starter", "small_reset_starter", "big_delete_starter", "small_delete_starter", "big_discard_starter", "small_discard_starter"]:

            getattr(self, f"_{name}_menu").append_section(None, self._help_menu_section)

        ###############################################################################################################

        self._left_menu_button = Gtk.MenuButton()

        self._left_menu_button.set_icon_name(self._icon_finder.get_name("open-menu-symbolic"))

        self._right_menu_button = Gtk.MenuButton()

        self._right_menu_button.set_icon_name(self._icon_finder.get_name("open-menu-symbolic"))

        ###############################################################################################################

        self._greeter_menu_button = Gtk.MenuButton()

        self._greeter_menu_button.set_icon_name(self._icon_finder.get_name("open-menu-symbolic"))

        self._greeter_menu_button.set_menu_model(self._greeter_menu)

        self._greeter_menu_button.set_primary(True)

        self._greeter_button = Gtk.Button()

        self._greeter_button.add_css_class("pill")

        self._greeter_button.add_css_class("suggested-action")

        self._greeter_button.connect("clicked", self._on_greeter_button_clicked)

        self._greeter_button.set_label(self._locale_manager.get("GREETER_PAGE_BUTTON_LABEL"))

        self._greeter_button.set_hexpand(False)

        self._greeter_button_clamp = Adw.Clamp()

        self._greeter_button_clamp.set_maximum_size(0)

        self._greeter_button_clamp.set_child(self._greeter_button)

        self._greeter_status_page = Adw.StatusPage()

        self._greeter_status_page.set_title(self._locale_manager.get("GREETER_PAGE_HEAD"))

        self._greeter_status_page.set_description(self._locale_manager.get("GREETER_PAGE_BODY"))

        self._greeter_status_page.set_icon_name(self._icon_finder.get_name("dialog-warning-symbolic"))

        self._greeter_status_page.set_child(self._greeter_button_clamp)

        self._greeter_status_page.set_hexpand(True)

        self._greeter_header_bar_label = Gtk.Label()

        self._greeter_top_header_bar = Gtk.HeaderBar()

        self._greeter_top_header_bar.set_show_title_buttons(True)

        self._greeter_top_header_bar.add_css_class("flat")

        self._greeter_top_header_bar.set_title_widget(self._greeter_header_bar_label)

        self._greeter_top_header_bar.pack_end(self._greeter_menu_button)

        self._greeter_window_handle = Gtk.WindowHandle()

        self._greeter_window_handle.set_child(self._greeter_status_page)

        self._greeter_window_handle.set_vexpand(True)

        self._greeter_window_handle.set_margin_bottom(self._greeter_top_header_bar.get_preferred_size()[1].height)

        self._greeter_page = Gtk.Box()

        self._greeter_page.set_orientation(Gtk.Orientation.VERTICAL)

        self._greeter_page.append(self._greeter_top_header_bar)

        self._greeter_page.append(self._greeter_window_handle)

        ###############################################################################################################

        self._left_event_controller_key = Gtk.EventControllerKey()

        self._left_event_controller_key.connect("key-pressed", self._on_left_event_controller_key_pressed)

        self._left_header_bar_label = Gtk.Label()

        self._left_header_bar = Adw.HeaderBar()

        self._left_header_bar.set_title_widget(self._left_header_bar_label)

        self._left_header_bar.add_controller(self._left_event_controller_key)

        self._left_header_bar.pack_start(self._search_button)

        self._left_header_bar.pack_end(self._left_menu_button)

        self._right_event_controller_key = Gtk.EventControllerKey()

        self._right_event_controller_key.connect("key-pressed", self._on_right_event_controller_key_pressed)

        self._right_header_bar_label = Gtk.Label()

        self._right_header_bar = Adw.HeaderBar()

        self._right_header_bar.set_title_widget(self._right_header_bar_label)

        self._right_header_bar.add_controller(self._right_event_controller_key)

        self._right_header_bar.pack_end(self._right_menu_button)

        ###############################################################################################################

        self._header_bar_size_group = Gtk.SizeGroup()

        self._header_bar_size_group.add_widget(self._left_header_bar)

        self._header_bar_size_group.add_widget(self._right_header_bar)

        self._header_bar_size_group.set_mode(Gtk.SizeGroupMode.VERTICAL)

        ###############################################################################################################

        self._start_page.set_margin_bottom(self._right_header_bar.get_preferred_size()[1].height)

        ###############################################################################################################

        self._main_stack = Gtk.Stack()

        self._main_stack.add_child(self._start_page)

        self._main_stack.add_child(self._settings_page)

        ###############################################################################################################

        if hasattr(Adw, "NavigationSplitView") and hasattr(Adw, "ToolbarView"):

            self._search_bar = self._search_list.get_search_bar()

            self._search_bar.unparent()

            toolbar_view_top_box = Gtk.Box()

            toolbar_view_top_box.set_orientation(Gtk.Orientation.VERTICAL)

            toolbar_view_top_box.append(self._left_header_bar)

            toolbar_view_top_box.append(self._search_bar)

            self._left_area_box = Adw.ToolbarView()

            self._left_area_box.set_size_request(180, 200)

            self._left_area_box.add_top_bar(toolbar_view_top_box)

            self._left_area_box.set_content(self._search_list)

            self._right_area_box = Adw.ToolbarView()

            self._right_area_box.set_size_request(300, 200)

            self._right_area_box.add_top_bar(self._right_header_bar)

            self._right_area_box.set_content(self._main_stack)

            self._split_view_sidebar = Adw.NavigationPage()

            self._split_view_sidebar.set_child(self._left_area_box)

            self._split_view_content = Adw.NavigationPage()

            self._split_view_content.set_child(self._right_area_box)

            self._main_split_layout = Adw.NavigationSplitView()

            self._main_split_layout.set_sidebar_width_fraction(1 / 4)

            self._main_split_layout.set_min_sidebar_width(self._left_area_box.get_property("width-request") * 9 / 8)

            self._main_split_layout.set_max_sidebar_width(self._left_area_box.get_property("width-request") * 5 / 3)

            self._main_split_layout.set_sidebar(self._split_view_sidebar)

            self._main_split_layout.set_content(self._split_view_content)

            self._main_split_layout.connect("notify::collapsed", self._on_main_split_layout_collapsed_changed)

            window_breakpoint_limit = self._left_area_box.get_property("width-request") + self._right_area_box.get_property("width-request") * 4 / 3

            self._window_breakpoint = Adw.Breakpoint()

            self._window_breakpoint.add_setter(self._main_split_layout, "collapsed", True)

            self._window_breakpoint.set_condition(Adw.BreakpointCondition.parse(f"max-width: {window_breakpoint_limit}sp"))

            self._application_window.add_breakpoint(self._window_breakpoint)

            self._application_window.set_size_request(*self._right_area_box.get_size_request())

        else:

            self._left_header_bar.set_show_start_title_buttons(False)

            self._left_header_bar.set_show_end_title_buttons(False)

            self._right_header_bar.set_show_start_title_buttons(False)

            self._right_header_bar.set_show_end_title_buttons(True)

            self._left_area_box = Gtk.Box()

            self._left_area_box.set_size_request(240, 200)

            self._left_area_box.set_orientation(Gtk.Orientation.VERTICAL)

            self._left_area_box.append(self._left_header_bar)

            self._left_area_box.append(self._search_list)

            self._left_area_box.set_hexpand(False)

            self._right_area_box = Gtk.Box()

            self._right_area_box.set_size_request(300, 200)

            self._right_area_box.set_orientation(Gtk.Orientation.VERTICAL)

            self._right_area_box.append(self._right_header_bar)

            self._right_area_box.append(self._main_stack)

            self._main_separator = Gtk.Separator()

            self._main_split_layout = Gtk.Box()

            self._main_split_layout.append(self._left_area_box)

            self._main_split_layout.append(self._main_separator)

            self._main_split_layout.append(self._right_area_box)

        ###############################################################################################################

        self._main_stack.connect("notify::visible-child", self._on_main_stack_visible_child_changed)

        ###############################################################################################################

        self._greeter_stack = Gtk.Stack()

        self._greeter_stack.add_child(self._greeter_page)

        self._greeter_stack.add_child(self._main_split_layout)

        self._toast_overlay = Adw.ToastOverlay()

        self._toast_overlay.set_vexpand(True)

        self._toast_overlay.set_child(self._greeter_stack)

        ###############################################################################################################

        self._about_window = Adw.AboutWindow()

        self._about_window.set_application_icon(

            self._icon_finder.get_name("page.codeberg.libre_menu_editor.LibreMenuEditor")

            )

        self._about_window.set_application_name(self._locale_manager.get("APPLICATION_NAME"))

        self._about_window.set_developer_name("libre-menu-editor")

        self._about_window.set_issue_url("https://codeberg.org/libre-menu-editor/libre-menu-editor/issues")

        self._about_window.set_copyright("© 2022 Free Software Foundation")

        self._about_window.set_license_type(Gtk.License.GPL_3_0)

        self._about_window.set_hide_on_close(True)

        self._about_window.set_transient_for(self._application_window)

        self._about_window.set_modal(True)

        ###############################################################################################################

        self._application_window_event_controller_key = Gtk.EventControllerKey()

        self._application_window_event_controller_key.connect("key-pressed", self._on_application_window_event_controller_key_pressed)

        self._application_window.set_icon_name(self._icon_finder.get_name("page.codeberg.libre_menu_editor.LibreMenuEditor"))

        self._application_window.set_title(self._locale_manager.get("APPLICATION_NAME"))

        self._application_window.add_controller(self._application_window_event_controller_key)

        self._application_window.connect("map", self._on_application_window_map)

        self._application_window.connect("close-request", self._on_application_window_close_request)

        self._application_window.set_content(self._toast_overlay)

        ###############################################################################################################

        self._text_editor = DefaultTextEditor(self)

        self._text_editor.hook("update", self._on_text_editor_update)

        ###############################################################################################################

        self._open_dialog_file_filter = Gtk.FileFilter()

        self._open_dialog_file_filter.add_mime_type("application/x-desktop")

        if not os.getenv("APP_RUNNING_AS_FLATPAK") == "true" or os.getenv("USE_NATIVE_DIALOGS") == "true":

            self._open_file_chooser_dialog = Gtk.FileChooserNative(select_multiple=True, filter=self._open_dialog_file_filter)

        else:

            self._open_dialog_accept_button = Gtk.Button()

            self._open_dialog_accept_button.add_css_class("suggested-action")

            self._open_dialog_accept_button.set_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_ACCEPT_BUTTON_LABEL"))

            self._open_dialog_cancel_button = Gtk.Button()

            self._open_dialog_cancel_button.set_label(self._locale_manager.get("PATH_CHOOSER_DIALOG_CANCEL_BUTTON_LABEL"))

            self._open_file_chooser_dialog = Gtk.FileChooserDialog(select_multiple=True, filter=self._open_dialog_file_filter)

            self._open_file_chooser_dialog.add_action_widget(self._open_dialog_accept_button, Gtk.ResponseType.ACCEPT)

            self._open_file_chooser_dialog.add_action_widget(self._open_dialog_cancel_button, Gtk.ResponseType.CANCEL)

            self._open_file_chooser_dialog.set_default_response(Gtk.ResponseType.ACCEPT)

            try:

                self._open_file_chooser_dialog.connect("show", self._on_open_file_chooser_dialog_show)

                self._open_file_chooser_dialog.connect("close-request", self._on_open_file_chooser_dialog_close_request)

            except TypeError:

                pass

        self._open_file_chooser_dialog.set_title(self._locale_manager.get("OPEN_FILE_CHOOSER_DIALOG_TITLE"))

        self._open_file_chooser_dialog.connect("response", self._on_open_file_chooser_dialog_response)

        self._open_file_chooser_dialog.set_transient_for(self._application_window)

        self._open_file_chooser_dialog.set_modal(True)

        ###############################################################################################################

        self._process_manager = basic.ProcessManager(

            os.path.join(self._config_dir, "lock"),

            os.path.join(self._config_dir, "argv")

            )

        self._process_manager.hook("activate", self._on_process_manager_activate)

        ###############################################################################################################

        self._application_window_drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)

        self._application_window_drop_target.set_gtypes([Gdk.FileList])

        self._application_window_drop_target.connect("drop", self._on_application_window_drop_target_drop)

        self._application_window.add_controller(self._application_window_drop_target)

        ###############################################################################################################

        self.connect("shutdown", self._on_application_shutdown)

        self._update_menu_button()

        self._load_desktop_starter_dirs()

    def _on_application_window_drop_target_drop(self, drop_target, value, x, y):

        self._load_external_starters(*[file.get_path() for file in value.get_files()])

    def _on_process_manager_activate(self, event, args):

        GLib.idle_add(self._after_process_manager_activate, args)

    def _after_process_manager_activate(self, args):

        if len(args):

            self._parse_command_line_args(args)

        self._application_window.present()

    def _on_text_editor_update(self, event, name):

        if name == self._current_desktop_starter_name:

            self._check_unsaved_data(self._after_text_editor_update, name)

        else:

            self._after_text_editor_update(name)

    def _after_text_editor_update(self, name):

        try:

            self._text_editor.save(name)

            parser = self._text_editor.get_parser(name)

            if not name in self._unsaved_custom_starters or not self._unsaved_custom_starters[name]["external"]:

                self._update_mime_data(parser)

        except Exception as error:

            self.log(error, error=error)

            self.notify(self._locale_manager.get("STARTER_SAVE_ERROR_TEXT"), error=error)

        else:

            text = parser.get_name()

            if not len(text):

                text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

            self.notify(self._locale_manager.get("STARTER_SAVE_MESSAGE_TEXT") % text)

            if name in self._unsaved_custom_starters and not self._unsaved_custom_starters[name]["external"]:

                del self._unsaved_custom_starters[name]

            if name in self._desktop_starter_parsers:

                parser = self._desktop_starter_parsers[name]

                self._update_search_list_item(name)

                if name == self._current_desktop_starter_name:

                    self._load_settings_page(name)

    def _on_application_shutdown(self, app):

        self._process_manager.set_active(False)

    def _on_application_window_close_request(self, window):

        if self._settings_page.get_changed():

            self._check_unsaved_data(GLib.idle_add, self._application_window.destroy)

            return True

    def _on_application_window_map(self, window):

        if self._config_manager.get("greeter.confirmed"):

            self._greeter_stack.set_visible_child(self._main_split_layout)

            self._process_manager.set_active(True)

        else:

            self._greeter_button.grab_focus()

    def _on_application_window_event_controller_key_pressed(self, window, keyval, keycode, state):

        control_modifier_pressed = state == state | Gdk.ModifierType.CONTROL_MASK

        if not hasattr(self, "_split_view_content") or not self._main_split_layout.get_collapsed() or not self._main_split_layout.get_show_content():

            if (control_modifier_pressed and keyval == 102 and # F

                not self._greeter_stack.get_visible_child() == self._greeter_page):

                if (self._search_list.get_search_mode() and (

                    not len(self._search_list.get_search_entry().get_text())

                    or not self._search_list.get_search_entry().get_focus_child() == None)):

                    self._search_list.set_search_mode(False)

                else:

                    self._search_list.grab_focus()

                return True

        ###############################################################################################################

            elif (control_modifier_pressed and keyval == 104 and # H

                not self._greeter_stack.get_visible_child() == self._greeter_page):

                state = self._view_menu_section.get_switch_state("show_hidden")

                self._view_menu_section.set_switch_state("show_hidden", state == False)

                return True

        ###############################################################################################################

        if (control_modifier_pressed and keyval == 110 and # N

            not self._greeter_stack.get_visible_child() == self._greeter_page and

            self._add_menu_section.get_enabled("new_starter")):

            self._on_new_starter_button_clicked(None)

            return True

        elif (control_modifier_pressed and keyval == 111 and # O

            not self._greeter_stack.get_visible_child() == self._greeter_page):

            self._on_open_file_button_clicked(None)

            return True

        ###############################################################################################################

        if not hasattr(self, "_split_view_content") or not self._main_split_layout.get_collapsed() or self._main_split_layout.get_show_content():

            if (control_modifier_pressed and keyval == 115 and # S

                self._main_stack.get_visible_child() == self._settings_page and

                self._save_settings_button.get_sensitive() and self._save_settings_button.get_visible()):

                self._on_save_settings_button_clicked(None)

                return True

            elif (control_modifier_pressed and keyval == 114 and # R

                self._main_stack.get_visible_child() == self._settings_page and

                self._reload_settings_button.get_sensitive() and self._reload_settings_button.get_visible()):

                self._on_reload_settings_button_clicked(None)

                return True

            elif (control_modifier_pressed and keyval == 101 and # E

                self._main_stack.get_visible_child() == self._settings_page):

                self._on_edit_file_button_clicked(None)

            elif (control_modifier_pressed and keyval == 100 and # D

                self._main_stack.get_visible_child() == self._settings_page):

                if (self._current_menu_button.get_menu_model() == self._current_reset_starter_menu and

                    self._reset_starter_menu_section.get_enabled("reset_starter")):

                    self._on_reset_starter_button_clicked(None)

                elif (self._current_menu_button.get_menu_model() == self._current_delete_starter_menu and

                    self._delete_starter_menu_section.get_enabled("delete_starter")):

                    self._on_delete_starter_button_clicked(None)

                elif (self._current_menu_button.get_menu_model() == self._current_discard_starter_menu and

                    self._discard_starter_menu_section.get_enabled("discard_starter")):

                    self._on_discard_starter_button_clicked(None)

                return True

        ###############################################################################################################

        if control_modifier_pressed and keyval == 223: # ?

            self._on_show_shortcuts_button_clicked(None)

        elif control_modifier_pressed and keyval == 113: # Q

            self._application_window.close()

        elif control_modifier_pressed and keyval == 119: # W

            self._application_window.close()

    def _on_toast_details_button_clicked(self, widget, action_name, parameter):

        self._on_show_about_button_clicked(None)

    def _on_open_file_chooser_dialog_show(self, dialog):

        self._open_file_chooser_dialog.set_current_folder(Gio.File.new_for_path(GLib.get_home_dir()))

    def _on_open_file_chooser_dialog_close_request(self, dialog):

        self._open_file_chooser_dialog.hide()

        return True

    def _on_open_file_chooser_dialog_response(self, dialog, response):

        self._open_file_chooser_dialog.hide()

        if response == Gtk.ResponseType.ACCEPT:

            paths = [file.get_path() for file in self._open_file_chooser_dialog.get_files()]

            self._load_external_starters(*paths, skip_discard_dialog=True)

    def _on_install_dialog_response(self, message_dialog, response):

        if response == "save":

            self._save_settings_page(skip_dialog=True)

        elif response == "install":

            self._unsaved_custom_starters[self._current_desktop_starter_name]["external"] = False

            message_dialog.callback(*message_dialog.callback_args, **message_dialog.callback_kwargs)

            if self._save_settings_page(skip_dialog=True):

                self._unsaved_custom_starters[self._current_desktop_starter_name]["external"] = True

    def _on_discard_dialog_response(self, message_dialog, response):

        if response == "save":

            if not self._save_settings_page():

                message_dialog.callback(*message_dialog.callback_args, **message_dialog.callback_kwargs)

        elif response == "discard":

            message_dialog.callback(*message_dialog.callback_args, **message_dialog.callback_kwargs)

        else:

            self._update_search_list_selection()

    def _on_reset_dialog_response(self, message_dialog, response):

        if response == "continue":

            message_dialog.callback(*message_dialog.callback_args, **message_dialog.callback_kwargs)

    def _on_delete_dialog_response(self, message_dialog, response):

        if response == "continue":

            message_dialog.callback(*message_dialog.callback_args, **message_dialog.callback_kwargs)

    def _on_greeter_button_clicked(self, button):

        self._config_manager.set("greeter.confirmed", True)

        self._greeter_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)

        self._greeter_stack.set_visible_child(self._main_split_layout)

        self._process_manager.set_active(True)

    def _on_main_split_layout_collapsed_changed(self, widget, gparam):

        self._update_menu_button()

    def _on_settings_page_changed_changed(self, event, previous_value, current_value):

        if hasattr(self, "_split_view_content"):

            if self._back_button_fade_timeout_id:

                GLib.source_remove(self._back_button_fade_timeout_id)

                self._back_button_fade_timeout_id = None

            if current_value:

                self._split_view_content.set_can_pop(False)

            else:

                self._back_button_fade_timeout_id = GLib.timeout_add(self._back_button_fade_duration, self._after_settings_page_changed_changed)

    def _after_settings_page_changed_changed(self):

        if hasattr(self, "_split_view_content"):

            self._split_view_content.set_can_pop(True)

            self._back_button_fade_timeout_id = None

            return GLib.SOURCE_REMOVE

    def _on_main_stack_visible_child_changed(self, stack, gparam):

        if not self._main_stack.get_visible_child() == self._settings_page:

            if hasattr(self._main_split_layout, "set_show_content"):

                self._main_split_layout.set_show_content(False)

            self._current_desktop_starter_name = None

            if not self._save_settings_button.get_parent() == None:

                self._save_settings_button.unparent()

            if not self._reload_settings_button.get_parent() == None:

                self._reload_settings_button.unparent()

            if self._settings_page.get_changed():

                self._settings_page.reset(reset_data=False)

        else:

            if self._reload_settings_button.get_parent() == None:

                self._right_header_bar.pack_start(self._reload_settings_button)

            if self._save_settings_button.get_parent() == None:

                self._right_header_bar.pack_end(self._save_settings_button)

        self._update_menu_button_menu_model()

    def _on_left_event_controller_key_pressed(self, controller, keyval, keycode, state):

        if keyval == gui.Keyval.DOWN or keyval == gui.Keyval.PAGEDOWN:

            self._search_list.grab_focus()

            return True

    def _on_right_event_controller_key_pressed(self, controller, keyval, keycode, state):

        if keyval == gui.Keyval.DOWN or keyval == gui.Keyval.PAGEDOWN:

            self._main_stack.get_visible_child().grab_focus()

            return True

    def _on_show_hidden_switch_changed(self, name):

        if not self._ignore_show_hidden_switch_changes:

            state = self._view_menu_section.get_switch_state(name)

            if not self._config_manager.get("show.hidden") == state:

                if self._current_desktop_starter_name:

                    parser = self._desktop_starter_parsers[self._current_desktop_starter_name]

                    if not state and parser.get_hidden():

                        self._set_show_hidden_switch_state_without_triggering(state == False)

                        self._check_unsaved_data(self._after_show_hidden_switch_changed, state)

                    else:

                        self._after_show_hidden_switch_changed(state)

                else:

                    self._after_show_hidden_switch_changed(state)

    def _after_show_hidden_switch_changed(self, state):

        self._set_show_hidden_switch_state_without_triggering(state)

        self._config_manager.set("show.hidden", state)

        self._reload_search_list_items()

    def _on_reset_starter_button_clicked(self, event):

        self._show_reset_dialog(self._reset_desktop_starter, self._current_desktop_starter_name)

    def _on_delete_starter_button_clicked(self, event):

        self._show_delete_dialog(self._delete_desktop_starter, self._current_desktop_starter_name)

    def _on_discard_starter_button_clicked(self, event):

        if self._settings_page.get_changed():

            self._show_discard_dialog(self._remove_desktop_starter, self._current_desktop_starter_name, notify_user=True)

        else:

            self._remove_desktop_starter(self._current_desktop_starter_name, notify_user=True)

    def _on_edit_file_button_clicked(self, event):

        if self._settings_page.get_changed():

            self._check_unsaved_data(self._after_edit_file_button_clicked)

        else:

            self._edit_desktop_starter(self._current_desktop_starter_name)

    def _after_edit_file_button_clicked(self):

        name = self._current_desktop_starter_name

        self._load_settings_page(name)

        self._edit_desktop_starter(name)

    def _on_open_file_button_clicked(self, event):

        self._check_unsaved_data(self._after_open_file_button_clicked)

    def _after_open_file_button_clicked(self):

        if self._current_desktop_starter_name:

            self._load_settings_page(self._current_desktop_starter_name)

        self._open_file_chooser_dialog.show()

    def _on_show_shortcuts_button_clicked(self, event):

        self._show_shortcuts_dialog()

    def _on_show_about_button_clicked(self, event):

        self._about_window.set_debug_info(self._debug_log.get())

        self._about_window.set_visible(True)

    def _on_new_starter_button_clicked(self, button):

        if (not self._current_desktop_starter_name in self._unsaved_custom_starters or

            self._unsaved_custom_starters[self._current_desktop_starter_name]["external"]):

            self._check_unsaved_data(self._create_desktop_starter)

        else:

            self._create_desktop_starter()

    def _on_save_settings_button_clicked(self, button):

        self._save_settings_page()

    def _on_reload_settings_button_clicked(self, button):

        self._load_settings_page(self._current_desktop_starter_name)

    def _on_search_list_item_activated(self, event, name):

        self._check_unsaved_data(self._load_settings_page, name, ignore_name=name)

        return True

    def _get_desktop_starter_has_default(self, name):

        return os.path.exists(self._get_desktop_starter_default_path(name, include_host=True))

    def _get_desktop_starter_has_override(self, name):

        return os.path.exists(self._get_desktop_starter_override_path(name))

    def _get_desktop_starter_default_path(self, name, include_host=False):

        for directory in self._system_data_dirs:

            path = os.path.join(directory, "applications", "%s.desktop" % name)

            if os.getenv("APP_RUNNING_AS_FLATPAK") == "true" and include_host:

                path = self.get_flatpak_sandbox_system_path(path)

            if os.path.exists(path):

                return path

        else:

            return os.path.join(self._system_data_dirs[0], "applications", "%s.desktop" % name)

    def _get_desktop_starter_override_path(self, name, include_host=False):

        path = os.path.join(self._desktop_starter_override_dir, "%s.desktop" % name)

        if os.getenv("APP_RUNNING_AS_FLATPAK") == "true" and include_host:

            path = self.get_flatpak_sandbox_system_path(path)

        return path

    def _get_desktop_starter_names(self):

        directories = []

        for directory in self._system_data_dirs:

            directories.append(os.path.join(directory, "applications"))

        else:

            directories.append(self._desktop_starter_override_dir)

        names = []

        for directory in directories:

            if os.path.exists(directory):

                for dirpath, dirnames, filenames in os.walk(directory):

                    for filename in filenames:

                        if filename.endswith(".desktop"):

                            full_path = os.path.join(dirpath, filename)

                            relative_path = os.path.relpath(full_path, directory)

                            name = relative_path[:-len(".desktop")].strip(os.path.sep)

                            if not name in names:

                                names.append(name)

        else:

            return names

    def _set_show_hidden_switch_state_without_triggering(self, state):

        self._ignore_show_hidden_switch_changes = True

        self._view_menu_section.set_switch_state("show_hidden", state)

        self._ignore_show_hidden_switch_changes = False

    def _load_desktop_starter_dirs(self):

        for name in reversed(sorted(self._get_desktop_starter_names())):

            try:

                self._add_desktop_starter(name)

            except Exception as error:

                self.log(error, error=error)

    def _focus_settings_page(self):

        if hasattr(self._main_split_layout, "set_show_content"):

            self._main_split_layout.set_show_content(True)

    def _check_unsaved_data(self, *callback_args, **callback_kwargs):

        if "ignore_name" in callback_kwargs:

            ignore_name = callback_kwargs.pop("ignore_name")

        else:

            ignore_name = None

        if (ignore_name and not ignore_name == self._current_desktop_starter_name) or not ignore_name:

            if self._settings_page.get_changed():

                if self._previous_discard_dialog and self._previous_discard_dialog.get_visible():

                    self._previous_discard_dialog.destroy()

                self._previous_discard_dialog = self._show_discard_dialog(*callback_args, **callback_kwargs)

                return True

            else:

                if len(callback_args) > 1:

                    callback_args[0](*callback_args[1:], **callback_kwargs)

                else:

                    callback_args[0](**callback_kwargs)

        else:

            self._focus_settings_page()

    def _show_shortcuts_dialog(self):

        builder = Gtk.Builder.new_from_string("""

            <?xml version="1.0" encoding="UTF-8"?>

            <interface><object class="GtkShortcutsWindow" id="shortcuts-window">
            <property name="modal">1</property>

                <child><object class="GtkShortcutsSection">
                <property name="max-height">12</property>

                    <child><object class="GtkShortcutsGroup">
                    <property name="title">{}</property>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                    </object></child>

                    <child><object class="GtkShortcutsGroup">
                    <property name="title">{}</property>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                    </object></child>

                    <child><object class="GtkShortcutsGroup">
                    <property name="title">{}</property>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                        <child><object class="GtkShortcutsShortcut">
                        <property name="accelerator">{}</property>
                        <property name="title">{}</property>
                        </object></child>

                    </object></child>

                </object></child>

            </object></interface>

            """.format(

                self._locale_manager.get("FIND_SHORTCUT_GROUP_TITLE"),

                "&lt;ctrl&gt;f", self._locale_manager.get("TOGGLE_SEARCH_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;h", self._locale_manager.get("SHOW_HIDDEN_SHORTCUT_TEXT"),

                self._locale_manager.get("GENERAL_SHORTCUT_GROUP_TITLE"),

                "&lt;ctrl&gt;q", self._locale_manager.get("QUIT_APPLICATION_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;question", self._locale_manager.get("SHOW_SHORTCUTS_SHORTCUT_TEXT"),

                "F10", self._locale_manager.get("SHOW_MENU_SHORTCUT_TEXT"),

                self._locale_manager.get("EDIT_SHORTCUT_GROUP_TITLE"),

                "&lt;ctrl&gt;s", self._locale_manager.get("SAVE_SETTINGS_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;r", self._locale_manager.get("RELOAD_SETTINGS_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;d", self._locale_manager.get("REVERT_CHANGES_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;n", self._locale_manager.get("NEW_STARTER_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;o", self._locale_manager.get("OPEN_FILE_SHORTCUT_TEXT"),

                "&lt;ctrl&gt;e", self._locale_manager.get("EDIT_FILE_SHORTCUT_TEXT")

            ), -1)

        window = builder.get_object("shortcuts-window")

        window.set_transient_for(self._application_window)

        window.set_modal(True)

        window.set_hide_on_close(False)

        window.set_visible(True)

    def _show_install_dialog(self, callback, *callback_args, **callback_kwargs):

        install_dialog = Adw.MessageDialog.new(

            self._application_window,

            self._locale_manager.get("INSTALL_DIALOG_HEAD"),

            self._locale_manager.get("INSTALL_DIALOG_BODY")

            )

        install_dialog.add_response(

            "back", self._locale_manager.get("INSTALL_DIALOG_BACK_BUTTON_LABEL")

            )

        install_dialog.add_response(

            "save", self._locale_manager.get("INSTALL_DIALOG_SAVE_BUTTON_LABEL")

            )

        install_dialog.add_response(

            "install", self._locale_manager.get("INSTALL_DIALOG_INSTALL_BUTTON_LABEL")

            )

        install_dialog.callback = callback

        install_dialog.callback_args = callback_args

        install_dialog.callback_kwargs = callback_kwargs

        install_dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)

        install_dialog.connect("response", self._on_install_dialog_response)

        install_dialog.show()

    def _show_discard_dialog(self, callback, *callback_args, **callback_kwargs):

        discard_dialog = Adw.MessageDialog.new(

            self._application_window,

            self._locale_manager.get("DISCARD_DIALOG_HEAD"),

            self._locale_manager.get("DISCARD_DIALOG_BODY")

            )

        discard_dialog.add_response(

            "back", self._locale_manager.get("DISCARD_DIALOG_BACK_BUTTON_LABEL")

            )

        discard_dialog.add_response(

            "save", self._locale_manager.get("DISCARD_DIALOG_SAVE_BUTTON_LABEL")

            )

        discard_dialog.add_response(

            "discard", self._locale_manager.get("DISCARD_DIALOG_DISCARD_BUTTON_LABEL")

            )

        discard_dialog.callback = callback

        discard_dialog.callback_args = callback_args

        discard_dialog.callback_kwargs = callback_kwargs

        discard_dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)

        discard_dialog.connect("response", self._on_discard_dialog_response)

        discard_dialog.show()

        return discard_dialog

    def _show_reset_dialog(self, callback, *callback_args, **callback_kwargs):

        reset_dialog = Adw.MessageDialog.new(

            self._application_window,

            self._locale_manager.get("RESET_DIALOG_HEAD"),

            self._locale_manager.get("RESET_DIALOG_BODY")

            )

        reset_dialog.add_response(

            "back", self._locale_manager.get("RESET_DIALOG_BACK_BUTTON_LABEL")

            )

        reset_dialog.add_response(

            "continue", self._locale_manager.get("RESET_DIALOG_CONTINUE_BUTTON_LABEL")

            )

        reset_dialog.callback = callback

        reset_dialog.callback_args = callback_args

        reset_dialog.callback_kwargs = callback_kwargs

        reset_dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)

        reset_dialog.connect("response", self._on_reset_dialog_response)

        reset_dialog.show()

    def _show_delete_dialog(self, callback, *callback_args, **callback_kwargs):

        delete_dialog = Adw.MessageDialog.new(

            self._application_window,

            self._locale_manager.get("DELETE_DIALOG_HEAD"),

            self._locale_manager.get("DELETE_DIALOG_BODY")

            )

        delete_dialog.add_response(

            "back", self._locale_manager.get("DELETE_DIALOG_BACK_BUTTON_LABEL")

            )

        delete_dialog.add_response(

            "continue", self._locale_manager.get("DELETE_DIALOG_CONTINUE_BUTTON_LABEL")

            )

        delete_dialog.callback = callback

        delete_dialog.callback_args = callback_args

        delete_dialog.callback_kwargs = callback_kwargs

        delete_dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)

        delete_dialog.connect("response", self._on_delete_dialog_response)

        delete_dialog.show()

    def _update_menu_button(self):

        try:

            if hasattr(self._main_split_layout, "get_collapsed") and self._main_split_layout.get_collapsed():

                self._left_menu_button.set_menu_model(self._small_start_menu)

                self._left_menu_button.set_primary(True)

                self._current_menu_button = self._right_menu_button

                self._right_menu_button.set_visible(True)

                self._right_menu_button.set_primary(True)

                sub_menu_name = "small"

            else:

                self._left_menu_button.set_menu_model(self._big_start_menu)

                self._left_menu_button.set_primary(True)

                self._current_menu_button = self._left_menu_button

                self._right_menu_button.set_visible(False)

                self._right_menu_button.set_primary(False)

                sub_menu_name = "big"

            for menu_name in ["_{}_start_menu", "_{}_reset_starter_menu", "_{}_delete_starter_menu", "_{}_discard_starter_menu"]:

                setattr(self, menu_name.format("current"), getattr(self, menu_name.format(sub_menu_name)))

            else:

                self._update_menu_button_menu_model()

        except AttributeError as error:

            if not hasattr(self._main_split_layout, "get_collapsed"):

                pass

            else:

                raise error

    def _update_search_list_selection(self, name=None):

        if name is None:

            name = self._current_desktop_starter_name

        if not self._search_list.get_active_item() == name:

            self._search_list.set_active_item(name)

    def _update_menu_button_menu_model(self):

        try:

            if self._main_stack.get_visible_child() == self._start_page:

                self._current_menu_button.set_menu_model(self._current_start_menu)

                self._reset_starter_menu_section.set_enabled("reset_starter", False)

            elif self._main_stack.get_visible_child() == self._settings_page:

                if not self._current_desktop_starter_name is None:

                    if self._current_desktop_starter_name in self._unsaved_custom_starters:

                        self._current_menu_button.set_menu_model(self._current_discard_starter_menu)

                    elif self._get_desktop_starter_has_default(self._current_desktop_starter_name):

                        self._current_menu_button.set_menu_model(self._current_reset_starter_menu)

                        if self._get_desktop_starter_has_override(self._current_desktop_starter_name):

                            self._reset_starter_menu_section.set_enabled("reset_starter", True)

                        else:

                            self._reset_starter_menu_section.set_enabled("reset_starter", False)

                    else:

                        self._current_menu_button.set_menu_model(self._current_delete_starter_menu)

                else:

                    self._current_menu_button.set_menu_model(self._current_reset_starter_menu)

                    self._reset_starter_menu_section.set_enabled("reset_starter", False)

        except AttributeError as error:

            if not hasattr(self, "_main_split_layout"):

                pass

            elif not hasattr(self, "_current_menu_button"):

                pass

            else:

                raise error

    def _update_mime_data(self, parser, delete=False):

        operations = [{

            "section": "Added Associations",

            "path": os.path.join(GLib.get_user_config_dir(), "mimeapps.list"),

            "desktop-id": os.path.relpath(parser.get_save_path(), self._desktop_starter_override_dir).strip(os.path.sep).replace(os.path.sep, "-")

            }]

        if os.path.abspath(parser.get_save_path()).startswith(os.path.abspath(self._desktop_starter_override_dir)):

            operations.append({

                "section": "MIME Cache",

                "path": os.path.join(os.path.dirname(parser.get_save_path()), "mimeinfo.cache"),

                "desktop-id": os.path.basename(parser.get_save_path())

                })

        for operation in operations:

            section = operation["section"]

            path = operation["path"]

            desktop_id = operation["desktop-id"]

            mime_parser = ConfigParser(interpolation=None, strict=False)

            mime_parser.optionxform = str

            if not mime_parser.has_section(section):

                mime_parser.add_section(section)

            mimeinfo_changed = False

            if os.access(path, os.R_OK):

                mime_parser.read(path)

            app_mimetypes = parser.get_mimetypes()

            mime_data_dict = dict(mime_parser.items(section))

            for mime_data_mimetype in mime_data_dict:

                mime_data_names = list(filter(None, mime_data_dict[mime_data_mimetype].split(";")))

                if desktop_id in mime_data_names and (not mime_data_mimetype in app_mimetypes or delete):

                    mime_data_names.remove(desktop_id)

                    if len(mime_data_names):

                        mime_parser.set(section, mime_data_mimetype, f"{';'.join(mime_data_names)};")

                    else:

                        mime_parser.remove_option(section, mime_data_mimetype)

                    mimeinfo_changed = True

            if not delete:

                for app_mimetype in app_mimetypes:

                    if not app_mimetype in mime_data_dict:

                        mime_parser.set(section, app_mimetype, f"{desktop_id};")

                        mimeinfo_changed = True

                    elif not desktop_id in mime_data_dict[app_mimetype]:

                        mime_data_names = list(filter(None, mime_data_dict[app_mimetype].split(";")))

                        mime_data_names.append(desktop_id)

                        mime_parser.set(section, app_mimetype, f"{';'.join(mime_data_names)};")

                        mimeinfo_changed = True

            if mimeinfo_changed:

                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

                with open(path, "w") as file:

                    mime_parser.write(file, space_around_delimiters=False)

    def _load_settings_page(self, name):

        self._focus_settings_page()

        if name in self._unsaved_custom_starters and self._unsaved_custom_starters[name]["external"]:

            self._settings_page.set_always_show_save_button(True)

        else:

            self._settings_page.set_always_show_save_button(False)

        self._current_desktop_starter_name = name

        parser = self._desktop_starter_parsers[name]

        self._settings_page.load_desktop_starter(name, parser)

        if not self._main_stack.get_visible_child() == self._settings_page:

            self._main_stack.set_visible_child(self._settings_page)

        else:

            self._update_menu_button_menu_model()

        self._update_search_list_selection()

    def _save_settings_page(self, skip_dialog=False):

        parser = self._desktop_starter_parsers[self._current_desktop_starter_name]

        if (self._current_desktop_starter_name in self._unsaved_custom_starters and

            self._unsaved_custom_starters[self._current_desktop_starter_name]["external"] and

            not skip_dialog):

            self._show_install_dialog(self._install_external_starter, self._current_desktop_starter_name)

            return True

        else:

            try:

                parser.check_write()

                if not self._current_desktop_starter_name in self._unsaved_custom_starters or not self._unsaved_custom_starters[self._current_desktop_starter_name]["external"]:

                    self._settings_page.set_always_show_save_button(False)

                    self._update_mime_data(parser)

                self._settings_page.save_desktop_starter()

                if self._current_desktop_starter_name in self._text_editor.get_names():

                    parser.save(path=self._text_editor.get_path(self._current_desktop_starter_name))

            except Exception as error:

                self.log(error, error=error)

                self.notify(self._locale_manager.get("STARTER_SAVE_ERROR_TEXT"), error=error)

                return True

            else:

                if self._current_desktop_starter_name in self._unsaved_custom_starters and not self._unsaved_custom_starters[self._current_desktop_starter_name]["external"]:

                    del self._unsaved_custom_starters[self._current_desktop_starter_name]

                text = parser.get_name()

                if not len(text):

                    text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

                self.notify(self._locale_manager.get("STARTER_SAVE_MESSAGE_TEXT") % text)

                self._update_search_list_item(self._current_desktop_starter_name)

                self._update_menu_button_menu_model()

    def _get_random_unused_desktop_starter_name(self):

        while True:

            random_string = ''.join(random.choices(string.digits, k=6))

            name = "%s.%s" % (self._desktop_starter_custom_create_name, random_string)

            if not name in self._get_desktop_starter_names() and not name in self._unsaved_custom_starters:

                return name

    def _install_external_starter(self, name):

        parser = self._desktop_starter_parsers[name]

        save_path = self._get_desktop_starter_override_path(name)

        parser.set_save_path(save_path)

    def _load_external_starters(self, *paths, skip_discard_dialog=False):

        exceptions = {}

        filtered_paths = []

        duplicate_names = []

        accepted_names = []

        for path in paths:

            path = os.path.abspath(path)

            if not path in filtered_paths:

                filtered_paths.append(path)

        else:

            paths = filtered_paths

        for name, data in self._unsaved_custom_starters.items():

            if data["external"] and data["load-path"] in paths:

                paths.remove(data["load-path"])

                duplicate_names.append(name)

        else:

            if not len(paths):

                if len(duplicate_names):

                    name = duplicate_names[0]

                    if not skip_discard_dialog:

                        self._check_unsaved_data(self._load_settings_page, name, ignore_name=name)

                    else:

                        self._load_settings_page(name)

            else:

                for path in reversed(paths):

                    if os.path.exists(path) and os.path.isfile(path) and os.access(path, os.R_OK):

                        name = self._get_random_unused_desktop_starter_name()

                        self._unsaved_custom_starters[name] = {

                            "load-path": path,

                            "save-path": path,

                            "external": True

                            }

                        try:

                            self._add_desktop_starter(name)

                            accepted_names.append(name)

                        except Exception as error:

                            exceptions[path] = (name, error, path)

                    else:

                        exceptions[path] = None, None, path

                else:

                    if len(exceptions):

                        for name, error, path in exceptions.values():

                            if not name is None:

                                self.log(error, error=error)

                                del self._unsaved_custom_starters[name]

                            else:

                                self.log(f"not readable file: {path}")

                        if len(exceptions) == 1:

                            self.notify(

                                self._locale_manager.get("LOAD_SINGLE_ERROR_TEXT") % os.path.basename(list(exceptions.keys())[0]),

                                error=True

                                )

                        else:

                            self.notify(

                                self._locale_manager.get("LOAD_MULTIPLE_ERROR_TEXT") % str(len(exceptions)),

                                error=True

                                )

                if len(accepted_names):

                    name = accepted_names[0]

                    if not skip_discard_dialog:

                        self._check_unsaved_data(self._load_settings_page, name, ignore_name=name)

                    else:

                        self._load_settings_page(name)

    def _create_desktop_starter(self):

        if (self._current_desktop_starter_name in self._unsaved_custom_starters and

            not self._unsaved_custom_starters[self._current_desktop_starter_name]["external"]):

            self._search_list.set_active_item(self._current_desktop_starter_name, activate=False)

            self._focus_settings_page()

        else:

            for name in self._unsaved_custom_starters:

                if not self._unsaved_custom_starters[name]["external"]:

                    self._search_list.set_active_item(name, activate=False)

                    self._load_settings_page(name)

                    break

            else:

                name = self._get_random_unused_desktop_starter_name()

                self._unsaved_custom_starters[name] = {

                    "load-path": self._desktop_starter_template_path,

                    "save-path": self._get_desktop_starter_override_path(name),

                    "external": False

                    }

                self._add_desktop_starter(name)

                parser = self._desktop_starter_parsers[name]

                text = parser.get_name()

                if not len(text):

                    text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

                self.notify(self._locale_manager.get("STARTER_CREATE_MESSAGE_TEXT") % text)

                self._search_list.set_active_item(self._current_desktop_starter_name, activate=False)

                self._load_settings_page(name)

    def _reset_desktop_starter(self, name):

        path = self._get_desktop_starter_override_path(name)

        parser = self._desktop_starter_parsers[name]

        try:

            self._update_mime_data(parser, delete=True)

            os.remove(path)

        except Exception as error:

            self.log(error, error=error)

            self.notify(self._locale_manager.get("STARTER_RESET_ERROR_TEXT"), error=error)

            return True

        text = parser.get_name()

        if not len(text):

            text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

        self.notify(self._locale_manager.get("STARTER_RESET_MESSAGE_TEXT") % text)

        self._add_desktop_starter(name, skip_search_list=True, exist_ok=True)

        self._update_search_list_item(name)

        if name == self._current_desktop_starter_name:

            self._load_settings_page(name)

    def _delete_desktop_starter(self, name):

        path = self._desktop_starter_parsers[name].get_save_path()

        parser = self._desktop_starter_parsers[name]

        try:

            self._update_mime_data(parser, delete=True)

            os.remove(path)

        except Exception as error:

            self.log(error, error=error)

            self.notify(self._locale_manager.get("STARTER_DELETE_ERROR_TEXT"), error=error)

            return True

        text = parser.get_name()

        if not len(text):

            text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

        self.notify(self._locale_manager.get("STARTER_DELETE_MESSAGE_TEXT") % text)

        self._remove_desktop_starter(name)

    def _edit_desktop_starter(self, name):

        parser = self._desktop_starter_parsers[name]

        try:

            self._text_editor.launch(name, parser)

        except Exception as error:

            self.log(error, error=error)

            self.notify(self._locale_manager.get("OPEN_FILE_ERROR_TEXT"), error=error)


    def _get_parser_should_be_shown(self, parser):

        if not self._config_manager.get("show.hidden"):

            if not parser.get_visible():

                return

            else:

                only_show_in_values = set(filter(None, parser.get_only_show_in().split(";")))

                not_show_in_values = set(filter(None, parser.get_not_show_in().split(";")))

                if only_show_in_values and not only_show_in_values.intersection(self._xdg_current_desktop_values):

                    return

                elif not_show_in_values and not_show_in_values.intersection(self._xdg_current_desktop_values):

                    return

                else:

                    return True

        else:

            return True

    def _add_search_list_item(self, name):

        if not self._get_parser_should_be_shown(self._desktop_starter_parsers[name]):

            return True

        text = self._desktop_starter_parsers[name].get_name()

        icon = self._desktop_starter_parsers[name].get_icon()

        search_data = self._desktop_starter_parsers[name].get_search_data()

        if not len(text):

            text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

            search_data.append(text)

        self._search_list.add(name, text, icon, search_data)

    def _remove_search_list_item(self, name):

        try:

            self._search_list.remove(name)

        except gui.ItemNotFoundError:

            pass

        if name == self._current_desktop_starter_name:

            self._main_stack.set_visible_child(self._start_page)

            self._search_list.set_active_item(self._current_desktop_starter_name, activate=False)

    def _update_search_list_item(self, name):

        parser = self._desktop_starter_parsers[name]

        if not self._get_parser_should_be_shown(parser):

            self._remove_search_list_item(name)

        else:

            text = parser.get_name()

            icon = parser.get_icon()

            search_data = parser.get_search_data()

            if not len(text):

                text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

                search_data.append(text)

            try:

                self._search_list.update(name, text, icon, search_data)

            except gui.ItemNotFoundError:

                self._search_list.add(name, text, icon, search_data)

    def _reload_search_list_items(self):

        self._search_list.clear()

        for name in self._desktop_starter_parsers:

            self._add_search_list_item(name)

        if not self._current_desktop_starter_name in self._search_list.list():

            self._main_stack.set_visible_child(self._start_page)

            self._search_list.set_active_item(self._current_desktop_starter_name, activate=False)

        else:

            self._search_list.set_active_item(self._current_desktop_starter_name, activate=False)

    def _add_desktop_starter(self, name, skip_search_list=False, exist_ok=False):

        if not name in self._desktop_starter_parsers or exist_ok:

            parser = self._parse_desktop_starter(name)

            self._desktop_starter_parsers[name] = parser

            if not skip_search_list:

                self._add_search_list_item(name)

        else:

            raise StarterAlreadyExistingError(name)

    def _remove_desktop_starter(self, name, skip_search_list=False, notify_user=False):

        text = self._desktop_starter_parsers[name].get_name()

        if name is self._current_desktop_starter_name:

            self._settings_page.reset()

        if name in self._unsaved_custom_starters:

            del self._unsaved_custom_starters[name]

        if name in self._desktop_starter_parsers:

            del self._desktop_starter_parsers[name]

            if not skip_search_list:

                if self._search_list.get_search_mode():

                    items = self._search_list.get_visible_items()

                    try:

                        next_index = items.index(name) + 1

                        if not next_index < len(items):

                            next_index = items.index(name) - 1

                    except ValueError:

                        next_index = - 1

                    try:

                        next_item = items[next_index]

                    except IndexError:

                        pass

                    else:

                        if not next_item == name:

                            self._load_settings_page(next_item)

                        elif self._search_list.get_search_mode():

                            self._search_list.set_search_mode(False)

                self._remove_search_list_item(name)

        else:

            raise StarterNotFoundError(name)

        if notify_user:

            if not len(text):

                text = self._locale_manager.get("UNNAMED_APPLICATION_PLACEHOLDER_TEXT")

            self.notify(self._locale_manager.get("STARTER_REMOVE_MESSAGE_TEXT") % text)

    def _parse_desktop_starter(self, name):

        if name in self._unsaved_custom_starters:

            load_path = self._unsaved_custom_starters[name]["load-path"]

        else:

            load_path = self._get_desktop_starter_override_path(name, include_host=True)

        if name in self._unsaved_custom_starters:

            save_path = self._unsaved_custom_starters[name]["save-path"]

        else:

            save_path = self._get_desktop_starter_override_path(name, include_host=True)

        if not os.path.exists(load_path):

            default_path = self._get_desktop_starter_default_path(name, include_host=True)

            if os.path.exists(default_path):

                load_path = default_path

            else:

                raise StarterNotFoundError(name)

        parser = DesktopParser(self, load_path, save_path)

        return parser

    def _parse_command_line_args(self, args):

        if len(args) and "--new" in args:

            self._create_desktop_starter()

            args.remove("--new")

        self._load_external_starters(*args)

    def notify(self, text, error=False):

        toast = Adw.Toast.new(text)

        if hasattr(toast, "set_use_markup"):

            toast.set_use_markup(False)

        if not error:

            toast.set_timeout(gui.Timeout.DEFAULT)

        else:

            if isinstance(error, NoAccessError):

                toast.set_title(self._locale_manager.get("STARTER_NO_ACCESS_ERROR_TEXT"))

            toast.set_timeout(0)

            toast.set_action_name("toast.details")

            toast.set_button_label(self._locale_manager.get("TOAST_SHOW_DETAILS_BUTTON_LABEL"))

        self._toast_overlay.add_toast(toast)

    def log(self, text, error=None):

        self._debug_log.add(text, error=error)

if __name__ == "__main__":

    project_dir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

    app = Application(project_dir, application_id="page.codeberg.libre_menu_editor.LibreMenuEditor")

    app.run()
