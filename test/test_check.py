# encoding=utf-8
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


def test_preflabel_uniqueness_is_deterministic():
    rdf = Graph()
    a = BNode()

    rdf.add((a, RDF.type, SKOS.Concept))
    # all English labels have the same length, tie must be broken
    rdf.add((a, SKOS.prefLabel, Literal('bab', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('bba', 'en')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aab', 'en')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('aba', 'en')))  # remove

    # ditto for Finnish labels
    rdf.add((a, SKOS.prefLabel, Literal('ba', 'fi')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('bb', 'fi')))  # remove
    rdf.add((a, SKOS.prefLabel, Literal('aa', 'fi')))  # keep
    rdf.add((a, SKOS.prefLabel, Literal('ab', 'fi')))  # remove

    len_before = len(rdf)

    skosify.check.preflabel_uniqueness(rdf, policy=['shortest'])
    assert len(rdf) == len_before
    assert (a, SKOS.prefLabel, Literal('aab', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('bab', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('bba', 'en')) in rdf
    assert (a, SKOS.altLabel, Literal('aba', 'en')) in rdf

    assert (a, SKOS.prefLabel, Literal('aa', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('ba', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('bb', 'fi')) in rdf
    assert (a, SKOS.altLabel, Literal('ab', 'fi')) in rdf
