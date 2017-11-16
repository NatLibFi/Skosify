# -*- coding: utf-8 -*-

from rdflib import RDF


def replace_subject(rdf, fromuri, touri):
    """Replace occurrences of fromuri as subject with touri in given model.

    If touri=None, will delete all occurrences of fromuri instead.
    If touri is a list or tuple of URIRefs, all values will be inserted.

    """
    if fromuri == touri:
        return
    for p, o in rdf.predicate_objects(fromuri):
        rdf.remove((fromuri, p, o))
        if touri is not None:
            if not isinstance(touri, (list, tuple)):
                touri = [touri]
            for uri in touri:
                rdf.add((uri, p, o))


def replace_predicate(rdf, fromuri, touri, subjecttypes=None, inverse=False):
    """Replace occurrences of fromuri as predicate with touri in given model.

    If touri=None, will delete all occurrences of fromuri instead.
    If touri is a list or tuple of URIRef, all values will be inserted. If
    touri is a list of (URIRef, boolean) tuples, the boolean value will be
    used to determine whether an inverse property is created (if True) or
    not (if False). If a subjecttypes sequence is given, modify only those
    triples where the subject is one of the provided types.

    """

    if fromuri == touri:
        return
    for s, o in rdf.subject_objects(fromuri):
        if subjecttypes is not None:
            typeok = False
            for t in subjecttypes:
                if (s, RDF.type, t) in rdf:
                    typeok = True
            if not typeok:
                continue
        rdf.remove((s, fromuri, o))
        if touri is not None:
            if not isinstance(touri, (list, tuple)):
                touri = [touri]
            for val in touri:
                if not isinstance(val, tuple):
                    val = (val, False)
                uri, inverse = val
                if uri is None:
                    continue
                if inverse:
                    rdf.add((o, uri, s))
                else:
                    rdf.add((s, uri, o))


def replace_object(rdf, fromuri, touri, predicate=None):
    """Replace all occurrences of fromuri as object with touri in the given
    model.

    If touri=None, will delete all occurrences of fromuri instead.
    If touri is a list or tuple of URIRef, all values will be inserted.
    If predicate is given, modify only triples with the given predicate.

    """
    if fromuri == touri:
        return
    for s, p in rdf.subject_predicates(fromuri):
        if predicate is not None and p != predicate:
            continue
        rdf.remove((s, p, fromuri))
        if touri is not None:
            if not isinstance(touri, (list, tuple)):
                touri = [touri]
            for uri in touri:
                rdf.add((s, p, uri))


def replace_uri(rdf, fromuri, touri):
    """Replace all occurrences of fromuri with touri in the given model.

    If touri is a list or tuple of URIRef, all values will be inserted.
    If touri=None, will delete all occurrences of fromuri instead.

    """
    replace_subject(rdf, fromuri, touri)
    replace_predicate(rdf, fromuri, touri)
    replace_object(rdf, fromuri, touri)


def delete_uri(rdf, uri):
    """Delete all occurrences of uri in the given model."""
    replace_uri(rdf, uri, None)
