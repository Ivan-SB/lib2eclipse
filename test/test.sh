#/usr/bin/env sh
cp -r ~/Documents/workspace/c2eT  ~/Documents/workspace/c2eT.bak
cd ..
./cube2eclipse.py -p ~/Documents/workspace/c2eT -l /usr/local/src/STM32Cube_FW_F1_V1.3.0 -c ~/Documents/stm32/c2eT -r -a install
cd ./test


