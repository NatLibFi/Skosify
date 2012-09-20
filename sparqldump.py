#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Osma Suominen <osma.suominen@aalto.fi>
# Copyright (c) 2012 Aalto University and University of Helsinki
# MIT License
# see README.txt for more information

import sys
from SPARQLWrapper import SPARQLWrapper, XML, TURTLE

FORMATMAP = {
  'xml': XML,
  'turtle': TURTLE,
}

def sparqldump(endpoint, graph=None, output='-', format='xml'):
  sparql = SPARQLWrapper(endpoint)
  if graph:
    graph = "GRAPH <%s>" % graph
  else:
    graph = ""
  sparql.setQuery("""
    CONSTRUCT { ?s ?p ?o }
    WHERE {
      %s { ?s ?p ?o . }
    }
  """ % graph)
  sparql.setReturnFormat(FORMATMAP[format])
  response = sparql.query().response

  if output == '-':
    out = sys.stdout
  else:
    out = open(output, "w")
  
  while True:
    data = response.read(1024)
    if len(data) == 0: break
    out.write(data)
  out.close()

def main():
  import optparse
  
  # process command line parameters
  # e.g. sparqldump -g http://example.org/mygraph http://example.org/sparql
  usage = "Usage: %prog [options] endpoint "
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-g', '--graph', type='string', help='Named graph to query. Default is none (i.e. use the default graph of the endpoint)')
  parser.add_option('-o', '--output', type='string', default='-', help='Output file name. Default is "-" (stdout).')
  parser.add_option('-F', '--to-format', type='string', default='turtle', help='Requested output format. Default is "xml". Possible values: xml, turtle. Not all endpoints will honor this setting.')
  
  options, remainingArgs = parser.parse_args()
  if len(remainingArgs) != 1:
    parser.error("exactly one endpoint URL must be specified")
  
  sparqldump(remainingArgs[0], options.graph, options.output, options.to_format)

if __name__ == '__main__':
  main()
