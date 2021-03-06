# lib2eclipse

## Overview
This program was originally conceived to import CubeMX projects into GNU ARM Eclipse plugin http://gnuarmeclipse.github.io/  
At this stage it can only do that.

However it has some methods that could be used in a more general way to import and relocate external libraries into C projects without them being located in the workspace.  
This means that if you need to use a library in an GNU ARM Eclipse C/C++ project:
* you won't have to add all include paths by hand
* you will be helped to update all include paths if you relocate the library
* you'll be helped to replace your library with a new version

## HOWTO
1. Download the CubeMX library from ST website and unzip it somewhere
2. Create a CubeMX project somewhere
3. Create a GNU ARM Eclipse project for your ST family
4. Optionally if you've installed GNU ARM plugins packs set the project > Proprieties > C/C++ Build > Settings > Devices
5. close the project
6. Use this tool
7. Refresh your C project (F5)
8. Due to a problem in FreeRTOS disable Link-time optimizer -flto (Proprieties > C/C++ Build > Settings > Optimization) [^1]
I noticed that sometimes you've to close/reopen a project more than once before Eclipse get aware of all the changes to get a successful build.

The program makes a backup of your .cproject file. The backup copy is never overwritten.

### Examples
#### first install over a fresh GNU ARM STM32 project
./cube2eclipse.py -c [path to your CubeMX project] -l [path to the CubeMX library] -p [path to your GNU ARM Eclipse project] -a install -w -mfreertos
-w is needed to cleanup not useful directories and settings of GNU ARM project.
#### remove code and configuration related to CubeMX
./cube2eclipse.py -c [path to your CubeMX project] -l [path to the CubeMX library] -p [path to your GNU ARM Eclipse project] -a remove
#### installation of a new version of CubeMX library or a CubeMX project generated with a new CubeMX tool
unzip somewhere else the CubeMX library
./cube2eclipse.py -c [path to your CubeMX project] -l [path to the CubeMX NEW library] -p [path to your GNU ARM Eclipse project] -a install
this will replace all includes, source etc... with new ones leaving untouched everything you wrote outside of the STCube dir
### Modules
You can enable FatFs, USBDevice, USBHost, STemWin, FreeRTOS, LwIP modules

## FreeRTOS
I prefer to directly work with FreeRTOS in spite of using CMSIS OS wrapper, I've excluded from build freertos.c and I've added a freertos_setup.c and freertos_setup.h that contain an FreeRTOS initialization skeleton. But since STemWin and LwIP libraries still require cmsis_os.h I left it there.
Upstream FreeRTOS doesn't include Source/CMSIS_RTOS/, if you want to use a newer version of FreeRTOS you'll have to copy that dir content into ./CMSIS_RTOS/ (relative to cube2eclipse.py). I'm not including those files since it is not clear to me if I've the right to redistribute them.

## Semihosting & Co.
Liviu Ionescu had done a great work providing support for different trace strategies but I'm a humble programmer and I found I could just manage a simpler approach.
So I distilled a simpler systemcalls.c version that works with CubeMX ldscript.

## TODO
Importing CubeMX projects into Eclipse requires some specialized additional steps than just adding include path and some symlink into Eclipse workspace:
* discover the MCU
* picking up the right linker script and startup code
* do some cleanup
But the most tedious part of importing a library is setting up include paths and importing the source code into the workspace.
**These functionalities are already implemented in current code but should be extracted in a library and made easier to use with other libraries as well**

## Known bugs
### Exclude from Build...
Since I'm linking most of CubeMX library including examples, BSP etc... inside the workspace, way too much stuff get compiled.
Some of this stuff may cause compilation errors because of missing configuration files (mostly stuff in Middleware), some may cause errors because of redefinition of functions or because they are templates.

Now this program provide some help to exclude from build directories and files that will break the build and an option (-m) to conditionally add FreeRTOS and in the future other modules.

To get things working as you need you may still check:
* Middlewares
* Drivers/CMSIS/DSP_Lib
* Drivers/BSP
because it may take way to long to compile and you'd use the compiled version of the math library or because you may miss configuration files
* Utilities

If you've to use FreeRTOS you'll still have to chose manually which memory management to use (heap_N.c)

### Binary libraries
Unfortunately at this moment I don't know how to generate numeric id for Eclipse .cproject
So if the original project doesn't have some "<option>" already specified, this tool won't be
able to add the listOptionValue.
This more concretely means in the case of GNU ARM plugin projects, it won't be able to add arm math binary library to your linker options.
A workaround is to add a fake entry to
Proprieties > C/C++ Build -> Settings > Cross ARM C Linker > Libraries
a fake entry

[^1]: https://gcc.gnu.org/wiki/LinkTimeOptimizationFAQ
