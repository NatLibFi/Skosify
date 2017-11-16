# -*- coding: utf-8 -*-
"""Generic RDF utility methods to parse and serialize RDF."""

import logging
import sys

from rdflib import Graph


def read_rdf(filenames, infmt):
    """Read the given RDF file(s) and return an rdflib Graph object or raise an Exception."""
    rdf = Graph()

    for filename in filenames:
        if filename == '-':
            f = sys.stdin
        else:
            f = open(filename, 'r')

        if infmt:
            fmt = infmt
        else:
            # determine format based on file extension
            fmt = 'xml'  # default
            if filename.endswith('n3'):
                fmt = 'n3'
            if filename.endswith('ttl'):
                fmt = 'n3'
            if filename.endswith('nt'):
                fmt = 'nt'

        logging.debug("Parsing input file %s (format: %s)", filename, fmt)
        rdf.parse(f, format=fmt)

    return rdf


def write_rdf(rdf, filename, fmt):
    if filename == '-':
        out = sys.stdout
    else:
        out = open(filename, 'wb')

    if not fmt:
        # determine output format
        fmt = 'xml'  # default
        if filename.endswith('n3'):
            fmt = 'n3'
        if filename.endswith('nt'):
            fmt = 'nt'
        if filename.endswith('ttl'):
            fmt = 'turtle'

    logging.debug("Writing output file %s (format: %s)", filename, fmt)
    rdf.serialize(destination=out, format=fmt)
