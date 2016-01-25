# lib2eclipse

## Overview
This program was originally conceived to import CubeMX projects into GNU ARM Eclipse plugin.
At this stage it can only do that.

However it has some methods that could be used in a more general way to import and relocate external libraries into C projects without them being located in the workspace.
This means that if you need to use a library in an GNU ARM Eclipse C/C++ project:
* you won't have to add all include paths by hand
* you will be helped to update all include paths if you relocate the library
* you'll helped to replace your library with a new version

## TODO
Importing CubeMX projects into Eclipse requires some specialized additional steps than just adding include path and some symlink into Eclipse workspace:
* discover the MCU
* picking up the right linker script and startup code
* do some cleanup
But the most tedious part of importing a library is setting up include paths and importing the source code into the workspace.
The most tedious part of updating or removing a library is removing/updating the source in the workspace.
**These functionalities are already implemented in current code but should be extracted in a library and made easier to use.**


## Known bugs
Unfortunately at this moment I don't know how to generate numeric id for Eclipse .cproject
So if the original project doesn't have some "<option>" already specified, this tool won't be
able to add the listOptionValue.
This more concretely means in the case of GNU ARM plugin projects, it won't be able to add arm math binary library to your linker options.
A workaround is to add a fake entry to
Proprieties > C/C++ Build -> Settings > Cross ARM C Linker > Libraries
a fake entry

