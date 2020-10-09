# encoding=utf-8
import unittest
import pytest
from rdflib import Graph, BNode, Literal
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


def test_label_overlap():
    rdf = Graph()
    a, b = BNode(), BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((b, RDF.type, SKOS.Concept))

    rdf.add((a, SKOS.prefLabel, Literal('Earth', 'en')))  # keep
    rdf.add((b, SKOS.altLabel, Literal('Earth', 'en')))  # keep
    rdf.add((a, SKOS.altLabel, Literal('Earth', 'en')))  # remove
    rdf.add((a, SKOS.hiddenLabel, Literal('Earth', 'en')))  # remove

    len_before = len(rdf)

    skosify.check.label_overlap(rdf, fix=False)
    assert len(rdf) == len_before

    skosify.check.label_overlap(rdf, fix=True)
    assert len(rdf) == len_before - 2
    assert (a, SKOS.prefLabel, Literal('Earth', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Earth', 'en')) not in rdf
    assert (a, SKOS.hiddenLabel, Literal('Earth', 'en')) not in rdf


def test_preflabel_uniqueness():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('short', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('longer', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('short', 'nb')))  # keep

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy='all')
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('longer', 'en')) in rdf

    skosify.check.preflabel_uniqueness(rdf, policy='shortest')
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('short', 'en')) in rdf
    assert (a, SKOS.prefLabel, Literal('short', 'nb')) in rdf
    assert (a, SKOS.altLabel, Literal('longer', 'en')) in rdf
