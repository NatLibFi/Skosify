#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function
import os
import sys

try:
    from setuptools import setup
except ImportError:
    print("This package requires 'setuptools' to be installed.")
    sys.exit(1)

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(name='skosify',
      version='1.0.0',  # Use bumpversion to update
      description='SKOS converter for RDFS/OWL/SKOS vocabularies.',
      long_description=README,
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3'
      ],
      keywords='rdf skos',
      author='Osma Suominen',
      author_email='osma.suominen@tkk.fi',
      url='https://github.com/NatLibFi/Skosify',
      license='MIT',
      install_requires=['rdflib'],
      setup_requires=['rdflib', 'pytest-runner>=2.9'],
      tests_require=['pytest', 'pytest-pep8', 'pytest-cov'],
      packages=['skosify'],
      entry_points = {'console_scripts': ['skosify=skosify.cli:main']}
      )
