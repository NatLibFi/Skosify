# encoding=utf-8
import unittest
import logging
from io import StringIO
from rdflib import URIRef

import skosify


def test_config(caplog):
    config = skosify.config('examples/dctype.cfg')

    assert ('root', logging.WARNING,
            'Ignoring unknown configuration option: debug') in caplog.record_tuples

    assert config['narrower'] is True

    assert config['namespaces']['dcmitype'] == URIRef('http://purl.org/dc/dcmitype/')
    assert set(config['namespaces'].keys()) == set(['owl', 'rdf', 'xsd', 'rdfs', 'dct', 'skos', 'dc', 'dcmitype'])

    # TODO: types, literals, relations


def test_empty_config_file():
    cfg = StringIO()
    cfg.write(u'')
    config = skosify.config(cfg)
    assert set(config['namespaces'].keys()) == set(['owl', 'rdf', 'xsd', 'rdfs', 'dct', 'skos', 'dc'])
    cfg.close()


def test_config_file_with_closed_namespace():
    cfg = StringIO()
    cfg.write(u'''
[literals]
rdfs.comment_EN=rdfs.comment
''')
    cfg.seek(0)
    config = skosify.config(cfg)
    assert set(config['namespaces'].keys()) == set(['owl', 'rdf', 'xsd', 'rdfs', 'dct', 'skos', 'dc'])
    cfg.close()


if __name__ == '__main__':
    unittest.main()
