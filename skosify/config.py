# -*- coding: utf-8 -*-
"""Store skosify configuration and read config file."""

import logging
from io import StringIO
from copy import copy
from rdflib.namespace import URIRef, Namespace, RDF, RDFS, OWL, SKOS, DC, DCTERMS, XSD

from configparser import ConfigParser

# default namespaces to register in the graph
DEFAULT_NAMESPACES = {
    'rdf': RDF,
    'rdfs': RDFS,
    'owl': OWL,
    'skos': SKOS,
    'dc': DC,
    'dct': DCTERMS,
    'xsd': XSD,
}

DEFAULT_SECTIONS = u"""
[namespaces]

[types]

[literals]

[relations]

[options]

"""


def config(file=None):
    """Get default configuration and optional settings from config file.

    - file: can be a filename or a file object
    """
    return vars(Config(file))


class Config(object):
    """Internal class to store and access configuration."""

    def __init__(self, file=None):
        """Create a new config object and read from config file if given."""

        # default options
        self.from_format = None
        self.to_format = None
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
        self.post_update_query = None

        # mappings
        self.types = {}
        self.literals = {}
        self.relations = {}

        # namespaces
        self.namespaces = copy(DEFAULT_NAMESPACES)

        if file is not None:
            self.read_and_parse_config_file(file)

    def read_and_parse_config_file(self, file):
        cfgparser = ConfigParser()
        # force case-sensitive handling of option names
        cfgparser.optionxform = lambda x: x
        # Add empty defaults to avoid NoSectionError if some sections are missing
        with StringIO(DEFAULT_SECTIONS) as defaults_fp:
            self.read_file(cfgparser, defaults_fp)
        # Then read the config file
        self.read_file(cfgparser, file)
        self.parse_config(cfgparser)

    def read_file(self, cfgparser, file):
        """Read configuration from file."""

        if hasattr(file, 'readline'):
            # we have a file object
            cfgparser.read_file(file)
        else:
            # we have a file name
            cfgparser.read(file)

    def parse_config(self, cfgparser):

        # parse namespaces from configuration file
        for prefix, uri in cfgparser.items('namespaces'):
            self.namespaces[prefix] = Namespace(uri)

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
        return URIRef(str(namespaces[ns]) + localpart)
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
