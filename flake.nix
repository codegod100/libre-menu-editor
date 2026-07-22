{
  description = "Libre Menu Editor — customize application menu launchers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          libre-menu-editor = pkgs.callPackage ./package.nix { };
        in
        {
          inherit libre-menu-editor;
          default = libre-menu-editor;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/libre-menu-editor";
          meta = {
            description = "Libre Menu Editor";
          };
        };
      });

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.default ];
            packages = with pkgs; [
              (python3.withPackages (ps: [ ps.pygobject3 ]))
              gtk4
              libadwaita
              gobject-introspection
              xdg-utils
            ];
          };
        }
      );

      overlays.default = final: _prev: {
        libre-menu-editor = final.callPackage ./package.nix { };
      };

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-rfc-style);
    };
}
