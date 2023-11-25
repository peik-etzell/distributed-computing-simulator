{ pkgs ? import <nixpkgs> { } }:
let
  python = pkgs.python311;
  pythonEnv = python.withPackages
    (ps: with ps; [ pip virtualenvwrapper python-lsp-server ]);
  lib-path = with pkgs; lib.makeLibraryPath [ libffi openssl stdenv.cc.cc ];
in pkgs.mkShell {
  packages = [ pythonEnv ];
  shellHook = ''
    export "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${lib-path}"

    VENV=.venv
    if test ! -d $VENV; then
        virtualenv $VENV
    fi
    source ./$VENV/bin/activate
    export PYTHONPATH=`pwd`/$VENV/${python.sitePackages}/:$PYTHONPATH

  '';
}
