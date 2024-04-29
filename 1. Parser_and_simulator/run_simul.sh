#!bin/bash
pushd simulator
bash compile.sh
popd

gcc -o main main.c -L./simulator -lsimulator
./main