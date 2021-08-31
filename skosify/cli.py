# -*- coding: utf-8 -*-
"""Provides skosify as command line client."""

from skosify import skosify
from .rdftools import write_rdf
from .config import Config

import optparse
import logging


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
                     'data (after possible --update-query) and '
                     'the result graph is used as the actual input. '
                     'The value can be either the actual query, '
                     'or "@filename".')
    group.add_option('--post-update-query', type='string',
                     help='SPARQL update query. '
                     'This convenience query is executed against '
                     'the output data before writing it. '
                     'The value can be either the actual query, '
                     'or "@filename". '
                     'Use at your own risk - output may not be '
                     'SKOS at all.')
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
                          'Possible values: shortest, longest, lowercase, '
                          'uppercase, all. Can also be a comma-separated list '
                          'of policies to apply in order.')
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


def main():
    """Read command line parameters and make a transform based on them."""

    config = Config()

    # additional options for command line client only
    defaults = vars(config)
    defaults['to_format'] = None
    defaults['output'] = '-'
    defaults['log'] = None
    defaults['debug'] = False

    options, remainingArgs = get_option_parser(defaults).parse_args()
    for key in vars(options):
        if hasattr(config, key):
            setattr(config, key, getattr(options, key))

    # configure logging, messages to stderr by default
    logformat = '%(levelname)s: %(message)s'
    loglevel = logging.INFO
    if options.debug:
        loglevel = logging.DEBUG
    if options.log:
        logging.basicConfig(filename=options.log,
                            format=logformat, level=loglevel)
    else:
        logging.basicConfig(format=logformat, level=loglevel)

    output = options.output

    # read config file as defaults and override from command line arguments
    if options.config is not None:
        config.read_and_parse_config_file(options.config)
        options, remainingArgs = get_option_parser(vars(config)).parse_args()
        for key in vars(options):
            if hasattr(config, key):
                setattr(config, key, getattr(options, key))

    if remainingArgs:
        inputfiles = remainingArgs
    else:
        inputfiles = ['-']

    voc = skosify(*inputfiles, **vars(config))
    write_rdf(voc, output, config.to_format)


if __name__ == '__main__':
    main()
