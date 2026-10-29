#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
git init -q && git add -A && git -c user.name=fixture -c user.email=fixture@example.org commit -qm "fixture"
# Simulate a Windows checkout: committed files have LF, the working copy gets CRLF.
git config core.autocrlf true && rm -rf src conf && git checkout -q -- .
