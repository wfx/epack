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
    scripts = ['bin/epack'],
    data_files = [
        ('share/applications', ['data/epack.desktop']),
        ('share/icons', ['data/epack.png']),
        ('share/icons/hicolor/256x256/apps', ['data/epack_256.png']),
    ]
)
