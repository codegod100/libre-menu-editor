ARCH := $(shell arch)
appimage:
	mkdir -p AppDir/usr
	cp -r export/* AppDir/usr
	mkdir -p AppDir/usr/share
	cp -r libre-menu-editor AppDir/usr/share/libre-menu-editor
	cp export/share/icons/hicolor/scalable/apps/page.codeberg.libre_menu_editor.LibreMenuEditor.svg AppDir/
	cp export/share/applications/page.codeberg.libre_menu_editor.LibreMenuEditor.desktop AppDir/
	ln -s ./usr/share/libre-menu-editor/main.py AppDir/AppRun | true
	wget -O appimagetool -nc "https://github.com/AppImage/appimagetool/releases/download/1.9.0/appimagetool-${ARCH}.AppImage"
	echo "46fdd785094c7f6e545b61afcfb0f3d98d8eab243f644b4b17698c01d06083d1 appimagetool" | sha256sum -c
	chmod +x appimagetool
	ARCH=aarch64 ./appimagetool AppDir
	ARCH=i686 ./appimagetool AppDir
	ARCH=x86_64 ./appimagetool AppDir

flatpak:
	mkdir -p /app
	cp -r export/* /app
	mkdir -p /app/share
	cp -r libre-menu-editor /app/share/libre-menu-editor

install:
	mkdir -p $(DESTDIR)/usr
	cp -r export/* $(DESTDIR)/usr
	mkdir -p $(DESTDIR)/usr/share
	cp -r libre-menu-editor $(DESTDIR)/usr/share/libre-menu-editor
