# -*- coding: utf-8 -*-
"""Read Skosify configuration file."""

import logging
import sys
import argparse
from rdflib import URIRef, Namespace, RDF, RDFS

# import for both Python 2 and Python 3
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser

# default namespaces to register in the graph
DEFAULT_NAMESPACES = {
    'rdf': RDF,
    'rdfs': RDFS,
    'owl': Namespace("http://www.w3.org/2002/07/owl#"),
    'skos': Namespace("http://www.w3.org/2004/02/skos/core#"),
    'dc': Namespace("http://purl.org/dc/elements/1.1/"),
    'dct': Namespace("http://purl.org/dc/terms/"),
    'xsd': Namespace("http://www.w3.org/2001/XMLSchema#"),
}


class Config(object):
    """Internal class to store and access configuration."""

    def __init__(self, filename=None):
        """Create a new config object and possibly read from config file."""

        # default options
        self.from_format = None
        self.mark_top_concepts = True
        self.narrower = True
        self.transitive = False
        self.enrich_mappings = True
        self.aggregates = False
        self.keep_related = False
        self.break_cycles = False
        self.eliminate_redundancy = False
        self.cleanup_classes = False
        self.cleanup_properties = False
        self.cleanup_unreachable = False
        self.namespace = None
        self.label = None
        self.set_modified = False
        self.default_language = None
        self.preflabel_policy = 'shortest'
        self.infer = False
        self.update_query = None
        self.construct_query = None

        # mappings
        self.types = {}
        self.literals = {}
        self.relations = {}

        # namespaces
        self.namespaces = DEFAULT_NAMESPACES

        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename):
        """Read configuration from file and update config object."""

        cfgparser = ConfigParser()

        # force case-sensitive handling of option names
        cfgparser.optionxform = str

        # complains if open failed
        with open(filename) as fp:
            cfgparser.readfp(fp)

        # parse namespaces from configuration file
        for prefix, uri in cfgparser.items('namespaces'):
            self.namespaces[prefix] = URIRef(uri)

        # parse types from configuration file
        for key, val in cfgparser.items('types'):
            self.types[expand_curielike(self.namespaces, key)] = \
                expand_mapping_target(self.namespaces, val)

        # parse literals from configuration file
        for key, val in cfgparser.items('literals'):
            self.literals[expand_curielike(self.namespaces, key)] = \
                expand_mapping_target(self.namespaces, val)

        # parse relations from configuration file
        for key, val in cfgparser.items('relations'):
            self.relations[expand_curielike(self.namespaces, key)] = \
                expand_mapping_target(self.namespaces, val)

        # parse options from configuration file
        for opt, val in cfgparser.items('options'):
            if not hasattr(self, opt) or opt in ['types', 'literals', 'relations', 'namespaces']:
                logging.warning('Ignoring unknown configuration option: %s', opt)
                continue
            if getattr(self, opt) in (True, False):  # is a Boolean option
                setattr(self, opt, cfgparser.getboolean('options', opt))
            else:
                setattr(self, opt, val)


def expand_curielike(namespaces, curie):
    """Expand a CURIE (or a CURIE-like string with a period instead of colon
    as separator) into URIRef. If the provided curie is not a CURIE, return it
    unchanged."""

    if curie == '':
        return None
    if sys.version < '3':  # Python 2 ConfigParser reads raw byte strings
        curie = curie.decode('UTF-8')  # ...make those into Unicode objects

    if curie.startswith('[') and curie.endswith(']'):
        # decode SafeCURIE
        curie = curie[1:-1]

    if ':' in curie:
        ns, localpart = curie.split(':', 1)
    elif '.' in curie:
        ns, localpart = curie.split('.', 1)
    else:
        return curie

    if ns in namespaces:
        return URIRef(namespaces[ns].term(localpart))
    else:
        logging.warning("Unknown namespace prefix %s", ns)
        return URIRef(curie)


def expand_mapping_target(namespaces, val):
    """Expand a mapping target, expressed as a comma-separated list of
    CURIE-like strings potentially prefixed with ^ to express inverse
    properties, into a list of (uri, inverse) tuples, where uri is a URIRef
    and inverse is a boolean."""

    vals = [v.strip() for v in val.split(',')]
    ret = []
    for v in vals:
        inverse = False
        if v.startswith('^'):
            inverse = True
            v = v[1:]
        ret.append((expand_curielike(namespaces, v), inverse))
    return ret
