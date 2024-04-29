#!bin/bash

gcc -c simulator.c
ar rc libsimulator.a simulator.o
ranlib libsimulator.a