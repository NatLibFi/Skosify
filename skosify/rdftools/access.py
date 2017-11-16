# -*- coding: utf-8 -*-
"""Generic RDF utility methods to extract data."""


def localname(uri):
    """Determine the presumable local name (after namespace) of an URI."""
    return uri.split('/')[-1].split('#')[-1]


def find_prop_overlap(rdf, prop1, prop2):
    """Generate (subject,object) pairs connected by two properties."""
    for s, o in sorted(rdf.subject_objects(prop1)):
        if (s, prop2, o) in rdf:
            yield (s, o)
