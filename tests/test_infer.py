# encoding=utf-8
import unittest
import pytest
from rdflib import Graph, BNode, Namespace, RDF, RDFS

import skosify

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def test_skos_related():
    rdf = Graph()
    a, b = BNode(), BNode()

    rdf.add((a, SKOS.related, b))

    skosify.infer.skos_related(rdf)

    assert (b, SKOS.related, a) in rdf


def test_skos_hierarchical():
    rdf = Graph()
    a, b, c, d = BNode(), BNode(), BNode(), BNode()

    rdf.add((a, SKOS.broader, b))
    rdf.add((d, SKOS.narrower, c))

    skosify.infer.skos_hierarchical(rdf, False)

    assert (c, SKOS.broader, d) in rdf
    assert (d, SKOS.narrower, c) not in rdf
    assert (b, SKOS.narrower, a) not in rdf

    skosify.infer.skos_hierarchical(rdf)

    assert (d, SKOS.narrower, c) in rdf
    assert (b, SKOS.narrower, a) in rdf


def test_rdfs_classes():
    rdf = Graph()
    a, b, c, x = BNode(), BNode(), BNode(), BNode()

    rdf.add((a, RDFS.subClassOf, b))
    rdf.add((b, RDFS.subClassOf, c))
    rdf.add((x, RDF.type, a))

    skosify.infer.rdfs_classes(rdf)

    assert (x, RDF.type, b) in rdf
    assert (x, RDF.type, c) in rdf
