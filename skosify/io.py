# -*- coding: utf-8 -*-
"""RDF reading and writing methods."""

import logging
import sys

from rdflib import Graph


def read_rdf(filenames, infmt):
    """Read the given RDF file(s) and return an rdflib Graph object or None or error."""
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
        try:
            rdf.parse(f, format=fmt)
        except:
            logging.critical("Parsing failed. Exception: %s",
                             str(sys.exc_info()[1]))
            return None
            sys.exit(1)

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
