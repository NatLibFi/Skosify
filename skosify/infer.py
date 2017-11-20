# -*- coding: utf-8 -*-
"""Inference rules are bundled in one namespace."""

import logging
from rdflib import Namespace, RDF, RDFS

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def skos_related(rdf):
    """Make sure that skos:related is stated in both directions (S23)."""
    for s, o in rdf.subject_objects(SKOS.related):
        rdf.add((o, SKOS.related, s))


def skos_topConcept(rdf):
    """Infer skos:topConceptOf/skos:hasTopConcept (S8) and skos:inScheme (S7)."""
    for s, o in rdf.subject_objects(SKOS.hasTopConcept):
        rdf.add((o, SKOS.topConceptOf, s))
    for s, o in rdf.subject_objects(SKOS.topConceptOf):
        rdf.add((o, SKOS.hasTopConcept, s))
    for s, o in rdf.subject_objects(SKOS.topConceptOf):
        rdf.add((s, SKOS.inScheme, o))


def skos_hierarchical(rdf, narrower=True):
    """Infer skos:broader/skos:narrower (S25) but only keep skos:narrower on request."""
    if narrower:
        for s, o in rdf.subject_objects(SKOS.broader):
            rdf.add((o, SKOS.narrower, s))
    for s, o in rdf.subject_objects(SKOS.narrower):
        rdf.add((o, SKOS.broader, s))
        if not narrower:
            rdf.remove((s, SKOS.narrower, o))


def skos_transitive(rdf, narrower=True):
    """Perform transitive closure inference (S22, S24)."""
    for conc in rdf.subjects(RDF.type, SKOS.Concept):
        for bt in rdf.transitive_objects(conc, SKOS.broader):
            if bt == conc:
                continue
            rdf.add((conc, SKOS.broaderTransitive, bt))
            if narrower:
                rdf.add((bt, SKOS.narrowerTransitive, conc))


def rdfs_classes(rdf):
    """Perform RDFS subclass inference.

    Mark all resources with a subclass type with the upper class."""

    # find out the subclass mappings
    upperclasses = {}  # key: class val: set([superclass1, superclass2..])
    for s, o in rdf.subject_objects(RDFS.subClassOf):
        upperclasses.setdefault(s, set())
        for uc in rdf.transitive_objects(s, RDFS.subClassOf):
            if uc != s:
                upperclasses[s].add(uc)

    # set the superclass type information for subclass instances
    for s, ucs in upperclasses.items():
        logging.debug("setting superclass types: %s -> %s", s, str(ucs))
        for res in rdf.subjects(RDF.type, s):
            for uc in ucs:
                rdf.add((res, RDF.type, uc))


def rdfs_properties(rdf):
    """Perform RDFS subproperty inference.

    Add superproperties where subproperties have been used."""

    # find out the subproperty mappings
    superprops = {}  # key: property val: set([superprop1, superprop2..])
    for s, o in rdf.subject_objects(RDFS.subPropertyOf):
        superprops.setdefault(s, set())
        for sp in rdf.transitive_objects(s, RDFS.subPropertyOf):
            if sp != s:
                superprops[s].add(sp)

    # add the superproperty relationships
    for p, sps in superprops.items():
        logging.debug("setting superproperties: %s -> %s", p, str(sps))
        for s, o in rdf.subject_objects(p):
            for sp in sps:
                rdf.add((s, sp, o))
