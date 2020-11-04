# -*- coding: utf-8 -*-
"""Generic RDF utility methods to parse and serialize RDF."""

import logging
import sys

from rdflib import Graph
from rdflib.util import guess_format


def read_rdf(sources, infmt):
    """Read a list of RDF files and/or RDF graphs. May raise an Exception."""
    rdf = Graph()

    for source in sources:
        if isinstance(source, Graph):
            for triple in source:
                rdf.add(triple)
            continue

        if source == '-':
            f = sys.stdin
        else:
            if sys.version_info[0] >= 3:
                # Python 3+ - force UTF-8
                f = open(source, 'r', encoding='utf-8-sig')
            else:
                f = open(source, 'r')

        if infmt:
            fmt = infmt
        else:
            # determine format based on file extension
            fmt = guess_format(source)
            if not fmt:
                fmt = 'xml'  # default

        if fmt == 'nt' and sys.version_info[0] >= 3:
            # Avoid using N-Triples parser on Python 3
            # due to rdflib issue https://github.com/RDFLib/rdflib/issues/1144
            # A workaround is to use N3 parser instead
            fmt = 'n3'

        logging.debug("Parsing input file %s (format: %s)", source, fmt)
        rdf.parse(f, format=fmt)

    return rdf


def write_rdf(rdf, filename, fmt):
    if filename == '-':
        # In Python 3 raw bytes must be written to stdout.buffer
        # This works in Python 2.7 as well
        out = sys.stdout.buffer
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
