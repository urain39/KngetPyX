#!/bin/sh

cd ./crypted
gpg -d base.py.p.asc | patch $1 -p0 ../kngetx/base.py
