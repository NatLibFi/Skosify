# -*- coding: utf-8 -*-
"""Checks/fixes are bundled in one namespace."""

import logging
import time
from rdflib.namespace import RDF, SKOS
from .rdftools.namespace import SKOSEXT
from .rdftools import localname


def _hierarchy_cycles_visit(rdf, node, parent, break_cycles, status):
    if status.get(node) is None:
        status[node] = 1  # entered
        for child in sorted(rdf.subjects(SKOS.broader, node)):
            _hierarchy_cycles_visit(
                rdf, child, node, break_cycles, status)
        status[node] = 2  # set this node as completed
    elif status.get(node) == 1:  # has been entered but not yet done
        if break_cycles:
            logging.info("Hierarchy cycle removed at %s -> %s",
                         localname(parent), localname(node))
            rdf.remove((node, SKOS.broader, parent))
            rdf.remove((node, SKOS.broaderTransitive, parent))
            rdf.remove((node, SKOSEXT.broaderGeneric, parent))
            rdf.remove((node, SKOSEXT.broaderPartitive, parent))
            rdf.remove((parent, SKOS.narrower, node))
            rdf.remove((parent, SKOS.narrowerTransitive, node))
        else:
            logging.info(
                "Hierarchy cycle detected at %s -> %s, "
                "but not removed because break_cycles is not active",
                localname(parent), localname(node))
    elif status.get(node) == 2:  # is completed already
        pass


def hierarchy_cycles(rdf, fix=False):
    """Check if the graph contains skos:broader cycles and optionally break these.

    :param Graph rdf: An rdflib.graph.Graph object.
    :param bool fix: Fix the problem by removing any skos:broader that overlaps
        with skos:broaderTransitive.
    """
    top_concepts = sorted(rdf.subject_objects(SKOS.hasTopConcept))
    status = {}
    for cs, root in top_concepts:
        _hierarchy_cycles_visit(
            rdf, root, None, fix, status=status)

    # double check that all concepts were actually visited in the search,
    # and visit remaining ones if necessary
    recheck_top_concepts = False
    for conc in sorted(rdf.subjects(RDF.type, SKOS.Concept)):
        if conc not in status:
            recheck_top_concepts = True
            _hierarchy_cycles_visit(
                rdf, conc, None, fix, status=status)
    return recheck_top_concepts


def disjoint_relations(rdf, fix=False):
    """Check if the graph contains concepts connected by both of the semantically
    disjoint semantic skos:related and skos:broaderTransitive (S27),
    and optionally remove the involved skos:related relations.

    :param Graph rdf: An rdflib.graph.Graph object.
    :param bool fix: Fix the problem by removing skos:related relations that
        overlap with skos:broaderTransitive.
    """
    for conc1, conc2 in sorted(rdf.subject_objects(SKOS.related)):
        if conc2 in sorted(rdf.transitive_objects(conc1, SKOS.broader)):
            if fix:
                logging.warning(
                    "Concepts %s and %s connected by both "
                    "skos:broaderTransitive and skos:related, "
                    "removing skos:related",
                    conc1, conc2)
                rdf.remove((conc1, SKOS.related, conc2))
                rdf.remove((conc2, SKOS.related, conc1))
            else:
                logging.warning(
                    "Concepts %s and %s connected by both "
                    "skos:broaderTransitive and skos:related, "
                    "but keeping it because keep_related is enabled",
                    conc1, conc2)


def hierarchical_redundancy(rdf, fix=False):
    """Check for and optionally remove extraneous skos:broader relations.

    :param Graph rdf: An rdflib.graph.Graph object.
    :param bool fix: Fix the problem by removing skos:broader relations between
        concepts that are otherwise connected by skos:broaderTransitive.
    """
    for conc, parent1 in rdf.subject_objects(SKOS.broader):
        for parent2 in rdf.objects(conc, SKOS.broader):
            if parent1 == parent2:
                continue  # must be different
            if parent2 in rdf.transitive_objects(parent1, SKOS.broader):
                if fix:
                    logging.warning(
                        "Eliminating redundant hierarchical relationship: "
                        "%s skos:broader %s",
                        conc, parent2)
                    rdf.remove((conc, SKOS.broader, parent2))
                    rdf.remove((conc, SKOS.broaderTransitive, parent2))
                    rdf.remove((parent2, SKOS.narrower, conc))
                    rdf.remove((parent2, SKOS.narrowerTransitive, conc))
                else:
                    logging.warning(
                        "Redundant hierarchical relationship "
                        "%s skos:broader %s found, but not eliminated "
                        "because eliminate_redundancy is not set",
                        conc, parent2)
