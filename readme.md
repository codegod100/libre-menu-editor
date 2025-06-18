<img src="https://codeberg.org/libre-menu-editor/downloads/raw/branch/main/screenshots/9.png"/>

# One-Click installation

- through the software center on [many GNU+Linux distributions](https://flathub.org/setup)
- through the [Arch-User-Repository](https://aur.archlinux.org/packages/libre-menu-editor) on [ArchLinux](https://archlinux.org)-based systems
- through the [download-page](https://flathub.org/apps/page.codeberg.libre_menu_editor.LibreMenuEditor) on flathub

---

# Manual setup

### Dependencies:
 - python3
 - python3-gobject
 - libadwaita >= 1.4 *(for adaptive interface)*
 - libadwaita >= 1.2 *(for static interface)*
 - libgtk >= 4.8
 - xdg-utils

## First: Download the code
```
git clone https://codeberg.org/libre-menu-editor/libre-menu-editor
cd libre-menu-editor
```

## Option 1: Run without installation
```
libre-menu-editor/main.py
```

## Option 2: Install with flatpak-builder
```
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install org.gnome.Platform/x86_64/48
flatpak-builder --user --install --force-clean .build-dir flatpak.yml
```

## Option 3: Install with make
```
sudo make install
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor
```

---

# How to contribute

### Option 1: Improving the translation

If you want to improve a translation, it is recommended to do so through the [weblate](https://translate.codeberg.org/projects/libre-menu-editor). Alternatively, you can edit the [translation files](libre-menu-editor/locales) directly and contribute your changes in a [pull request](https://codeberg.org/libre-menu-editor/libre-menu-editor/pulls).

### Option 2: Reporting bugs and giving feedback

If you have encountered a problem or think that an important feature is missing, please open an [issue](https://codeberg.org/libre-menu-editor/libre-menu-editor/issues).

---

# Contributions

**2023-07-01**: [albano.battistella](mailto:albano.battistella@noreply.codeberg.org) added italian translations: [it.json](libre-menu-editor/locales/it.json)

**2024-01-07**: [locness3](mailto:locness3@e.email) improved french translations: [fr.json](libre-menu-editor/locales/fr.json)

**2024-04-28**: [Sabri Ünal](mailto:yakushabb@gmail.com) added turkish translations: [tr.json](libre-menu-editor/locales/tr.json)

**2024-07-29**: [SomeTr](https://translate.codeberg.org/user/SomeTr) improved ukrainian translations: [uk.json](libre-menu-editor/locales/uk.json)

**2024-08-09**: [NaumovSN](https://translate.codeberg.org/user/NaumovSN) added russian translations: [ru.json](libre-menu-editor/locales/ru.json)

**2024-08-26**: [meskobalazs](https://translate.codeberg.org/user/meskobalazs) added hungarian translations: [hu.json](libre-menu-editor/locales/hu.json)

**2024-11-04**: [SomeTr](https://translate.codeberg.org/user/SomeTr) improved ukrainian translations: [uk.json](libre-menu-editor/locales/uk.json)

**2025-01-20**: [NaumovSN](https://translate.codeberg.org/user/NaumovSN) improved russian translations: [ru.json](libre-menu-editor/locales/ru.json)

**2025-04-20**: [jrtcdbrg](https://translate.codeberg.org/user/jrtcdbrg) improved estonian translations: [et.json](libre-menu-editor/locales/et.json)

**2025-05-01**: [SomeTr](https://translate.codeberg.org/user/SomeTr) improved ukrainian translations: [uk.json](libre-menu-editor/locales/uk.json)

**2025-06-04**: [norlin](mailto:norlin@noreply.codeberg.org) improved swedish translations: [sv.json](libre-menu-editor/locales/sv.json)

**2025-06-15**: [Poesty Li](https://translate.codeberg.org/user/poesty) added chinese translations: [zh_Hans.json](libre-menu-editor/locales/zh_Hans.json)

