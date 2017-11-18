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

As command line script:

.. code-block:: console

    skosify myontology.owl -o myontology-skos.rdf --label "My Ontology"

Run ``skosify --help`` for more usage information.

As Python library:

.. code-block:: python

    import skosify  # contains two functions: skosify and config

    voc = skosify.skosify('myontology.owl', label='My Ontology')
    voc.serialize(destination='myontology-skos.rdf', format='xml')

    rdf = Graph()
    rdf.parse('myontology.owl')
    config = skosify.config('owl2skos.cfg')
    voc = skosify.skosify(rdf, **config)

The `skosify` function gets a list of RDF input files and/or Graphs, and named configuration settings.

Additional documentation can be found `in the GitHub project wiki <https://github.com/NatLibFi/Skosify/wiki>`_


Additional scripts
==================

The `scripts` directory contains two additional scripts to be used together with Skosify:

* `skosify.cgi` a web application to use Skosify
* `sparqldump.py` a command line client to download RDF via a SPARQL endpoint

