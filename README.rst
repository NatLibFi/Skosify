.. image:: https://travis-ci.org/NatLibFi/Skosify.svg?branch=master
    :target: https://travis-ci.org/NatLibFi/Skosify
.. image:: https://codecov.io/gh/NatLibFi/Skosify/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/NatLibFi/Skosify

Python script for converting to `SKOS <http://www.w3.org/2004/02/skos/>`_.

This program accepts a thesaurus-like vocabulary expressed as RDFS, OWL or
SKOS as input. It produces a clean SKOS representation, which attempts to
represent the input data losslessly using SKOS best practices. When given
SKOS as input, it will be cleaned up, validated and enriched to follow
the SKOS specification and related best practices.

Usage
=====

.. code-block:: console

    ./skosify.py myontology.owl -o myontology-skos.rdf

Run ``./skosify.py --help`` for more usage information.

Additional documentation can be found `in the GitHub project wiki <https://github.com/NatLibFi/Skosify/wiki>`_
