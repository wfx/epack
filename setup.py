#!/usr/bin/env python

import os
import fnmatch
from distutils.core import setup, Command
from distutils.command.build import build
from distutils.dir_util import mkpath
from distutils.dep_util import newer
from distutils.log import warn, info, error
from distutils.file_util import copy_file


class build_i18n(Command):
    description = 'Compile all the po files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        linguas_file = os.path.join('data', 'locale', 'LINGUAS')
        for lang in open(linguas_file).read().split():
            po_file = os.path.join('data', 'locale', lang + '.po')
            mo_file = os.path.join('epack', 'locale', lang, 'LC_MESSAGES', 'epack.mo')
            mkpath(os.path.dirname(mo_file), verbose=False)
            if newer(po_file, mo_file):
                info('compiling po file: %s -> %s' % (po_file, mo_file))
                cmd = 'msgfmt -o %s -c %s' % (mo_file, po_file)
                os.system(cmd)


class update_po(Command):
   description = 'Prepare all i18n files and update them as needed'
   user_options = []

   def initialize_options(self):
      pass

   def finalize_options(self):
      pass

   def run(self):
      # build the string of all the source files to be translated
      sources = 'bin/epack'
      for dirpath, dirs, files in os.walk('epack'):
         for name in fnmatch.filter(files, '*.py'):
            sources += ' ' + os.path.join(dirpath, name)

      # create or update the reference pot file
      pot_file = os.path.join('data', 'locale', 'epack.pot')
      info('updating pot file: %s' % (pot_file))
      cmd = 'xgettext --language=Python --from-code=UTF-8 --force-po ' \
                     '--output=%s %s' % (pot_file, sources)
      os.system(cmd)

      # create or update all the .po files
      linguas_file = os.path.join('data', 'locale', 'LINGUAS')
      for lang in open(linguas_file).read().split():
         po_file = os.path.join('data', 'locale', lang + '.po')
         mo_file = os.path.join('epack', 'locale', lang, 'LC_MESSAGES', 'epack.mo')
         if os.path.exists(po_file):
            # update an existing po file
            info('updating po file: %s' % (po_file))
            cmd = 'msgmerge -N -U -q %s %s' % (po_file, pot_file)
            os.system(cmd)
         else:
            # create a new po file
            info('creating po file: %s' % (po_file))
            mkpath(os.path.dirname(po_file), verbose=False)
            copy_file(pot_file, po_file, verbose=False)


class Build(build):
   def run(self):
      self.run_command("build_i18n")
      build.run(self)


setup(
    name = 'epack',
    version = '0.1.0', # don't forget to change also in utils.py
    description = 'A simple tool to extract any archive file',
    license="GNU General Public License v3 (GPLv3)",
    author = 'Wolfgang Morawetz (wfx) & Davide Andreoli (davemds)',
    author_email = 'wolfgang.morawetz@gmail.com',
    url="https://github.com/wfx/epack",
    requires = ['efl', 'magic'],
    provides = ['epack'],
    packages = ['epack', 'epack.libarchive'],
    package_data = {
        'epack': ['data/*', 'locale/*/LC_MESSAGES/*.mo'],
    },
    scripts = ['bin/epack'],
    data_files = [
        ('share/applications', ['data/epack.desktop']),
        ('share/icons', ['data/epack.png']),
        ('share/icons/hicolor/24x24/apps', ['data/icons/24x24/epack.png']),
        ('share/icons/hicolor/32x32/apps', ['data/icons/32x32/epack.png']),
        ('share/icons/hicolor/64x64/apps', ['data/icons/64x64/epack.png']),
        ('share/icons/hicolor/128x128/apps', ['data/icons/128x128/epack.png']),
        ('share/icons/hicolor/256x256/apps', ['data/icons/256x256/epack.png']),
    ],
    cmdclass = {
        'build': Build,
        'build_i18n': build_i18n,
        'update_po': update_po,
    },
)
