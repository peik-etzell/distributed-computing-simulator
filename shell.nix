{ pkgs ? import <nixpkgs> { } }:
let
  python = pkgs.python311;
  pythonEnv = python.withPackages
    (ps: with ps; [ pip virtualenvwrapper ]);
in pkgs.mkShell {
  packages = [ pythonEnv ];
  shellHook = ''
    VENV=.venv
    if test ! -d $VENV; then
        virtualenv $VENV
    fi
    source ./$VENV/bin/activate
    export PYTHONPATH=`pwd`/$VENV/${python.sitePackages}/:$PYTHONPATH
  '';
}
