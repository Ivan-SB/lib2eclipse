#!/usr/bin/env python3
# -*- coding: utf-8-*

'''
@package: cube2eclipse
@contact: mail@webthatworks.it
@author: Ivan Sergio Borgonovo
@copyright: 2016 Ivan Sergio Borgonovo
@license: GPL2
@date 2016-01-22
'''

__version__ = '0.1'
__libversion__ = '0.1'
__url__ = 'https://github.com/Ivan-SB/lib2eclipse'

import argparse

import os
import glob
import shutil
import sys

import re
from lxml import etree

HEADERS = ('.h', '.hpp', '.hh', '.h++', '.hxx')
BINLIB = ('.a', '.la', '.lo', '.so')
STMDIR = 'SW4STM32'
INCLUDECACHE = 'includecache.csv'

MCURE = 'STM32(.)(.)0(.)(.)(.)'

LIBRARYNAME = "STCube"
LIBRARYVERSION = "1.3.0"
LIBRARYHASH = "000"

LDSCRIPT = '{}_FLASH.ld'
BINLIBPATH = ("Drivers/CMSIS/Lib/GCC",)

SYSTEMC = "system_stm32{}{}xx.c"
SYSTEMPATH = "Drivers/CMSIS/Device/ST/STM32{}{}xx/Source/Templates"

STARTUP = "startup_stm32{}{}0{}x{}.{}"
STARTUPPATH = "Drivers/CMSIS/Device/ST/STM32{}{}xx/Source/Templates/gcc"

class cube2eclipse():
    """docstring"""
    EXCLUDE = ('/Projects', '/DSP_Lib/Examples',
               '/RTOS/Template',
               '/portable/IAR', '/portable/Keil', '/portable/RVDS', '/portable/GCC',
               '/portable/Tasking')
    EXCLUDEr = re.compile("|".join(EXCLUDE))
    MCUr = re.compile(MCURE)

# TODO componenttype should be an Enum
# TODO consolidate the use of common path syscalls, systemfile etc...

    def CleanList(self, xmllist):
      for e in xmllist:
        e.getparent().remove(e)

    def CleanListFiltered(self, xmllist, sieve):
      values = []
      for e in sieve:
        values.append(sieve.attrib['value'])
      for e in xmllist:
        if e.attrib['value'] in values:
          e.getparent().remove(e)

    def ProjectClean(self, optionpath, uoptionpath, componenttype='current'):
      options = self.project.xpath(optionpath)
      if componenttype == 'all':
        self.CleanList(options)
      elif componenttype == 'current':
        if hasattr(self, 'previousundolibrary'):
          uoptions = self.previousundolibrary.xpath(uoptionpath)
          if len(uoptions) > 0:
            self.CleanListFiltered(options, uoptions[0])

    def TreePrint(self, tree, file):
      s = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")
      if file:
        with open(file, 'wb+') as f:
          f.write(s)
      else:
        print(s)

    def ProjectPrint(self, file):
      self.TreePrint(self.project, file)

    def ProjectSave(self):
      self.ProjectPrint(os.path.join(self.projectpath, '.cproject'))

    def CubeProjectLoad(self):
      projectdir = os.path.normpath(os.path.expanduser(self.cubeproject))
      projectname = os.path.basename(projectdir)
      eclipseproject = os.path.join(projectdir, STMDIR, projectname)
      cproject = os.path.join(eclipseproject, '.cproject')
      if os.path.isfile(cproject) and os.access(cproject, os.R_OK):
        self.cubecprojectx = etree.parse(open(cproject, "r"))
      else:
        sys.exit("{} can't be opened for reading".format(cproject))
#       project  = os.path.join(eclipseproject, '.project')
#       if os.path.isfile(project) and os.access(project, os.R_OK):
#         self.cubeprojectx = etree.parse(open(project, "r"))
#       else:
#         sys.exit("{} can't be opened for reading".format(project))
      self.CubeLibraryCheck()
      self.CubeGetInfo()
      self.ldscript = os.path.join(eclipseproject, LDSCRIPT.format(self.MCU))

    def CubeLibraryCheck(self):
      if (os.path.isdir(self.cubelibrary) and
          os.path.isdir(os.path.join(self.cubelibrary, 'Drivers')) and
          os.path.isdir(os.path.join(self.cubelibrary, 'Middlewares'))):
        return
      else:
        sys.exit("{} doesn't look as the Cube Library directory".format(self.cubelibrary))

    def CubeGetInfo(self):
      options = self.cubecprojectx.xpath('//option[@name="Mcu" and @superClass="fr.ac6.managedbuild.option.gnu.cross.mcu"]')[0]
      self.MCU = options.attrib["value"]
      self.MCUp = re.match(self.MCUr, self.MCU).groups()
    
    def GetCM(self, code):
#       L0 F0 CM0
#       L1 F1 F2 CM3
#       L4 F3 F4 CM4
#       F7 CM7
      if (code == '0'):
        cm = '0'
      elif (code == '1' or code == '2'):
        cm = '3'
      elif (code == '3' or  code == '4'):
        cm = '4'
      elif (code == '7' ):
        cm = '7'
      else:
        pass
      return cm

    def LibraryIncludeGet(self):
      # TODO should include /portable/Tasking and other subdirs
      return (
              os.path.join(self.cubelibrary, 'Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/', 'ARM_CM' + self.GetCM(self.MCUp[1])),
              '"${workspace_loc:/${ProjName}/STCube/Inc}"'
              )

    def UndoSave(self):
      self.TreePrint(self.undo, os.path.join(self.projectpath, '.cprojectundo'))

    def UndoLoad(self):
      projectundo = os.path.join(self.projectpath, '.cprojectundo')
      if(os.path.isfile(projectundo)):
        self.previousprojectundo = projectundo
        self.previousundo = etree.parse(open(projectundo, 'r+'))
        previousundolibrary = self.previousundo.xpath('//lib2eclipse/library[@name="{}"]'.format(LIBRARYNAME))
        if len(previousundolibrary) > 0:
          self.previousundolibrary = previousundolibrary[0]

    def __init__(self, cubeproject, cubelibrary, includecache, refresh, components):
      self.components = components.lower().split(',')
      self.cubeproject = cubeproject
      self.cubelibrary = cubelibrary
      self.includecache = includecache
      if not self.includecache:
        self.includes = self.IncludeScan()
      else:
        if(os.path.isfile(self.includecache) and not refresh):
          self.includes = self.IncludeLoad()
        else:
          self.includes = self.IncludeScan()
          self.IncludeSave()
      self.CubeProjectLoad()
      self.includes.extend(self.LibraryIncludeGet())

    def ProjectLoad(self, project, wipe):
      cproject = os.path.join(project, '.cproject')
      if os.path.isfile(cproject) and os.access(cproject, os.W_OK):
        self.projectpath = project
        self.project = etree.parse(open(cproject, 'r+'))
        self.undo = etree.Element("lib2eclipse", {'version': __version__, 'URL': __url__})
        self.undolibrary = etree.SubElement(self.undo, 'library', name=LIBRARYNAME)
        self.wipe = wipe
      else:
        sys.exit("{} can't be opened for writing".format(cproject))
      self.UndoLoad()

    def IncludeScan(self):
      includes = []
      for dirpath, _, filenames in os.walk(self.cubelibrary):
        for f in filenames:
          if os.path.splitext(f)[1].lower() in HEADERS and not self.IncludeExclude(dirpath):
            includes.append(dirpath)
            break
      return includes

    def IncludeLoad(self):
      with open(self.includecache) as f:
        return f.read().splitlines()

    def IncludeSave(self):
      with open(self.includecache, "w") as f:
        for l in self.includes:
          f.write(l)
          f.write("\n")

    def IncludeExclude(self, dirpath):
      return re.search(self.EXCLUDEr, dirpath)

    def ProjectCleanInclude(self, componenttype='current'):
      optionpath = '//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue'
      uoptionpath = '//include/listOptionValue'
      self.ProjectClean(optionpath, uoptionpath, componenttype)

    def ProjectCleanIncludeList(self, alienlibraries):
      includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue')
      for i in includes:
        if i.attrib['value'].startswith(tuple(alienlibraries)):
          i.getparent().remove(i)

    def ProjectAddInclude(self):
      includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]')
      for i in includes:
        for l in self.includes:
          etree.SubElement(i, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})
      # undo
      uinclude = etree.SubElement(self.undolibrary, 'include')
      for l in self.includes:
          etree.SubElement(uinclude, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})

    def GetExcludeSrc(self):
      templates = ["STCube/Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_msp_template.c", "STCube/Drivers/CMSIS/Device/ST/STM32F1xx/Source/Templates", "STCube/Drivers/CMSIS/RTOS"]
      DSPlib = ["STCube/Drivers/CMSIS/DSP_Lib"]
      STlib = ["STCube/Middlewares/ST"]
      BSP = ["STCube/Drivers/BSP"]
      
      UT = ["STCube/Utilities"]
      
      common = templates + DSPlib + STlib + BSP + UT
      
      excluding = common
      
      FreeRTOS = ['"STCube/Middlewares/Third_Party/FreeRTOS']
      LwIPlib = ["STCube/Middlewares/Third_Party/LwIP"]
      FatFslib= ["STCube/Middlewares/Third_Party/FatFs"]
      
      Tasking = ["STCube/Middlewares/Third_Party/FreeRTOS/Source/portable/Tasking"]
      freertos = ["STCube/Src/freertos.c"]
      compilers = ["Middleware/Third_Party/FreeRTOS/Source/portable/IAR", "Middleware/Third_Party/FreeRTOS/Source/portable/Keil", "Middleware/Third_Party/FreeRTOS/Source/portable/RVDS"]
      if 'freertos' in self.components:
        FreeRTOSport = os.path.join(self.projectpath, LIBRARYNAME, 'Middlewares/Third_Party/FreeRTOS/Source/portable/GCC')
        MCUport = []
        for dirpath in os.listdir(FreeRTOSport):
          if not re.search(dirpath, 'ARM_CM' + self.GetCM(self.MCUp[1])):
            MCUport.append(os.path.join(LIBRARYNAME, 'Middlewares/Third_Party/FreeRTOS/Source/portable/GCC', dirpath))
            #       STCube/Middlewares/Third_Party/FreeRTOS/Source/portable/MemMang/heap_5.c
        excluding = excluding + Tasking + LwIPlib + FatFslib + compilers + MCUport + freertos
      else:
        excluding = excluding + LwIPlib + FatFslib + FreeRTOS
      return excluding

    def ProjectCleanExcludeSrc(self, componenttype='current'):
      if hasattr(self, 'previousundolibrary'):
        uexcluding = self.previousundolibrary.xpath('entry')
        mergeremove = uexcluding[0].get('excluding')
      else:
        mergeremove = ""
      entry = self.project.xpath('//storageModule/cconfiguration/storageModule[@moduleId="cdtBuildSystem"]/configuration/sourceEntries/entry[@excluding]')
      if componenttype == 'all':
#         FIXME even if wipe it doesn't pass from here
        for e in entry:
          e.getparent().remove(e)
      else:
        for e in entry:
          excluding = e.get('excluding')
          cleanexcluding = list(set(excluding.split('|')) - set(mergeremove.split('|')))
          if len(cleanexcluding)>0:
            e.attrib['excluding'] = '|'.join(cleanexcluding)
          else:
            e.getparent().remove(e)
    
    def ProjectAddExcludeSrc(self):
      newexcludinglist = self.GetExcludeSrc()
      mergeremove = []
      cfg = self.project.xpath('//storageModule/cconfiguration/storageModule[@moduleId="cdtBuildSystem"]/configuration')
      for c in cfg:
        src = c.xpath('.//sourceEntries')
        if len(src)<=0:
          src = etree.SubElement(c, 'sourceEntries')
        for s in src:
          entry = s.xpath('.//entry[@excluding]')
          if len(entry)<=0:
            entry =  etree.SubElement(s, 'entry', {'excluding': "|".join(newexcludinglist), 'flags': 'VALUE_WORKSPACE_PATH|RESOLVED', 'kind': 'sourcePath', 'name': ''})
          else:
            for e in entry:
              excluding = e.get('excluding')
              mergeexcluding = list(set(excluding.split('|')) | set(newexcludinglist))
              mergeremove = list(set(newexcludinglist) - set(excluding.split('|')))
              e.attrib['excluding'] = '|'.join(mergeexcluding)
      # undo
      etree.SubElement(self.undolibrary, 'entry', {'excluding': '|'.join(mergeremove)})

    def BinLibrariesScan(self):
      return BINLIBPATH

    def ProjectCleanBinLibPath(self, componenttype='current'):
      optionpath = '//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]/listOptionValue'
      uoptionpath = '//libbinpath/listOptionValue'
      self.ProjectClean(optionpath, uoptionpath, componenttype)

    def ProjectCleanBinLib(self, componenttype='current'):
      optionpath = '//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]/listOptionValue'
      uoptionpath = '//libbinpathlib/listOptionValue'
      self.ProjectClean(optionpath, uoptionpath, componenttype)

    def ProjectCleanBinLibraries(self, componenttype='current'):
      self.ProjectCleanBinLibPath(componenttype)
      self.ProjectCleanBinLib(componenttype)

    # FIXME if there is no previous option, id doesn't add libraries. I don't know how to get an "Eclipse id" from python
    def ProjectAddBinLibraries(self):
      libbinpaths = self.BinLibrariesScan()
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
      for lib in sections:
        for binlibpath in libbinpaths:
          etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath)})
      # undo
      ulibbinpath = etree.SubElement(self.undolibrary, 'libbinpath')
      for binlibpath in libbinpaths:
        etree.SubElement(ulibbinpath, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath)})
      libnames = []
      sections = self.project.xpath('//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]')
      for lib in sections:
        for binlibpath in libbinpaths:
          for f in glob.glob(os.path.join(self.cubelibrary, binlibpath) + '/*.a'):
            libname = os.path.splitext(os.path.basename(f))[0]
            libnames.append(libname)
            etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': libname})
      # undo
      ulibbinpathlib = etree.SubElement(self.undolibrary, 'libbinpathlib')
      for libname in libnames:
        etree.SubElement(ulibbinpathlib, 'listOptionValue', {'builtIn': "false", 'value': libname})

    def ProjectRemoveLD(self, componenttype='current'):
      if componenttype == 'all':
        for f in glob.glob(os.path.join(self.projectpath, 'ldscripts') + '/*.ld'):
          try:
            os.remove(f)
          except FileNotFoundError:
            pass
      elif componenttype == 'current':
        try:
          os.remove(os.path.join(self.projectpath, 'ldscripts', LDSCRIPT.format(self.MCU)))
        except FileNotFoundError:
          pass

    def ProjectCleanLD(self, componenttype='current'):
      optionpath = '//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]/listOptionValue'
      uoptionpath = '//ld/listOptionValue'
      self.ProjectClean(optionpath, uoptionpath, componenttype)
      self.ProjectRemoveLD(componenttype)

    def ProjectAddLD(self):
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]')
      for ld in sections:
        etree.SubElement(ld, 'listOptionValue', {'builtIn': "false", 'value': self.ldscript})
      shutil.copy2(self.ldscript, os.path.join(self.projectpath, 'ldscripts'))
      # undo
      uld = etree.SubElement(self.undolibrary, 'ld')
      etree.SubElement(uld, 'listOptionValue', {'builtIn': "false", 'value': self.ldscript})
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
      for ldlib in sections:
        etree.SubElement(ldlib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.projectpath, 'ldscripts')})
      # undo
      uldlib = etree.SubElement(self.undolibrary, 'ldlib')
      etree.SubElement(uldlib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.projectpath, 'ldscripts')})

    def ProjectImportStartup(self):
      startupfilesrc = os.path.join(self.cubelibrary, STARTUPPATH.format(self.MCUp[0], self.MCUp[1]),
                                 STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower(), 's'))
      startupfiledst = STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower(), 'S')
      shutil.copy2(startupfilesrc, os.path.join(self.projectpath, 'ldscripts', startupfiledst))
      # undo
      etree.SubElement(self.undolibrary, 'startup',
                       {'value': os.path.join(self.projectpath, 'ldscripts', startupfiledst)})

    def ProjectCleanDef(self, componenttype='current'):
      optionpath = '//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]/listOptionValue'
      uoptionpath = '//define/listOptionValue'
      self.ProjectClean(optionpath, uoptionpath, componenttype)

    def GetMathLib(self):
      # TODO ARM_MATH_CM0PLUS vs ARM_MATH_CM0
      return 'ARM_MATH_CM' + self.GetCM(self.MCUp[1])

    def ProjectAddDef(self):
      mathlib = self.GetMathLib()
      define = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]')
      definev = []
      definesrc = self.cubecprojectx.xpath('//option[@superClass="gnu.c.compiler.option.preprocessor.def.symbols" and @valueType="definedSymbols"]/listOptionValue')
      for sd in definesrc:
        definev.append(sd.attrib['value'])
      for d in define:
        for sd in definev:
          etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": sd})
        etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": mathlib})
      # undo
      udefine = etree.SubElement(self.undolibrary, 'define')
      for sd in definev:
        etree.SubElement(udefine, 'listOptionValue', {'builtin': 'false', "value": sd})
      etree.SubElement(udefine, 'listOptionValue', {'builtin': 'false', "value": mathlib})

    def rmtreeError(self, func, path, execinfo):
      print('{} deleting path {}'.format(execinfo[0].__name__, path), file=sys.stderr)

    def ProjectCleanSrcARM(self):
      shutil.rmtree(os.path.join(self.projectpath, 'src'), ignore_errors=False, onerror=self.rmtreeError)
      shutil.rmtree(os.path.join(self.projectpath, 'include'), ignore_errors=False, onerror=self.rmtreeError)
      shutil.rmtree(os.path.join(self.projectpath, 'system'), ignore_errors=False, onerror=self.rmtreeError)

    def ProjectCleanSrc(self):
      systemfile = os.path.join(self.projectpath, 'ldscripts', SYSTEMC.format(self.MCUp[0].lower(), self.MCUp[1].lower()))
      syscallsfile = os.path.join(self.projectpath, 'ldscripts', 'syscalls.c')
      try:
        os.remove(systemfile)
        os.remove(syscallsfile)
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME))
      except FileNotFoundError:
        pass

    # TODO ProjectAddSrc should accept a list of dirs
    # TODO ProjectAddSrc should be separated in Source + "special file" copy (system, startup, syscalls...)
    def ProjectAddSrc(self):
      # system file
      systemfile = os.path.join(self.cubelibrary, SYSTEMPATH.format(self.MCUp[0], self.MCUp[1]), SYSTEMC.format(self.MCUp[0].lower(), self.MCUp[1].lower()))
      shutil.copy2(systemfile, os.path.join(self.projectpath, 'ldscripts'))
      # undo
      etree.SubElement(self.undolibrary, 'system', {'value': os.path.join(self.projectpath, 'ldscripts', SYSTEMC.format(self.MCUp[0].lower(), self.MCUp[1].lower()))})
      # syscalls file
      syscallsfile = os.path.join(codepath, 'syscalls.c')
      shutil.copy2(syscallsfile, os.path.join(self.projectpath, 'ldscripts'))
      # undo
      etree.SubElement(self.undolibrary, 'syscalls', {'value': os.path.join(self.projectpath, 'syscalls.c')})
      # Library
      dst = os.path.join(self.projectpath, LIBRARYNAME)
      try:
        os.mkdir(dst, mode=0o770)
        os.symlink(os.path.join(self.cubelibrary, 'Drivers'), os.path.join(dst, 'Drivers'), target_is_directory=True)
        os.symlink(os.path.join(self.cubelibrary, 'Middlewares'), os.path.join(dst, 'Middlewares'), target_is_directory=True)
        os.symlink(os.path.join(self.cubelibrary, 'Utilities'), os.path.join(dst, 'Utilities'), target_is_directory=True)
      except FileExistsError:
        pass
      # undo
      symlink = etree.SubElement(self.undolibrary, 'symlink')
      etree.SubElement(symlink, 'listOptionValue', value=os.path.join(dst, 'Drivers'))
      etree.SubElement(symlink, 'listOptionValue', value=os.path.join(dst, 'Middlewares'))
      etree.SubElement(symlink, 'listOptionValue', value=os.path.join(dst, 'Utilities'))
      # Code
      try:
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME, 'Src'))
      except FileNotFoundError:
        pass
      shutil.copytree(os.path.join(self.cubeproject, 'Inc'), os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
      shutil.copytree(os.path.join(self.cubeproject, 'Src'), os.path.join(self.projectpath, LIBRARYNAME, 'Src'))
      # undo
      src = etree.SubElement(self.undolibrary, 'src')
      etree.SubElement(src, 'listOptionValue', value=os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
      etree.SubElement(src, 'listOptionValue', value=os.path.join(self.projectpath, LIBRARYNAME, 'Src'))
      
    def ProjectSourceMangle(self):
      if 'freertos' in self.components:
        with open(os.path.join(self.projectpath, LIBRARYNAME, 'Src/main.c'), 'r+') as f:
          oldmain = f.read()
          f.seek(0)
          newmain = re.sub('#include "cmsis_os.h"', '//#include "cmsis_os.h"', oldmain)
          newmain = re.sub('void MX_FREERTOS_Init\(void\);', '//void MX_FREERTOS_Init(void);', newmain)
          newmain = re.sub('MX_FREERTOS_Init\(\);', '//MX_FREERTOS_Init();', newmain)
          newmain = re.sub('osKernelStart\(\);', '//osKernelStart();', newmain)
          f.write(newmain)

#     /* queue to manage delays */
#     xQueuePhase = xQueueCreate((unsigned portBASE_TYPE)1, (unsigned portBASE_TYPE)sizeof(signed portCHAR));
#     /* mutex to manage status */
#     xStatusMutex = xSemaphoreCreateMutex();
#     xDateMutex = xSemaphoreCreateMutex();
#     xTaskCreate(
#       vI2CTask
#       ,  (const signed portCHAR *)"I2C"
#       ,  configMINIMAL_STACK_SIZE
#       ,  NULL
#       ,  I2C_PRIORITY
#       ,  &xI2CHandle );
#     vTaskSuspend(xThermostateHandle);
#     vTaskStartScheduler();

    def ProjectBackup(self):
      shutil.copy2(os.path.join(self.projectpath, '.cproject'), os.path.join(self.projectpath, '.cproject.bak'))

    def ProjectRemove(self):
      if self.wipe == True:
        wipe = 'all'
      else:
        wipe = 'current'

      self.ProjectBackup()
      self.ProjectCleanInclude(wipe)
      self.ProjectCleanDef(wipe)
      self.ProjectCleanLD(wipe)
      self.ProjectCleanBinLibraries(wipe)
      self.ProjectCleanSrcARM()
      self.ProjectCleanSrc()
      self.ProjectCleanExcludeSrc(wipe)
      self.ProjectPrint("./.cproject")
#       XXX should I remove undo section?

    def ProjectInstall(self):
      if self.wipe == True:
        wipe = 'all'
      else:
        wipe = 'current'

      self.ProjectBackup()
      self.ProjectCleanInclude(wipe)
      self.ProjectCleanDef(wipe)
      self.ProjectAddDef()
      self.ProjectAddInclude()
      self.ProjectCleanLD(wipe)
      self.ProjectAddLD()
      self.ProjectImportStartup()
      self.ProjectCleanBinLibraries(wipe)
      self.ProjectAddBinLibraries()
      self.ProjectCleanSrcARM()
      self.ProjectCleanSrc()
      self.ProjectAddSrc()
      self.ProjectAddExcludeSrc()
      self.ProjectSourceMangle()
      self.ProjectPrint("./.cproject")
      self.UndoSave()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description='Add Cube libraries to an Eclipse program and import macros from a CubeMX project',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--project',
                        dest='project',
                        required=True,
                        metavar='DIR',
                        help='project directory')
    parser.add_argument('-l', '--cubelibrary',
                        dest='cubelibrary',
                        default='/usr/local/src/STM32Cube_FW_F1_V1.3.0/',
                        metavar='DIR',
                        help='Cube Library directory')
    parser.add_argument('-c', '--cubeproject',
                        dest='cubeproject',
                        required=True,
                        metavar='DIR',
                        help='CubeMX project')
    parser.add_argument('-i', '--includecache',
                        dest='includecache',
                        metavar='FILE',
                        help='load or generate include cache file')
    parser.add_argument('-m', '--components',
                        dest='components',
                        metavar='COMPONENT,COMPONENT',
                        help='add components to build [FreeRTOS,...]')
    parser.add_argument('-r', '--refreshinclude',
                        dest='refresh',
                        action='store_true',
                        help='refresh include cache file')
    parser.add_argument('-w', '--wipe',
                        dest='wipe',
                        action='store_true',
                        help='wipe cproject')
    parser.add_argument('-a', '--action',
                        dest='action',
                        default='install',
                        metavar='ACTION',
                        help='install | remove')

    args = parser.parse_args()
    

    codepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'code')
    cube = cube2eclipse(args.cubeproject, args.cubelibrary, args.includecache, args.refresh, args.components)

    cube.ProjectLoad(args.project, args.wipe)
    if args.action == 'install':
      cube.ProjectInstall()
    elif args.action == 'remove':
      cube.ProjectRemove()
    else:
      sys.exit('Invalid action')
