# -*- coding: utf-8 -*-
"""Checks/fixes are bundled in one namespace."""

import logging
from rdflib.namespace import RDF, SKOS
from .rdftools.namespace import SKOSEXT
from .rdftools import localname, find_prop_overlap


def _hierarchy_cycles_visit(rdf, node, parent, break_cycles, status):
    if status.get(node) is None:
        status[node] = 1  # entered
        for child in sorted(rdf.subjects(SKOS.broader, node)):
            _hierarchy_cycles_visit(
                rdf, child, node, break_cycles, status)
        status[node] = 2  # set this node as completed
    elif status.get(node) == 1:  # has been entered but not yet done
        if break_cycles:
            logging.warning("Hierarchy cycle removed at %s -> %s",
                            localname(parent), localname(node))
            rdf.remove((node, SKOS.broader, parent))
            rdf.remove((node, SKOS.broaderTransitive, parent))
            rdf.remove((node, SKOSEXT.broaderGeneric, parent))
            rdf.remove((node, SKOSEXT.broaderPartitive, parent))
            rdf.remove((parent, SKOS.narrower, node))
            rdf.remove((parent, SKOS.narrowerTransitive, node))
        else:
            logging.warning(
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
    for conc, parent1 in sorted(rdf.subject_objects(SKOS.broader)):
        for parent2 in sorted(rdf.objects(conc, SKOS.broader)):
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


def preflabel_uniqueness(rdf, policy='all'):
    """Check that concepts have no more than one value of skos:prefLabel per
    language tag (S14), and optionally move additional values to skos:altLabel.

    :param Graph rdf: An rdflib.graph.Graph object.
    :param str policy: Policy for deciding which value to keep as prefLabel
        when multiple prefLabels are found.  Possible values are 'shortest'
        (keep the shortest label), 'longest' (keep the longest label),
        'uppercase' (prefer uppercase), 'lowercase' (prefer uppercase) or
        'all' (keep all, just log the problems).  Alternatively, a list of
        policies to apply in order, such as ['shortest', 'lowercase'], may
        be used.
    """
    resources = set(
        (res for res, label in rdf.subject_objects(SKOS.prefLabel)))

    policy_fn = {
        'shortest': len,
        'longest': lambda x: -len(x),
        'uppercase': lambda x: int(x[0].islower()),
        'lowercase': lambda x: int(x[0].isupper())
    }

    if type(policy) not in (list, tuple):
        policies = policy.split(',')
    else:
        policies = policy

    for p in policies:
        if p not in policy_fn:
            logging.critical("Unknown preflabel-policy: %s", policy)
            return

    def key_fn(label):
        return [policy_fn[p](label) for p in policies] + [str(label)]

    for res in sorted(resources):
        prefLabels = {}
        for label in rdf.objects(res, SKOS.prefLabel):
            lang = label.language
            if lang not in prefLabels:
                prefLabels[lang] = []
            prefLabels[lang].append(label)
        for lang, labels in prefLabels.items():
            if len(labels) > 1:
                if policies[0] == 'all':
                    logging.warning(
                        "Resource %s has more than one prefLabel@%s, "
                        "but keeping all of them due to preflabel-policy=all.",
                        res, lang)
                    continue

                chosen = sorted(labels, key=key_fn)[0]

                logging.warning(
                    "Resource %s has more than one prefLabel@%s: "
                    "choosing %s (policy: %s)",
                    res, lang, chosen, str(policy))
                for label in labels:
                    if label != chosen:
                        rdf.remove((res, SKOS.prefLabel, label))
                        rdf.add((res, SKOS.altLabel, label))


def label_overlap(rdf, fix=False):
    """Check if concepts have the same value for any two of the pairwise
    disjoint properties skos:prefLabel, skos:altLabel and skos:hiddenLabel
    (S13), and optionally remove the least significant property.

    :param Graph rdf: An rdflib.graph.Graph object.
    :param bool fix: Fix the problem by removing the least significant property
        (altLabel or hiddenLabel).
    """
    def label_warning(res, label, keep, remove):
        if fix:
            logging.warning(
                "Resource %s has '%s'@%s as both %s and %s; removing %s",
                res, label, label.language, keep, remove, remove
            )
        else:
            logging.warning(
                "Resource %s has '%s'@%s as both %s and %s",
                res, label, label.language, keep, remove
            )

    for res, label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.altLabel):
        label_warning(res, label, 'prefLabel', 'altLabel')
        if fix:
            rdf.remove((res, SKOS.altLabel, label))
    for res, label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.hiddenLabel):
        label_warning(res, label, 'prefLabel', 'hiddenLabel')
        if fix:
            rdf.remove((res, SKOS.hiddenLabel, label))
    for res, label in find_prop_overlap(rdf, SKOS.altLabel, SKOS.hiddenLabel):
        label_warning(res, label, 'altLabel', 'hiddenLabel')
        if fix:
            rdf.remove((res, SKOS.hiddenLabel, label))
