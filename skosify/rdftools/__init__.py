# -*- coding: utf-8 -*-
"""Utility module with generic RDF methods not specific to SKOS."""

from .io import read_rdf, write_rdf
from .access import localname, find_prop_overlap
from .modify import replace_subject, replace_predicate, replace_object, replace_uri, delete_uri

__all__ = ['read_rdf', 'write_rdf', 'localname', 'find_prop_overlap',
           'replace_subject', 'replace_predicate', 'replace_object',
           'replace_uri', 'delete_uri']
