# encoding=utf-8
import unittest
import pytest
import glob
import re
import os
import logging

from rdflib import Graph

import skosify


def expect_rdf(expect, graph):
    """Check whether all triples of an expected graph are included in another graph."""
    for triple in expect:
        assert triple in graph


@pytest.mark.parametrize('infile', glob.glob('examples/*.in.*'))
def test_example(infile):
    outfile = re.sub('\.in\.([^.]+)$', r'.out.\1', infile)
    conffile = re.sub('\.in\.[^.]+$', r'.cfg', infile)

    if os.path.isfile(conffile):
        config = skosify.config(conffile)
    else:
        config = {}

    voc = skosify.skosify(infile, **config)

    expect = Graph()
    if os.path.isfile(outfile):
        expect.parse(outfile, format='turtle')
    elif len(voc) > 0:
        logging.info("new example output: %s" % (outfile))
        voc.serialize(destination=outfile, format='turtle')

    expect_rdf(expect, voc)


def test_sources():
    infile = 'examples/milk.in.ttl'
    voc1 = skosify.skosify(infile)

    rdf = Graph()
    rdf = rdf.parse(infile, format='turtle')
    voc2 = skosify.skosify(rdf)

    expect_rdf(voc1, voc2)


if __name__ == '__main__':
    unittest.main()
