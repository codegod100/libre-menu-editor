{
  lib,
  stdenvNoCC,
  python3,
  wrapGAppsHook4,
  gobject-introspection,
  gtk4,
  libadwaita,
  glib,
  xdg-utils,
  gdk-pixbuf,
  librsvg,
  hicolor-icon-theme,
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.pygobject3 ]);
in
stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "libre-menu-editor";
  version = "1.10.4";

  src = lib.cleanSource ./.;

  nativeBuildInputs = [
    wrapGAppsHook4
    gobject-introspection
  ];

  buildInputs = [
    pythonEnv
    gtk4
    libadwaita
    glib
    xdg-utils
    gdk-pixbuf
    librsvg
    hicolor-icon-theme
  ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share $out/bin
    cp -r libre-menu-editor $out/share/libre-menu-editor
    cp -r export/share/* $out/share/

    # Drop Flatpak-only desktop key
    sed -i '/^X-Flatpak=/d' \
      $out/share/applications/page.codeberg.libre_menu_editor.LibreMenuEditor.desktop

    # main.py resolves project_dir from its own path and is a valid entrypoint
    sed -i "1s|.*|#!${pythonEnv.interpreter}|" $out/share/libre-menu-editor/main.py
    chmod +x $out/share/libre-menu-editor/main.py
    ln -s $out/share/libre-menu-editor/main.py $out/bin/libre-menu-editor

    runHook postInstall
  '';

  meta = {
    description = "Customize application menu launchers";
    longDescription = ''
      Libre Menu Editor is a free and libre tool for editing application menu
      entries (.desktop files) with a modern GTK4/libadwaita interface.
    '';
    homepage = "https://codeberg.org/libre-menu-editor/libre-menu-editor";
    changelog = "https://codeberg.org/libre-menu-editor/libre-menu-editor/releases";
    license = lib.licenses.gpl3Plus;
    mainProgram = "libre-menu-editor";
    platforms = lib.platforms.linux;
  };
})
