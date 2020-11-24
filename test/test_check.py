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


def test_preflabel_uniqueness_longest():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('short', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('longer', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('short', 'nb')))  # keep

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy='longest')
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('short', 'nb')) in rdf
    assert (a, SKOS.prefLabel, Literal('longer', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('short', 'en')) in rdf


def test_preflabel_uniqueness_shortest_lowercase():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('short', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('Short', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('longer', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('Longer', 'en')))  # remove

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy=['shortest', 'lowercase'])
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('short', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Short', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('longer', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Longer', 'en')) in rdf


def test_preflabel_uniqueness_shortest_uppercase():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('short', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('Short', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('longer', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('Longer', 'en')))  # remove

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy=['shortest', 'uppercase'])
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('Short', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('short', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('longer', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Longer', 'en')) in rdf


def test_preflabel_uniqueness_alphanumeric():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('äaa', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('Äba', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aab', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aba', 'en')))  # remove

    rdf.add((a, SKOS.prefLabel, Literal('äa', 'fi')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('Äb', 'fi')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aä', 'fi')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('ab', 'fi')))  # keep

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy=['shortest'])
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('äaa', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Äba', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('aab', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('aba', 'en')) in rdf

    assert (a, SKOS.prefLabel, Literal('ab', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('äa', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('Äb', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('aä', 'fi')) in rdf


def test_preflabel_uniqueness_alphanumeric2():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    rdf.add((a, SKOS.prefLabel, Literal('AAa', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('Aaa', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aaa', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('Äää', 'en')))  # remove

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy=[])
    assert len(rdf) == len_before
    assert (a, SKOS.altLabel, Literal('AAa', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Aaa', 'en')) in rdf
    assert (a, SKOS.prefLabel, Literal('aaa', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('Äää', 'en')) in rdf
