![icon](https://github.com/wfx/epack/blob/master/data/epack.png) epack
=====

epack is a tiny file extractor

![Screenshot](https://github.com/wfx/epack/blob/master/data/screenshot.jpg)


## Requirements ##

* Python 2.7 or higher
* python-efl >= 1.11
* python-magic
* Libarchive


## Installation ##

* For system-wide installation (needs administrator privileges):

 `(sudo) python setup.py install --record files.txt`

* Install in a custom location:

 `python setup.py install --prefix=/MY_PREFIX`

## Uninstall ##

* For system.wide deinstallation (need administrator privileges):

 `(sudo) cat files.txt | xargs rm -rf`

## Translations ##

To add a new language just add it's code (ex: "it" or "en") to the LINGUAS
file present in the data/locale folder of the sources and run:

`python setup.py update_po`

to generate the new empty po file under data/locale/your_code.po, you
can now edit this file to fill your translation. Don't forget to fill the
header informations, at least charset (usually UTF-8) and Plural-Forms.

