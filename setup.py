#!/usr/bin/env python
from __future__ import print_function

import os
import sys

try:
    from setuptools import setup
except ImportError:
    print("This package requires 'setuptools' to be installed.")
    sys.exit(1)

requirements = ['rdflib']

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

setup(name='skosify',
      version='1.0.0',
      description='SKOS converter for RDFS/OWL/SKOS vocabularies.',
      long_description=README,
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3'
      ],
      author='Osma Suominen',
      author_email='osma.suominen@tkk.fi',
      url='https://code.google.com/p/skosify/',
      license='MIT',
      install_requires=requirements,
      packages=['skosify'],
      entry_points = {'console_scripts': ['skosify=skosify.skosify:main',
                                          'sparqldump=skosify.sparqldump:main']}
      )