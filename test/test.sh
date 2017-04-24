#/usr/bin/env sh

. ./const.sh

tar -xf ./eclipse/c2eT.tar.bz2 -C ../../

cd ..

#./cube2eclipse.py -p ~/Documents/workspace/c2eT -l /usr/local/src/STM32Cube_FW_F1_V1.4.0l -c ~/Documents/stm32/c2eT -r -a install
#./cube2eclipse.py -p ~/Documents/workspace/c2eT -l /usr/local/src/STM32Cube_FW_F1_V1.3.0 -c ~/Documents/stm32/c2eT -w -r -a install -mFreeRTOS
./cube2eclipse.py -p "$projectpath" -l "$librarypath" -c "$stm32cubemxpath" -w -r -a install -mFreeRTOS

#cp ./.cproject ~/Documents/workspace/c2eT

cd ./test
