# encoding=utf-8
import unittest
import pytest
import glob
import re
import os
from rdflib import Graph
from skosify.skosify import Skosify


def expect_rdf(expect, graph):
    """Check whether all triples of an expected graph are included in another graph."""
    for triple in expect:
        assert triple in graph


@pytest.mark.parametrize('infile', glob.glob('examples/*.in.*'))
def test_example(infile):
    outfile = re.sub('\.in\.([^.]+)$', r'.out.\1', infile)
    conffile = re.sub('\.in\.[^.]+$', r'.cfg', infile)

    skosify = Skosify()
    voc = skosify.skosify(infile)

    expect = Graph()
    if os.path.isfile(outfile):
        expect.parse(outfile, format='turtle')
    elif len(graph) > 0:
        graph.serialize(destination=outfile, format='turtle')

    expect_rdf(expect, voc)


if __name__ == '__main__':
    unittest.main()
