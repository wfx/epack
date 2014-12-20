#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'epack',
    version = '2014.12.7.050',
    description = 'A simple tool to extract any file with efm',
    license = "GNU GPL",
    author = 'Wolfgang Morawetz (wfx)',
    author_email = 'wolfgang.morawetz@gmail.com',
    requires = ['efl', 'magic'],
    provides = ['epack'],
    packages = ['epack', 'epack.libarchive'],
    scripts = ['bin/epack'],
    data_files = [
        ('share/applications', ['data/epack.desktop']),
        ('share/icons', ['data/epack.png']),
        ('share/icons/hicolor/24x24/apps', ['data/icons/24x24/epack.png']),
        ('share/icons/hicolor/32x32/apps', ['data/icons/32x32/epack.png']),
        ('share/icons/hicolor/64x64/apps', ['data/icons/64x64/epack.png']),
        ('share/icons/hicolor/128x128/apps', ['data/icons/128x128/epack.png']),
        ('share/icons/hicolor/256x256/apps', ['data/icons/256x256/epack.png']),
    ]
)
