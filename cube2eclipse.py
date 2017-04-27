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

# ${workspace_loc:/${ProjName}/STCube}

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

# TODO componenttype should be an Enum
# TODO consolidate the use of common path syscalls, systemfile etc...
# TODO set ilg.gnuarmeclipse.managedbuild.cross.option.optimization.lto to false for Debug
# TODO include libraries as ref in .project
# rather than copying/symlinking source in workspace, it is better to include libraries as ref into .project
# .project
# direct link
#   <linkedResources>
#     <link>
#       <name>olimex</name>
#       <type>2</type>
#       <location>/home/ivan/Documents/programming/embedded/stm32/olimex</location>
#     </link>
#   </linkedResources>
# link inside a real directory (pino exists, winstar is a link)
#   <linkedResources>
#     <link>
#       <name>pino/winstar</name>
#       <type>2</type>
#       <location>/home/ivan/Documents/programming/embedded/display/winstar</location>
#     </link>
#   </linkedResources>



# .cproject &quot;${workspace_loc:/${ProjName}/olimex}&quot;"/
# this has an impact also on how to gather includes

class cube2eclipse():
  """docstring"""
  MCUr = re.compile(MCURE)
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
  
  # FIXME I should clean project and cproject
  def ProjectClean(self, optionpath, uoptionpath, componenttype='current'):
    options = self.cproject.xpath(optionpath)
    if componenttype == 'all':
      self.CleanList(options)
    elif componenttype == 'current':
      if hasattr(self, 'previousundocproject'):
        uoptions = self.previousundocproject.xpath(uoptionpath)
        if len(uoptions) > 0:
          self.CleanListFiltered(options, uoptions[0])
  
  def TreePrint(self, tree, file):
    s = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")
    if file:
      with open(file, 'wb+') as f:
        f.write(s)
    else:
      print(s)
  
  def ProjectSave(self):
    self.TreePrint(self.cproject, os.path.join(self.projectpath, '.cproject'))
    self.TreePrint(self.project, os.path.join(self.projectpath, '.project'))
  
  def CubeProjectLoad(self):
    projectdir = os.path.normpath(self.cubeproject)
    projectname = os.path.basename(projectdir)
    self.eclipseproject = os.path.join(projectdir, STMDIR, projectname)
    cproject = os.path.join(self.eclipseproject, '.cproject')
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
    self.ldscript = LDSCRIPT.format(self.MCU)

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
    elif (code == '7'):
      cm = '7'
    else:
      pass
    return cm
  
  def LibraryIncludeGet(self):
    # TODO should include /portable/Tasking and other subdirs
    includes = ['"${workspace_loc:/${ProjName}/STCube/Inc}"']
    if 'freertos' in self.components:
      includes = includes + [os.path.join(self.cubelibrary, 'Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/', 'ARM_CM' + self.GetCM(self.MCUp[1]))]
    return includes
  
  def UndoSave(self):
    self.TreePrint(self.undo, os.path.join(self.projectpath, '.projectundo'))
  
  def UndoLoad(self):
    projectundo = os.path.join(self.projectpath, '.projectundo')
    if(os.path.isfile(projectundo)):
      self.previousprojectundo = projectundo
      self.previousundo = etree.parse(open(projectundo, 'r+'))
      previousundocproject = self.previousundo.xpath('//lib2eclipse/library[@name="{}"]/cproject'.format(LIBRARYNAME))
      if len(previousundocproject) > 0:
        self.previousundocproject = previousundocproject[0]
      previousundoproject = self.previousundo.xpath('//lib2eclipse/library[@name="{}"]/project'.format(LIBRARYNAME))
      if len(previousundoproject) > 0:
        self.previousundoproject = previousundoproject[0]
  
  def __init__(self, cubeproject, cubelibrary, includecache, components, options):
    self.components = components
    self.options = options
    self.cubeproject = os.path.expanduser(cubeproject)
    self.cubelibrary = os.path.expanduser(cubelibrary)
    self.includecache = includecache
    # TODO possibly collecting includes and GetExcludeSrc() could be done in the same context/pass
  
    self.USBDevice = ["STCube/Middlewares/ST/STM32_USB_Device_Library"]
    self.USBHost = ["STCube/Middlewares/ST/STM32_USB_Host_Library"]
    self.STemWin = ["STCube/Middlewares/ST/STemWin"]
  
    self.FreeRTOS = ["STCube/Middlewares/Third_Party/FreeRTOS"]
    self.LwIPlib = ["STCube/Middlewares/Third_Party/LwIP"]
    self.FatFslib = ["STCube/Middlewares/Third_Party/FatFs"]
  
    excluding = ['/Projects', '/DSP_Lib/Examples',
                    '/RTOS/Template',
                    '/FreeRTOS/Source/portable/'
                ]
  
    if not ('freertos' in self.components):
      excluding = excluding + self.FreeRTOS
  
    if not ('lwip' in self.components):
      excluding = excluding + self.LwIPlib
  
    if not ('fatfs' in self.components):
      excluding = excluding + self.FatFslib
  
    if not ('usbdevice' in self.components):
      excluding = excluding + self.USBDevice
  
    if not ('usbhost' in self.components):
      excluding = excluding + self.USBHost
  
    if not ('stemwin' in self.components):
      excluding = excluding + self.STemWin
  
    combined = "(?:" + ")|(?:".join(excluding) + ")"
    self.excludingR = re.compile(combined)
    self.CubeProjectLoad()
  
  def FillIncludes(self):
    if not self.includecache:
      self.includes = self.IncludeScan()
    else:
      if(os.path.isfile(self.includecache) and not self.refresh):
        self.includes = self.IncludeLoad()
      else:
        self.includes = self.IncludeScan()
        self.IncludeSave()
    self.includes.extend(self.LibraryIncludeGet())
  
  def ProjectLoad(self, project, wipe, refresh):
    project = os.path.expanduser(project)
    self.projectpath = project
    
    cproject = os.path.join(project, '.cproject')
    project = os.path.join(project, '.project')
    if not (os.path.isfile(cproject) and os.access(cproject, os.W_OK)):
      sys.exit("{} can't be opened for writing".format(cproject))
    if not (os.path.isfile(project) and os.access(project, os.W_OK)):
      sys.exit("{} can't be opened for writing".format(project))
    
    self.cproject = etree.parse(open(cproject, 'r+'))
    self.project = etree.parse(open(project, 'r+'))

    self.undo = etree.Element("lib2eclipse", {'version': __version__, 'URL': __url__})
#     self.undocproject = etree.SubElement(self.undo, 'library', name=LIBRARYNAME)
    self.undolibrary = etree.SubElement(self.undo, 'library', name=LIBRARYNAME)
    self.undocproject = etree.SubElement(self.undolibrary, 'cproject')
    self.undoproject = etree.SubElement(self.undolibrary, 'project')
    
    self.wipe = wipe
    self.refresh = refresh      
    self.UndoLoad()
  
  def IncludeScan(self):
    includes = []
    for dirpath, _, filenames in os.walk(os.path.join(self.projectpath, LIBRARYNAME), followlinks=True):
      for f in filenames:
        if (os.path.splitext(f)[1].lower() in HEADERS) and (not self.IncludeExclude(dirpath)):
          relpath = os.path.relpath(dirpath, self.projectpath)
# TODO cleanup debug print
#           print("p={} d={} r={} f={}".format(self.projectpath, dirpath, relpath, '&quot;${workspace_loc:/${ProjName}/' + relpath + '}&quot;'))
#           ${workspace_loc:/${ProjName}/olimex} &quot;zzz&quot;
          includes.append('"${workspace_loc:/${ProjName}/' + relpath + '}"')
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
    return re.search(self.excludingR, dirpath)
  
  def ProjectCleanInclude(self, componenttype='current'):
    optionpath = '//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue'
    uoptionpath = '//include/listOptionValue'
    self.ProjectClean(optionpath, uoptionpath, componenttype)
  
  def ProjectCleanIncludeList(self, alienlibraries):
    includes = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue')
    for i in includes:
      if i.attrib['value'].startswith(tuple(alienlibraries)):
        i.getparent().remove(i)
  
  def ProjectAddInclude(self):
    self.FillIncludes()
    includes = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]')
    for i in includes:
      for l in self.includes:
        etree.SubElement(i, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})
    # undo
    uinclude = etree.SubElement(self.undocproject, 'include')
    for l in self.includes:
        etree.SubElement(uinclude, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})
  
  def GetExcludeSrc(self):
    templates = ["STCube/Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_msp_template.c", "STCube/Drivers/CMSIS/Device/ST/STM32F1xx/Source/Templates", "STCube/Drivers/CMSIS/RTOS"]
    DSPlib = ["STCube/Drivers/CMSIS/DSP_Lib"]
    BSP = ["STCube/Drivers/BSP"]
  
    UT = ["STCube/Utilities"]
  
    common = templates + DSPlib + BSP + UT
  
    excluding = common
  
    freertos = ["STCube/Src/freertos.c"]
  
    if 'freertos' in self.components:
      FreeRTOSport = os.path.join(self.projectpath, LIBRARYNAME, 'Middlewares/Third_Party/FreeRTOS/Source/portable')
      basepath = os.path.join(self.projectpath)
      MCUport = []
      MemMag = []
      for dirpath, _, _ in os.walk(FreeRTOSport, followlinks=True):
        if not re.search('(?:GCC/ARM_CM' + self.GetCM(self.MCUp[1]) + '$)|(?:GCC$)|(?:portable$)|(?:MemMang)', dirpath):
          srcpath = os.path.relpath(dirpath, basepath)
          MCUport.append(srcpath)
      for o in (availableoptions - self.options):
        r = re.sub('(heap)([0-9])', r'\1_\2.c', o)
        e = srcpath = os.path.relpath(os.path.join(FreeRTOSport, 'MemMang', r), basepath)
        MemMag.append(e)
      excluding = excluding + MCUport + MemMag + freertos
    else:
      excluding = excluding + self.FreeRTOS
  
    if not ('lwip' in self.components):
      excluding = excluding + self.LwIPlib
  
    if not ('fatfs' in self.components):
      excluding = excluding + self.FatFslib
  
    if not ('usbdevice' in self.components):
      excluding = excluding + self.USBDevice
  
    if not ('usbhost' in self.components):
      excluding = excluding + self.USBHost
  
    if not ('stemwin' in self.components):
      excluding = excluding + self.STemWin
  
    return excluding
  
  def ProjectCleanExcludeSrc(self, componenttype='current'):
    if hasattr(self, 'previousundocproject'):
      uexcluding = self.previousundocproject.xpath('entry')
      mergeremove = uexcluding[0].get('excluding')
    else:
      mergeremove = ""
    entry = self.cproject.xpath('//storageModule/cconfiguration/storageModule[@moduleId="cdtBuildSystem"]/configuration/sourceEntries/entry[@excluding]')
    if componenttype == 'all':
      for e in entry:
        e.getparent().remove(e)
    else:
      for e in entry:
        excluding = e.get('excluding')
        cleanexcluding = list(set(excluding.split('|')) - set(mergeremove.split('|')))
        if len(cleanexcluding) > 0:
          e.attrib['excluding'] = '|'.join(cleanexcluding)
        else:
          e.getparent().remove(e)
  
  def ProjectAddExcludeSrc(self):
    newexcludinglist = self.GetExcludeSrc()
    mergeremove = []
    cfg = self.cproject.xpath('//storageModule/cconfiguration/storageModule[@moduleId="cdtBuildSystem"]/configuration')
  #       TODO add all heap excluding one, can't use .project it seems there are 2 (?)
    for c in cfg:
      src = c.xpath('.//sourceEntries')
      if len(src) <= 0:
        src = etree.SubElement(c, 'sourceEntries')
      for s in src:
        entry = s.xpath('.//entry[@excluding]')
        if len(entry) <= 0:
          entry = etree.SubElement(s, 'entry', {'excluding': "|".join(newexcludinglist), 'flags': 'VALUE_WORKSPACE_PATH|RESOLVED', 'kind': 'sourcePath', 'name': ''})
        else:
          for e in entry:
            excluding = e.get('excluding')
            mergeexcluding = list(set(excluding.split('|')) | set(newexcludinglist))
            mergeremove = list(set(newexcludinglist) - set(excluding.split('|')))
            e.attrib['excluding'] = '|'.join(mergeexcluding)
    # undo
    etree.SubElement(self.undocproject, 'entry', {'excluding': '|'.join(mergeremove)})
  
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
    sections = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
    for lib in sections:
      for binlibpath in libbinpaths:
        etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath)})
    # undo
    ulibbinpath = etree.SubElement(self.undocproject, 'libbinpath')
    for binlibpath in libbinpaths:
      etree.SubElement(ulibbinpath, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath)})
    libnames = []
    sections = self.cproject.xpath('//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]')
    for lib in sections:
      for binlibpath in libbinpaths:
        for f in glob.glob(os.path.join(self.cubelibrary, binlibpath) + '/*.a'):
          libname = os.path.splitext(os.path.basename(f))[0]
          libnames.append(libname)
          etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': libname})
    # undo
    ulibbinpathlib = etree.SubElement(self.undocproject, 'libbinpathlib')
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
    sections = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]')
    ldpath = '"${workspace_loc:/${ProjName}/ldscripts}"'
    ldscript = '"${workspace_loc:/${ProjName}/ldscripts/' + self.ldscript + '}"'
    for ld in sections:
      etree.SubElement(ld, 'listOptionValue', {'builtIn': "false", 'value': ldscript})
    shutil.copy2(os.path.join(self.eclipseproject, self.ldscript), os.path.join(self.projectpath, 'ldscripts'))
    # undo
    uld = etree.SubElement(self.undocproject, 'ld')
    etree.SubElement(uld, 'listOptionValue', {'builtIn': "false", 'value': ldscript})
    sections = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
    for ldlib in sections:
      etree.SubElement(ldlib, 'listOptionValue', {'builtIn': "false", 'value': ldpath})
    # undo
    uldlib = etree.SubElement(self.undocproject, 'ldlib')
    etree.SubElement(uldlib, 'listOptionValue', {'builtIn': "false", 'value': ldpath})
  
  def ProjectImportStartup(self):
    startupfilesrc = os.path.join(self.cubelibrary, STARTUPPATH.format(self.MCUp[0], self.MCUp[1]),
                               STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower(), 's'))
    startupfiledst = STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower(), 'S')
    shutil.copy2(startupfilesrc, os.path.join(self.projectpath, 'ldscripts', startupfiledst))
    # undo
    etree.SubElement(self.undocproject, 'startup',
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
    define = self.cproject.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]')
    definev = []
    definesrc = self.cubecprojectx.xpath('//option[@superClass="gnu.c.compiler.option.preprocessor.def.symbols" and @valueType="definedSymbols"]/listOptionValue')
    for sd in definesrc:
      definev.append(sd.attrib['value'])
    for d in define:
      for sd in definev:
        etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": sd})
      etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": mathlib})
    # undo
    udefine = etree.SubElement(self.undocproject, 'define')
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
    etree.SubElement(self.undocproject, 'system', {'value': os.path.join(self.projectpath, 'ldscripts', SYSTEMC.format(self.MCUp[0].lower(), self.MCUp[1].lower()))})
    # syscalls file
    syscallsfile = os.path.join(codepath, 'syscalls.c')
    shutil.copy2(syscallsfile, os.path.join(self.projectpath, 'ldscripts'))
    # undo
    etree.SubElement(self.undocproject, 'syscalls', {'value': os.path.join(self.projectpath, 'syscalls.c')})
    # Library
    dst = os.path.join(self.projectpath, LIBRARYNAME)
    try:
      os.mkdir(dst, mode=0o770)
#       projectroot = self.project.xpath('//projectDescription')
#       linkedres = self.project.xpath('//projectDescription/linkedResources')
#       if len(linkedres)<=0:
#         linkedres = etree.SubElement(projectroot[0], 'linkedResources')
#       else:
#         linkedres = linkedres[0]
#       links = ('Drivers', 'Middlewares', 'Utilities')
#       for l in links:
#         link = etree.SubElement(linkedres, 'link')
#         etree.SubElement(link, 'name').text=LIBRARYNAME + '/' + l
#         etree.SubElement(link, 'type').text='2'
#         etree.SubElement(link, 'location').text=os.path.join(self.cubelibrary, l)
# TODO add undo
      os.symlink(os.path.join(self.cubelibrary, 'Drivers'), os.path.join(dst, 'Drivers'), target_is_directory=True)
      os.symlink(os.path.join(self.cubelibrary, 'Middlewares'), os.path.join(dst, 'Middlewares'), target_is_directory=True)
      os.symlink(os.path.join(self.cubelibrary, 'Utilities'), os.path.join(dst, 'Utilities'), target_is_directory=True)
      if 'freertos' in self.components:
        CMSIS_RTOSorig = os.path.join(dst, 'Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS')
        if not os.path.isdir(CMSIS_RTOSorig):
          CMSIS_RTOSsrc = os.path.join(codepath, 'CMSIS_RTOS')
          shutil.copytree(CMSIS_RTOSsrc, os.path.join(self.projectpath, LIBRARYNAME, 'CMSIS_RTOS'))
    except FileExistsError:
      pass
    # undo
    symlink = etree.SubElement(self.undocproject, 'symlink')
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
    src = etree.SubElement(self.undocproject, 'src')
    etree.SubElement(src, 'listOptionValue', value=os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
    etree.SubElement(src, 'listOptionValue', value=os.path.join(self.projectpath, LIBRARYNAME, 'Src'))
  
  def CopyNoOverwrite(self, src, des):
    # avoiding TOCTTOU
    try:
      fd = os.open(des, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
      with os.fdopen(fd, "w") as df:
        with open(src, "r") as sf:
          # TODO find a way to copy file without TOCTTOU that preserve metadata
          shutil.copyfileobj(sf, df)
    except FileExistsError:
      pass
  
  def ProjectSourceMangle(self):
    if 'freertos' in self.components:
      with open(os.path.join(self.projectpath, LIBRARYNAME, 'Src/main.c'), 'r+') as f:
        oldmain = f.read()
        f.truncate(0)
        # cmsis_os.h is used in other libraries: STemWin and LwIP
        newmain = re.sub('#include "cmsis_os.h"', '#include "cmsis_os.h"\n#include "freertos_setup.h"', oldmain)
        newmain = re.sub('/* USER CODE BEGIN Includes */',
                         '''
#pragma GCC diagnostic push
                         
#pragma GCC diagnostic warning "-Wconversion"
#pragma GCC diagnostic warning "-Wpadded"
#pragma GCC diagnostic warning "-Wunused"
#pragma GCC diagnostic warning "-Wextra"

/* USER CODE BEGIN Includes */''', newmain)
        newmain = newmain + '\n#pragma GCC diagnostic pop\n'
        f.write(newmain)
      rtosc = os.path.join(codepath, "freertos_setup.c")
      self.CopyNoOverwrite(rtosc, os.path.join(self.projectpath, LIBRARYNAME, 'Src/freertos_setup.c'))
      rtosh = os.path.join(codepath, "freertos_setup.h")
      self.CopyNoOverwrite(rtosh, os.path.join(self.projectpath, LIBRARYNAME, 'Inc/freertos_setup.h'))
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
  # add code to set up interrupt:
  #   add an include for setup functions
  #   call setup function in /* USER CODE BEGIN 2 */
  # add code for
  
  
  def ProjectBackup(self):
    if not os.path.isfile(os.path.join(self.projectpath, '.cproject.bak')):
      shutil.copy2(os.path.join(self.projectpath, '.cproject'), os.path.join(self.projectpath, '.cproject.bak'))
    if not os.path.isfile(os.path.join(self.projectpath, '.project.bak')):
      shutil.copy2(os.path.join(self.projectpath, '.project'), os.path.join(self.projectpath, '.project.bak'))
  
  def ProjectWipe(self):
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
  
  def ProjectRemove(self):
    self.ProjectWipe()
    self.ProjectSave()
  #       XXX should I remove undo section?
  
  def ProjectInstall(self):
    self.ProjectWipe()
  
    self.ProjectImportStartup()
    self.ProjectAddLD()
    self.ProjectAddBinLibraries()
    self.ProjectAddSrc()
    self.ProjectSourceMangle()
    self.ProjectAddInclude()
    self.ProjectAddDef()
    self.ProjectAddExcludeSrc()

    self.ProjectSave()
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
    parser.add_argument('-o', '--options',
                        dest='options',
                        metavar='OPTION,OPTION',
                        help='various options')
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

    # TODO use argparse choices? beware of case
    availablecomponents = set(('freertos', 'usbdevice', 'usbhost', 'stemwin', 'fatfs', 'lwip'))
    if args.components:
      components = set(args.components.lower().split(','))
    else:
      components = set()
    if not components <= availablecomponents:
      sys.exit('There are no components named: {}'.format(', '.join(components - availablecomponents)))
    
    availableoptions = set(('heap1', 'heap2', 'heap3', 'heap4', 'heap5' ))
    if args.options:
      options = set(args.options.lower().split(','))
    else:
      options = set(('heap4',))
    if not options <= availableoptions:
      sys.exit('There are no options named: {}'.format(', '.join(options - availableoptions)))

    codepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'code')
    cube = cube2eclipse(args.cubeproject, args.cubelibrary, args.includecache, components, options)

    cube.ProjectLoad(args.project, args.wipe, args.refresh)
    if args.action == 'install':
      cube.ProjectInstall()
    elif args.action == 'remove':
      cube.ProjectRemove()
    else:
      sys.exit('Invalid action')
