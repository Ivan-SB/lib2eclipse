#/usr/bin/env sh

. ./const.sh

tar -xf ./eclipse/c2eT.tar.bz2 -C ../../

cd ..

./cube2eclipse.py -p "$projectpath" -l "$librarypath" -c "$stm32cubemxpath" -w -r -a install -mFreeRTOS

cd ./test
