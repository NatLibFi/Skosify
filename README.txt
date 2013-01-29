Skosify version 0.6

SKOS converter for RDFS/OWL/SKOS vocabularies

The program accepts a thesaurus-like vocabulary expressed as RDFS, OWL or
SKOS as input. It produces a clean SKOS representation, which attempts to
represent the input data losslessly using SKOS best practices. When given
SKOS as input, it will be cleaned up, validated and enriched to follow
the SKOS specification and related best practices.

Simple usage:

./skosify.py myontology.owl -o myontology-skos.rdf

For more usage information, try

./skosify.py --help


Additional documentation can be found in the Google Code wiki:
http://code.google.com/p/skosify/wiki/GettingStarted
