#!/bin/sh
make cleanall
make all

if [ ! -f ./graph-engine ]
  then echo "stage of building graph-engine by makefile failed"
fi