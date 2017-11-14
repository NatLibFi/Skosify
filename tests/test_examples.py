# encoding=utf-8
import unittest
import pytest
import glob
import re
import os
import argparse
from rdflib import Graph
from skosify.skosify import Skosify, DEFAULT_OPTIONS

"""
#import os
#import sys
#from rdflib.namespace import RDF, SKOS, OWL, DCTERMS, Namespace
#from rdflib import URIRef, Literal, Graph
"""


def expect_rdf(expect, graph):
    """Check whether all triples of an expected graph are included in another graph."""
    for triple in expect:
        assert triple in graph


@pytest.mark.parametrize('infile', glob.glob('examples/*.in.*'))
def test_example(infile):
    outfile = re.sub('\.in\.([^.]+)$', r'.out.\1', infile)

    skosify = Skosify()

    options = argparse.Namespace(**DEFAULT_OPTIONS)
    voc = skosify.skosify([infile], None, {}, {}, {}, options)

    expect = Graph()
    if os.path.isfile(outfile):
        expect.parse(outfile, format='turtle')
    elif len(graph) > 0:
        graph.serialize(destination=outfile, format='turtle')

    expect_rdf(expect, voc)


if __name__ == '__main__':
    unittest.main()
