#!/usr/bin/env python
from distutils.core import setup
from efl.utils.setup import build_extra, build_i18n, build_fdo, uninstall


setup(
    name = 'epack',
    version = '0.1.0', # don't forget to change also in utils.py
    description = 'A simple tool to extract any archive file',
    license="GNU General Public License v3 (GPLv3)",
    author = 'Wolfgang Morawetz (wfx) & Davide Andreoli (davemds)',
    author_email = 'wolfgang.morawetz@gmail.com',
    url="https://github.com/wfx/epack",
    requires = ['efl (>= 1.13)'],
    provides = ['epack'],
    packages = ['epack', 'epack.libarchive'],
    scripts = ['bin/epack'],
    cmdclass = {
        'build': build_extra,
        'build_i18n': build_i18n,
        'build_fdo': build_fdo,
        'uninstall': uninstall,
    },
    command_options={
        'install': {'record': ('setup.py', 'installed_files.txt')}
    },
)
