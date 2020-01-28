let
  pkgs = import <nixpkgs> {};
  requirements = pkgs.callPackage ./requirements.nix {};
in pkgs.mkShell {
  buildInputs = [
    requirements.interpreter
    pkgs.wabt
  ];
}
