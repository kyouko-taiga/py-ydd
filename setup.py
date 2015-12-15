#!/usr/bin/env python

# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import os

from setuptools import Extension, find_packages, setup
from codecs import open


# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), 'r', encoding='utf-8').read()


# Set `ext_modules` to `[]` if you don't want to build the C++ extensions.
ext_modules = [
    Extension(
        'ydd.engines._cpp',
        ['src/wrapper.cpp'],
        libraries=['boost_python'],
        extra_compile_args=['-std=c++11']
    )
]


setup(
    name="py-ydd",
    version="0.1.0",
    author="Dimitri Racordon",
    author_email="dimitri.racordon@unige.ch",
    description=("A library to use YaDDs with Python."),
    long_description=read('README.md'),
    license="Apache 2.0",
    keywords="ydd, yadd",
    url="https://github.com/kyouko-taiga/py-ydd",
    packages=find_packages(),
    ext_modules=ext_modules,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
    ],
    extras_require={}
)
