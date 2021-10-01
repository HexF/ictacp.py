{ pkgs ? import <nixpkgs> {} }:
with pkgs.python3Packages;
  pkgs.mkShell {
    nativeBuildInputs = with pkgs; [
      python3 poetry
    ];
}