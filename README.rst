.. image:: https://badge.fury.io/py/skosify.svg
   :target: https://badge.fury.io/py/skosify.svg    
.. image:: https://travis-ci.org/NatLibFi/Skosify.svg?branch=master
   :target: https://travis-ci.org/NatLibFi/Skosify
.. image:: https://readthedocs.org/projects/skosify/badge/?version=latest
   :target: http://skosify.rtfd.io/ 
.. image:: https://codecov.io/gh/NatLibFi/Skosify/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/NatLibFi/Skosify

Python script for converting to `SKOS <http://www.w3.org/2004/02/skos/>`_.

This program accepts a thesaurus-like vocabulary expressed as RDFS, OWL or
SKOS as input. It produces a clean SKOS representation, which attempts to
represent the input data losslessly using SKOS best practices. When given
SKOS as input, it will be cleaned up, validated and enriched to follow
the SKOS specification and related best practices.

Installation
============

Skosify requires Python 3.6+.

.. code-block:: console

    pip install --upgrade skosify

Usage
=====

As command line script:

.. code-block:: console

    skosify myvoc.owl -o myvoc-skos.ttl --label "My Ontology"

This will read the file ``myvoc.owl`` in RDF/XML format and write SKOS file ``myvoc-skos.ttl`` in Turtle format, setting the name of the Concept Scheme to ``My Ontology``.

Run ``skosify --help`` for more usage information.

As Python library:

.. code-block:: python

    import skosify  # contains skosify, config, and infer

    voc = skosify.skosify('myontology.owl', label='My Ontology')
    voc.serialize(destination='myontology-skos.rdf', format='xml')

    rdf = Graph()
    rdf.parse('myontology.owl')
    config = skosify.config('owl2skos.cfg')
    voc = skosify.skosify(rdf, **config)

    skosify.infer.skos_related(rdf)
    skosify.infer.skos_topConcept(rdf):
    skosify.infer.skos_hierarchical(rdf, narrower=True)
    skosify.infer.skos_transitive(rdf, narrower=True)

    skosify.infer.rdfs_classes(rdf)
    skosify.infer.rdfs_properties(rdf)

See `the API Reference <http://skosify.readthedocs.io/en/latest/api.html>`_ for documentation of the public API of this module. Everything not listed there might change in a future version.

Additional documentation can be found `in the GitHub project wiki <https://github.com/NatLibFi/Skosify/wiki>`_


Additional scripts
==================

The `scripts` directory contains two additional scripts to be used together with Skosify:

* `skosify.cgi` a web application to use Skosify
* `sparqldump.py` a command line client to download RDF via a SPARQL endpoint

Author and Contributors
=======================

-  Osma Suominen
-  Jakob Voß
-  Dan Michael O. Heggø
-  Alex Kourijoki

See also
========

See `background` for history, related works, publications etc.

.. background: docs/background.rst


