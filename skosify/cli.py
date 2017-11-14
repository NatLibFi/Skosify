# -*- coding: utf-8 -*-
"""Provides skosify as command line client."""

from __future__ import print_function

from .skosify import Skosify

import optparse
import logging
import sys

from rdflib import URIRef, Namespace, RDF, RDFS

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


# default values for config file / command line options
DEFAULT_OPTIONS = {
    'output': '-',
    'log': None,
    'from_format': None,
    'to_format': None,
    'mark_top_concepts': True,
    'narrower': True,
    'transitive': False,
    'enrich_mappings': True,
    'aggregates': False,
    'keep_related': False,
    'break_cycles': False,
    'eliminate_redundancy': False,
    'cleanup_classes': False,
    'cleanup_properties': False,
    'cleanup_unreachable': False,
    'namespace': None,
    'label': None,
    'set_modified': False,
    'default_language': None,
    'preflabel_policy': 'shortest',
    'debug': False,
    'infer': False,
    'update_query': None,
    'construct_query': None,
}

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

def get_option_parser(defaults):
    """Create and return an OptionParser with the given defaults."""
    # based on recipe from:
    # http://stackoverflow.com/questions/1880404/using-a-file-to-store-optparse-arguments

    # process command line parameters
    # e.g. skosify yso.owl -o yso-skos.rdf
    usage = "Usage: %prog [options] voc1 [voc2 ...]"
    parser = optparse.OptionParser(usage=usage)
    parser.set_defaults(**defaults)
    parser.add_option('-c', '--config', type='string',
                      help='Read default options '
                           'and transformation definitions '
                           'from the given configuration file.')
    parser.add_option('-o', '--output', type='string',
                      help='Output file name. Default is "-" (stdout).')
    parser.add_option('-D', '--debug', action="store_true",
                      help='Show debug output.')
    parser.add_option('-d', '--no-debug', dest="debug",
                      action="store_false", help='Hide debug output.')
    parser.add_option('-O', '--log', type='string',
                      help='Log file name. Default is to use standard error.')


    group = optparse.OptionGroup(parser, "Input and Output Options")
    group.add_option('-f', '--from-format', type='string',
                      help='Input format. '
                           'Default is to detect format '
                           'based on file extension. '
                           'Possible values: xml, n3, turtle, nt...')
    group.add_option('-F', '--to-format', type='string',
                      help='Output format. '
                           'Default is to detect format '
                           'based on file extension. '
                           'Possible values: xml, n3, turtle, nt...')
    group.add_option('--update-query', type='string',
                      help='SPARQL update query. '
                           'This query is executed against the input '
                           'data before processing it. '
                           'The value can be either the actual query, '
                           'or "@filename".')
    group.add_option('--construct-query', type='string',
                      help='SPARQL CONSTRUCT query. '
                           'This query is executed against the input '
                           'data and the result graph is used as the '
                           'actual input. '
                           'The value can be either the actual query, '
                           'or "@filename".')
    group.add_option('-I', '--infer', action="store_true",
                     help='Perform RDFS subclass/subproperty inference '
                          'before transforming input.')
    group.add_option('-i', '--no-infer', dest="infer", action="store_false",
                     help="Don't perform RDFS subclass/subproperty inference "
                          "before transforming input.")
    parser.add_option_group(group)

    group = optparse.OptionGroup(
        parser, "Concept Scheme and Labelling Options")
    group.add_option('-s', '--namespace', type='string',
                     help='Namespace of vocabulary '
                          '(usually optional; used to create a ConceptScheme)')
    group.add_option('-L', '--label', type='string',
                     help='Label/title for the vocabulary '
                          '(usually optional; used to label a ConceptScheme)')
    group.add_option('-l', '--default-language', type='string',
                     help='Language tag to set for labels '
                          'with no defined language.')
    group.add_option('-p', '--preflabel-policy', type='string',
                     help='Policy for handling multiple prefLabels '
                          'with the same language tag. '
                          'Possible values: shortest, longest, all.')
    group.add_option('--set-modified', dest="set_modified",
                     action="store_true",
                     help='Set modification date on the ConceptScheme')
    group.add_option('--no-set-modified', dest="set_modified",
                     action="store_false",
                     help="Don't set modification date on the ConceptScheme")
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Vocabulary Structure Options")
    group.add_option('-E', '--mark-top-concepts', action="store_true",
                     help='Mark top-level concepts in the hierarchy '
                          'as top concepts (entry points).')
    group.add_option('-e', '--no-mark-top-concepts',
                     dest="mark_top_concepts", action="store_false",
                     help="Don't mark top-level concepts in the hierarchy "
                          "as top concepts.")
    group.add_option('-N', '--narrower', action="store_true",
                     help='Include narrower/narrowerGeneric/narrowerPartitive '
                          'relationships in the output vocabulary.')
    group.add_option('-n', '--no-narrower',
                     dest="narrower", action="store_false",
                     help="Don't include "
                          "narrower/narrowerGeneric/narrowerPartitive "
                          "relationships in the output vocabulary.")
    group.add_option('-T', '--transitive', action="store_true",
                     help='Include transitive hierarchy relationships '
                          'in the output vocabulary.')
    group.add_option('-t', '--no-transitive',
                     dest="transitive", action="store_false",
                     help="Don't include transitive hierarchy relationships "
                          "in the output vocabulary.")
    group.add_option('-M', '--enrich-mappings', action="store_true",
                     help='Perform SKOS enrichments on mapping relationships.')
    group.add_option('-m', '--no-enrich-mappings', dest="enrich_mappings",
                     action="store_false",
                     help="Don't perform SKOS enrichments "
                          "on mapping relationships.")
    group.add_option('-A', '--aggregates', action="store_true",
                     help='Keep AggregateConcepts completely '
                          'in the output vocabulary.')
    group.add_option('-a', '--no-aggregates',
                     dest="aggregates", action="store_false",
                     help='Remove AggregateConcepts completely '
                          'from the output vocabulary.')
    group.add_option('-R', '--keep-related', action="store_true",
                     help="Keep skos:related relationships "
                          "within the same hierarchy.")
    group.add_option('-r', '--no-keep-related',
                     dest="keep_related", action="store_false",
                     help="Remove skos:related relationships "
                          "within the same hierarchy.")
    group.add_option('-B', '--break-cycles', action="store_true",
                     help="Break any cycles in the skos:broader hierarchy.")
    group.add_option('-b', '--no-break-cycles', dest="break_cycles",
                     action="store_false",
                     help="Don't break cycles in the skos:broader hierarchy.")
    group.add_option('--eliminate-redundancy', action="store_true",
                     help="Eliminate hierarchical redundancy in the "
                          "skos:broader hierarchy.")
    group.add_option('--no-eliminate-redundancy', dest="eliminate_redundancy",
                     action="store_false",
                     help="Don't eliminate hierarchical redundancy in the "
                          "skos:broader hierarchy.")
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Cleanup Options")
    group.add_option('--cleanup-classes', action="store_true",
                     help="Remove definitions of classes with no instances.")
    group.add_option('--no-cleanup-classes', dest='cleanup_classes',
                     action="store_false",
                     help="Don't remove definitions "
                          "of classes with no instances.")
    group.add_option('--cleanup-properties', action="store_true",
                     help="Remove definitions of properties "
                          "which have not been used.")
    group.add_option('--no-cleanup-properties', action="store_false",
                     dest='cleanup_properties',
                     help="Don't remove definitions of properties "
                          "which have not been used.")
    group.add_option('--cleanup-unreachable', action="store_true",
                     help="Remove triples which can not be reached "
                          "by a traversal from the main vocabulary graph.")
    group.add_option('--no-cleanup-unreachable', action="store_false",
                     dest='cleanup_unreachable',
                     help="Don't remove triples which can not be reached "
                          "by a traversal from the main vocabulary graph.")
    parser.add_option_group(group)

    return parser


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


def main():
    """Read command line parameters and make a transform based on them."""

    skosify = Skosify()

    namespaces = DEFAULT_NAMESPACES
    typemap = {}
    literalmap = {}
    relationmap = {}
    defaults = DEFAULT_OPTIONS
    options, remainingArgs = get_option_parser(defaults).parse_args()

    if options.config is not None:
        # read the supplied configuration file
        cfgparser = configparser.SafeConfigParser()
        # force case-sensitive handling of option names
        cfgparser.optionxform = str
        cfgparser.read(options.config)

        # parse namespaces from configuration file
        for prefix, uri in cfgparser.items('namespaces'):
            namespaces[prefix] = URIRef(uri)

        # parse types from configuration file
        for key, val in cfgparser.items('types'):
            typemap[expand_curielike(namespaces, key)] = \
                expand_mapping_target(namespaces, val)

        # parse literals from configuration file
        for key, val in cfgparser.items('literals'):
            literalmap[expand_curielike(namespaces, key)] = \
                expand_mapping_target(namespaces, val)

        # parse relations from configuration file
        for key, val in cfgparser.items('relations'):
            relationmap[expand_curielike(namespaces, key)] = \
                expand_mapping_target(namespaces, val)

        # parse options from configuration file
        for opt, val in cfgparser.items('options'):
            if opt not in defaults:
                logging.warning(
                    'Unknown option in configuration file: %s (ignored)', opt)
                continue
            if defaults[opt] in (True, False):  # is a Boolean option
                defaults[opt] = cfgparser.getboolean('options', opt)
            else:
                defaults[opt] = val

        # re-initialize and re-run OptionParser using defaults read from
        # configuration file
        options, remainingArgs = get_option_parser(defaults).parse_args()

    if remainingArgs:
        inputfiles = remainingArgs
    else:
        inputfiles = ['-']

    voc = skosify.skosify(inputfiles, namespaces, typemap, literalmap, relationmap, options)

    write_rdf(voc, options.output, options.to_format)


if __name__ == '__main__':
    main()
