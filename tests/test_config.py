# encoding=utf-8
import unittest
import pytest
import logging

from rdflib import URIRef, Namespace

from skosify.skosify import Config


def test_config(caplog):
    config = Config('examples/owl2skos.cfg')

    assert ('root', logging.WARNING,
            'Ignoring unknown configuration option: debug') in caplog.record_tuples

    assert config.narrower is True

    assert config.namespaces['dcmitype'] == URIRef('http://purl.org/dc/dcmitype/')

    # TODO: types, literals, relations


if __name__ == '__main__':
    unittest.main()
