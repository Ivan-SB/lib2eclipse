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

STARTUP = "startup_stm32{}{}0{}x{}.s"
STARTUPPATH = "Drivers/CMSIS/Device/ST/STM32{}{}xx/Source/Templates/gcc"

class cube2eclipse():
    """docstring"""
    EXCLUDE = ('/Projects/', '/DSP_Lib/Examples/', '/RTOS/Template')
    EXCLUDEr = re.compile("|".join(EXCLUDE))
    MCUr = re.compile(MCURE)

# TODO componenttype should be an Enum

    def CleanList(self, xmllist):
      for e in xmllist:
        e.getparent().remove(e)

    def ProjectPrint(self, file):
      s = etree.tostring(self.project, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")
      if file:
        with open(file, 'wb+') as f:
          f.write(s)
      else:
        print(s)

    def ProjectSave(self):
      self.ProjectPrint(os.path.join(self.projectpath, '.cproject'))

    def CubeProjectLoad(self):
      projectdir = os.path.normpath(os.path.expanduser(self.cubeproject))
      projectname = os.path.basename(projectdir)
      eclipseproject = os.path.join(projectdir, STMDIR, projectname + ' Configuration')
      cproject = os.path.join(eclipseproject, '.cproject')
      if os.path.isfile(cproject) and os.access(cproject, os.R_OK):
        self.cubecproject = etree.parse(open(cproject, "r"))
      else:
        sys.exit("{} can't be opened for reading".format(cproject))
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
      options = self.cubecproject.xpath('//option[@name="Mcu" and @superClass="fr.ac6.managedbuild.option.gnu.cross.mcu"]')[0]
      self.MCU = options.attrib["value"]
      self.MCUp = re.match(self.MCUr, self.MCU).groups()

    def LibraryIncludeGet(self):
      return ('"${project_loc:/STCube/inc"',)

    def __init__(self, cubeproject, cubelibrary, includecache, refresh):
      self.cubeproject = cubeproject
      self.cubelibrary = cubelibrary
      self.includecache = includecache
      self.install = etree.Element("lib2eclipse", {'version': __version__, 'URL': __url__})
      if not self.includecache:
        self.includes = self.IncludeScan()
      else:
        if(os.path.isfile(self.includecache) and not refresh):
          self.includes = self.IncludeLoad()
        else:
          self.includes = self.IncludeScan()
          self.IncludeSave()
        self.includes.extend(self.LibraryIncludeGet())
      self.CubeProjectLoad()

    def ProjectLoad(self, project):
      cproject = os.path.join(project, '.cproject')
      if os.path.isfile(cproject) and os.access(cproject, os.W_OK):
        self.projectpath = project
        self.project = etree.parse(open(cproject, 'r+'))
      else:
        sys.exit("{} can't be opened for writing".format(cproject))

    def ProjectGetInfo(self):
      library = self.project.xpath('//storageModule[@moduleId="org.eclipse.cdt.core.settings"]/libraryManager/library[@name="{}"]'.format(LIBRARYNAME))
      if len(library):
        return library[0]
      else:
        return None

    def ProjectSetInfo(self):
      library = self.ProjectGetInfo()
      if library is not None:
        library.attrib['path'] = self.cubelibrary
        library.attrib['version'] = LIBRARYVERSION
        library.attrib['hash'] = LIBRARYHASH
      else:
        libraryManager = self.project.xpath('//storageModule[@moduleId="org.eclipse.cdt.core.settings"]/libraryManager')
        if not len(libraryManager):
          EclipseCDT = self.project.xpath('//storageModule[@moduleId="org.eclipse.cdt.core.settings"]')[0]
          libraryManager = (etree.SubElement(EclipseCDT, 'libraryManager', version="0.1"),)
        library = etree.Element('library',
                      {'name': LIBRARYNAME, 'path': self.cubelibrary, 'version': LIBRARYVERSION, 'hash': '0000'}
                      )
        libraryManager[0].append(library)

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
      if componenttype == 'all':
        includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue')
      elif componenttype == 'current':
        previouspath = self.ProjectGetInfo()['path'] if self.ProjectGetInfo()['path'] else self.cubelibrary
        includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue[starts-with(@value, "{}")]'.format(previouspath))
      self.CleanList(includes)

    def ProjectCleanIncludeList(self, alienlibraries):
      includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]/listOptionValue')
      for i in includes:
        if i.attrib['value'].startswith(tuple(alienlibraries)):
          i.getparent().remove(i)

    def ProjectAddInclude(self):
      uinclude = etree.SubElement(self.install, 'include')
      includes = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="includePath"]')
      for i in includes:
        for l in self.includes:
          etree.SubElement(i, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})
      # undo
      for l in self.includes:
          etree.SubElement(uinclude, 'listOptionValue', {'builtin': 'false', "value": '{}'.format(l)})

    def BinLibrariesScan(self):
      return BINLIBPATH

    def ProjectCleanBinLibraries(self, componenttype='current'):
      if componenttype == 'all':
        options = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]/listOptionValue')
        self.CleanList(options)
        options = self.project.xpath('//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]/listOptionValue')
        self.CleanList(options)
      elif componenttype == 'current':
        options = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]/listOptionValue[@library="{}"]'.format(LIBRARYNAME))
        self.CleanList(options)
        options = self.project.xpath('//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]/listOptionValue[@library="{}"]'.format(LIBRARYNAME))
        self.CleanList(options)

    # FIXME if there is no previous option, id doesn't add libraries. I don't know how to get an "Eclipse id" from python
    def ProjectAddBinLibraries(self):
      libbinpaths = self.BinLibrariesScan()
      ulibbinpath = etree.SubElement(self.install, 'libbinpath')
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
      for lib in sections:
        for binlibpath in libbinpaths:
          etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath), 'library': LIBRARYNAME})
      # undo
      for binlibpath in libbinpaths:
        etree.SubElement(ulibbinpath, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.cubelibrary, binlibpath)})
      ulibbinpathlib = etree.SubElement(self.install, 'libbinpathlib')
      libnames = []
      sections = self.project.xpath('//option[@superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.libs" and @valueType="libs"]')
      for lib in sections:
        for binlibpath in libbinpaths:
          for f in glob.glob(os.path.join(self.cubelibrary, binlibpath) + '/*.a'):
            libname = os.path.splitext(os.path.basename(f))[0]
            libnames.append(libname)
            etree.SubElement(lib, 'listOptionValue', {'builtIn': "false", 'value': libname, 'library': LIBRARYNAME})
      # undo
      for libname in libnames:
        etree.SubElement(ulibbinpathlib, 'listOptionValue', {'builtIn': "false", 'value': libname})

    def ProjectRemoveLD(self, componenttype='current'):
      if componenttype == 'all':
        for f in glob.glob(os.path.join(self.projectpath, 'ldscripts') + '/*.ld'):
          os.remove(f)
      elif componenttype == 'current':
        os.remove(os.path.join(self.projectpath, 'ldscripts', LDSCRIPT.format(self.MCU)))

    def ProjectCleanLD(self, componenttype='current'):
      if componenttype == 'all':
        options = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]/listOptionValue')
      elif componenttype == 'current':
        options = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]/listOptionValue[@library="{}"'.format(LIBRARYNAME))
      self.CleanList(options)
      self.ProjectRemoveLD(componenttype)

    def ProjectAddLD(self):
      uld = etree.SubElement(self.install, 'ld')
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="stringList"]')
      for ld in sections:
        etree.SubElement(ld, 'listOptionValue', {'builtIn': "false", 'value': self.ldscript, 'library': LIBRARYNAME})
      shutil.copy2(self.ldscript, os.path.join(self.projectpath, 'ldscripts'))
      # undo
      etree.SubElement(uld, 'listOptionValue', {'builtIn': "false", 'value': self.ldscript})
      uldlib = etree.SubElement(self.install, 'ldlib')
      sections = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="libPath"]')
      for ldlib in sections:
        etree.SubElement(ldlib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.projectpath, 'ldscripts'), 'library': LIBRARYNAME})
      # undo
      etree.SubElement(uldlib, 'listOptionValue', {'builtIn': "false", 'value': os.path.join(self.projectpath, 'ldscripts')})

    def ProjectImportStartup(self):
      startupfile = os.path.join(self.cubelibrary, STARTUPPATH.format(self.MCUp[0], self.MCUp[1]), STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower()))
      shutil.copy2(startupfile, os.path.join(self.projectpath, 'ldscripts'))
      # undo
      etree.SubElement(self.install, 'startup',
                       {'value': os.path.join(
                                              self.projectpath, 'ldscripts',
                                              STARTUP.format(self.MCUp[0].lower(), self.MCUp[1].lower(), self.MCUp[2].lower(), self.MCUp[4].lower())
                                              )})

    def ProjectCleanDef(self, componenttype='current'):
      if componenttype == 'all':
        define = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]/listOptionValue')
      elif componenttype == 'current':
        define = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]/listOptionValue[@library="{}"]'.format(LIBRARYNAME))
      self.CleanList(define)

    def GetMathLib(self):
      # TODO ARM_MATH_CM0PLUS vs ARM_MATH_CM0
      return 'ARM_MATH_CM' + self.MCUp[1]

    def ProjectAddDef(self):
      udefine = etree.SubElement(self.install, 'define')
      mathlib = self.GetMathLib()
      define = self.project.xpath('//option[starts-with(@superClass, "ilg.gnuarmeclipse.managedbuild.cross.option") and @valueType="definedSymbols"]')
      definev = []
      definesrc = self.cubecproject.xpath('//option[@superClass="gnu.c.compiler.option.preprocessor.def.symbols" and @valueType="definedSymbols"]/listOptionValue')
      for sd in definesrc:
        definev.append(sd.attrib['value'])
      for d in define:
        for sd in definev:
          etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": sd})
        etree.SubElement(d, 'listOptionValue', {'builtin': 'false', "value": mathlib})
      # undo
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
      try:
        os.remove(systemfile)
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME))
      except FileNotFoundError:
        pass

    def ProjectAddSrc(self):
      systemfile = os.path.join(self.cubelibrary, SYSTEMPATH.format(self.MCUp[0], self.MCUp[1]), SYSTEMC.format(self.MCUp[0].lower(), self.MCUp[1].lower()))
      shutil.copy2(systemfile, os.path.join(self.projectpath, 'ldscripts'))
      dst = os.path.join(self.projectpath, LIBRARYNAME)
      try:
        os.mkdir(dst, mode=0o777)
        os.symlink(os.path.join(self.cubelibrary, 'Drivers'), os.path.join(dst, 'Drivers'), target_is_directory=True)
        os.symlink(os.path.join(self.cubelibrary, 'Middlewares'), os.path.join(dst, 'Middlewares'), target_is_directory=True)
        os.symlink(os.path.join(self.cubelibrary, 'Utilities'), os.path.join(dst, 'Utilities'), target_is_directory=True)
      except FileExistsError:
        pass
      try:
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
        shutil.rmtree(os.path.join(self.projectpath, LIBRARYNAME, 'Src'))
      except FileNotFoundError:
        pass
      shutil.copytree(os.path.join(self.cubeproject, 'Inc'), os.path.join(self.projectpath, LIBRARYNAME, 'Inc'))
      shutil.copytree(os.path.join(self.cubeproject, 'Src'), os.path.join(self.projectpath, LIBRARYNAME, 'Src'))

    def ProjectRebase(self):
      self.ProjectCleanInclude('current')
      self.ProjectAddInclude()
      self.ProjectCleanSrc('current')
      self.ProjectAddSrc()
      pass

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
    parser.add_argument('-r', '--refreshinclude',
                        dest='refresh',
                        action='store_true',
                        help='refresh include cache file')

    args = parser.parse_args()

    cube = cube2eclipse(args.cubeproject, args.cubelibrary, args.includecache, args.refresh)

    cube.ProjectLoad(args.project)
    cube.ProjectGetInfo()
    cube.ProjectSetInfo()
    cube.ProjectCleanInclude('all')
    cube.ProjectCleanDef('all')
    cube.ProjectAddDef()
    cube.ProjectAddInclude()
    cube.ProjectCleanLD('all')
    cube.ProjectAddLD()
    cube.ProjectImportStartup()
    cube.ProjectCleanBinLibraries('current')
    cube.ProjectAddBinLibraries()
    cube.ProjectCleanSrcARM()
    cube.ProjectCleanSrc()

    cube.ProjectAddSrc()
#     cube.ProjectSave()
    cube.ProjectPrint("./.cproject")
    print(etree.tostring(cube.install, pretty_print=True))

