#!/bin/sh

cd ./crypted
gpg -d base.py.p.asc | patch -p0

