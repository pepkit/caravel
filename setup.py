#! /usr/bin/env python

from setuptools import setup
import sys

PACKAGE = "caravel"

# Additional keyword arguments for setup().
extra = {}

# Ordinary dependencies
DEPENDENCIES = []
with open("caravel/requirements/requirements-all.txt", 'r') as reqs_file:
    for line in reqs_file:
        if not line.strip():
            continue
        DEPENDENCIES.append(line)

# 2to3
if sys.version_info >= (3, ):
    extra["use_2to3"] = True
extra["install_requires"] = DEPENDENCIES


with open("{}/_version.py".format(PACKAGE), 'r') as versionfile:
    version = versionfile.readline().split()[-1].strip("\"'\n")

# Handle the pypi README formatting.
try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except(IOError, ImportError, OSError, RuntimeError):
    long_description = open('README.md').read()

setup(
    name=PACKAGE,
    packages=[PACKAGE],
    version=version,
    description="Caravel provides aweb interface to interact with your "
    " PEP-formatted projects. Caravel lets you submit jobs to any cluster resource manager,"
    " monitor jobs, summarize results, and browse project summary web pages.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
    keywords="project, bioinformatics, sequencing, ngs, workflow, GUI",
    url="https://{}.databio.org/".format(PACKAGE),
    author=u"Nathan Sheffield, Vince Reuter, Michal Stolarczyk",
    license="BSD2",
    entry_points={
        "console_scripts": [
            "{p} = {p}.{p}:main".format(p=PACKAGE)
        ],
    },
    package_data={PACKAGE: ['templates/*', 'requirements/*']},
    include_package_data=True,
    **extra
)
