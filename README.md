![nuke_parser](docs/resources/logo.png?raw=true "nuke_parser")

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


The nuke_parser consists of two projects
* [parser](docs/parser.md) Nuke script (.nk) ascii parser to generate scene description.
* [nkview](docs/nkview.md) Standalone nuke node graph app to view nuke scripts.

### License

nuke_parser is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0), which is
a free, open-source, and detailed software license developed and maintained by the Apache Software Foundation.

Contents
========

- [Installing nuke_parser](#installing-nuke_parser)
  * [Requirements](#requirements)
  * [Install](#install)


Installing nuke_parser
======================

Requirements
------------

**nkview** requires [Python 3](https://www.python.org/), [PySide6](https://pypi.org/project/PySide6/) or [PySide2](https://pypi.org/project/PySide2/),
[networkx](https://pypi.org/project/networkx/), [pyside_setup_macro](https://github.com/maxWiklund/PysideSetupMacro) and 
[setuptools](https://github.com/pypa/setuptools)

### Install
```shell
git clone https://github.com/maxWiklund/nuke_parser.git
cd nuke_parser

# Install nk_parser
cd parser
pip install .
# or 
python setup.py install

# install nkview
cd nkview
pip install -r requirements.txt
pip install .
# or 
python setup.py install
```


## Demo
![](demo.gif)

### Note: 
Zoom in / out bug found on macOS [QTBUG-73033](https://bugreports.qt.io/browse/QTBUG-73033)