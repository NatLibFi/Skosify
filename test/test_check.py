# encoding=utf-8
import unittest
import pytest
from rdflib import Graph, BNode
from rdflib.namespace import RDF, SKOS

import skosify


def test_hierarchy_cycles():
    rdf = Graph()
    a, b = BNode(), BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((b, RDF.type, SKOS.Concept))

    rdf.add((a, SKOS.broader, b))
    rdf.add((b, SKOS.broader, a))

    len_before = len(rdf)

    skosify.check.hierarchy_cycles(rdf, fix=False)
    assert len(rdf) == len_before

    skosify.check.hierarchy_cycles(rdf, fix=True)
    assert len(rdf) == len_before - 1
    assert bool((a, SKOS.broader, b) in rdf) != bool((b, SKOS.broader, a) in rdf)


def test_disjoint_relations():
    rdf = Graph()
    a, b, c = BNode(), BNode(), BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((b, RDF.type, SKOS.Concept))
    rdf.add((c, RDF.type, SKOS.Concept))

    rdf.add((a, SKOS.broader, b))
    rdf.add((b, SKOS.broader, c))
    rdf.add((a, SKOS.related, c))

    len_before = len(rdf)

    skosify.check.disjoint_relations(rdf, fix=False)
    assert len(rdf) == len_before

    skosify.check.disjoint_relations(rdf, fix=True)
    assert len(rdf) == len_before - 1
    assert (a, SKOS.related, c) not in rdf


def test_hierarchical_redundancy():
    rdf = Graph()
    a, b, c = BNode(), BNode(), BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((b, RDF.type, SKOS.Concept))
    rdf.add((c, RDF.type, SKOS.Concept))

    rdf.add((a, SKOS.broader, b))
    rdf.add((b, SKOS.broader, c))
    rdf.add((a, SKOS.broader, c))

    len_before = len(rdf)

    skosify.check.hierarchical_redundancy(rdf, fix=False)
    assert len(rdf) == len_before

    skosify.check.hierarchical_redundancy(rdf, fix=True)
    assert len(rdf) == len_before - 1
    assert (a, SKOS.broader, c) not in rdf
