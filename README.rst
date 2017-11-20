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

The `skosify` function gets a list of RDF input files and/or Graphs, and named configuration settings.

Additional documentation can be found `in the GitHub project wiki <https://github.com/NatLibFi/Skosify/wiki>`_


Additional scripts
==================

The `scripts` directory contains two additional scripts to be used together with Skosify:

* `skosify.cgi` a web application to use Skosify
* `sparqldump.py` a command line client to download RDF via a SPARQL endpoint

See also
========

Author and Contributors
-----------------------

-  Osma Suominen
-  Jakob Voß
-  Dan Michael O. Heggø
-  Sini Pessala

Related works
-------------

-  `mc2skos <https://github.com/scriptotek/mc2skos>`__ can convert
   MARC21 Classification and Authority records to SKOS

Publications
------------

-  Osma Suominen and Christian Mader: Assessing and Improving the
   Quality of SKOS Vocabularies. Journal on Data Semantics, vol. 3, no.
   1, pp. 47-73, June, 2014
   (`PDF <https://seco.cs.aalto.fi/publications/2014/suominen-mader-skosquality.pdf>`__)

-  Osma Suominen and Eero Hyvönen: Improving the Quality of SKOS
   Vocabularies with Skosify. Proceedings of the 18th International
   Conference on Knowledge Engineering and Knowledge Management (EKAW
   2012), Springer-Verlag, Galway, Ireland, October, 2012
   (`PDF <https://seco.cs.aalto.fi/publications/2012/suominen-hyvonen-skosify-2012.pdf>`__)
