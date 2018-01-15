# encoding=utf-8
import unittest
import pytest
from rdflib import Graph, BNode
from rdflib.namespace import Namespace, RDF, RDFS, SKOS

import skosify


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


def test_skos_symmetric_mappings():
    rdf = Graph()
    a, b = BNode(), BNode()

    rdf.add((a, SKOS.exactMatch, b))
    rdf.add((a, SKOS.closeMatch, b))
    rdf.add((a, SKOS.relatedMatch, b))

    skosify.infer.skos_symmetric_mappings(rdf)

    assert (b, SKOS.exactMatch, a) in rdf
    assert (b, SKOS.closeMatch, a) in rdf
    assert (b, SKOS.relatedMatch, a) in rdf
    assert (a, SKOS.related, b) in rdf
    assert (b, SKOS.related, a) in rdf


def test_skos_symmetric_mappings_without_related():
    rdf = Graph()
    a, b = BNode(), BNode()

    rdf.add((a, SKOS.exactMatch, b))
    rdf.add((a, SKOS.closeMatch, b))
    rdf.add((a, SKOS.relatedMatch, b))

    skosify.infer.skos_symmetric_mappings(rdf, False)

    assert (b, SKOS.exactMatch, a) in rdf
    assert (b, SKOS.closeMatch, a) in rdf
    assert (b, SKOS.relatedMatch, a) in rdf
    assert (a, SKOS.related, b) not in rdf
    assert (b, SKOS.related, a) not in rdf


def test_skos_hierarchical_mappings():
    rdf = Graph()
    a, b, c = BNode(), BNode(), BNode()

    rdf.add((a, SKOS.broadMatch, b))
    rdf.add((a, SKOS.narrowMatch, c))

    skosify.infer.skos_hierarchical_mappings(rdf)

    assert (b, SKOS.narrowMatch, a) in rdf
    assert (c, SKOS.narrowMatch, a) not in rdf
    assert (c, SKOS.broadMatch, a) in rdf
    assert (b, SKOS.broadMatch, a) not in rdf

    assert (a, SKOS.broader, b) in rdf
    assert (a, SKOS.narrower, c) in rdf
    assert (c, SKOS.broader, a) in rdf
    assert (b, SKOS.narrower, a) in rdf


def test_skos_hierarchical_mappings_without_narrower():
    rdf = Graph()
    a, b, c = BNode(), BNode(), BNode()

    rdf.add((a, SKOS.broadMatch, b))
    rdf.add((a, SKOS.narrowMatch, c))

    skosify.infer.skos_hierarchical_mappings(rdf, False)

    assert (b, SKOS.narrowMatch, a) not in rdf
    assert (c, SKOS.narrowMatch, a) not in rdf
    assert (c, SKOS.broadMatch, a) in rdf
    assert (b, SKOS.broadMatch, a) not in rdf

    assert (a, SKOS.broader, b) in rdf
    assert (a, SKOS.narrower, c) not in rdf
    assert (c, SKOS.broader, a) in rdf
    assert (b, SKOS.narrower, a) not in rdf
