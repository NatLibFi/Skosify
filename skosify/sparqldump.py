#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Osma Suominen <osma.suominen@aalto.fi>
# Copyright (c) 2012 Aalto University and University of Helsinki
# MIT License
# see README.txt for more information

import sys
import os
import logging
from SPARQLWrapper import SPARQLWrapper, XML, TURTLE

FORMATMAP = {
  'xml': XML,
  'turtle': TURTLE,
}

def query_to_file(endpoint, graph, output, format, limit=0, offset=0, ordered=False):
  logging.debug("Querying to file %s", output)
  sparql = SPARQLWrapper(endpoint)

  if graph:
    graph = "GRAPH <%s>" % graph
  else:
    graph = ""

  if limit:
    extra = "LIMIT %s OFFSET %s" % (limit, offset)
    if ordered:
      extra = "ORDER BY ?s ?p ?o " + extra
  else:
    extra = ""

  query = """
    CONSTRUCT { ?s ?p ?o }
    WHERE {
      %s { ?s ?p ?o . }
    } %s
  """ % (graph, extra)
  logging.debug("query: %s", query)
  sparql.setQuery(query)
  sparql.setReturnFormat(FORMATMAP[format])
  response = sparql.query().response

  if output == '-':
    out = sys.stdout
  else:
    out = open(output, "w")
  
  size = 0
  while True:
    data = response.read(1024)
    size += len(data)
    if len(data) == 0: break
    out.write(data)
  out.close()
  logging.info("Wrote %d bytes to output file %s", size, output)
  return size
  
def sparqldump(endpoint, graph=None, output='-', format='xml', multiple=0, ordered=False):
  if multiple:
    logging.debug("Multiple query mode, querying %d triples per request", multiple)
    page = totalsize = lastsize = 0
    lastfile = None
    while True:
      outfile = output
      if output != '-': outfile = "%s-%d" % (output, page + 1)
      offset = page * multiple
      size = query_to_file(endpoint, graph, outfile, format, multiple, offset, ordered)
      totalsize += size
      if size < 1024 and size == lastsize:
        logging.info("Empty results seen, cleaning up empty files: %s %s", lastfile, outfile)
        os.remove(outfile)
        os.remove(lastfile)
        return totalsize
      lastsize = size
      lastfile = outfile
      page += 1
  else:
    logging.debug("Single query mode")
    return query_to_file(endpoint, graph, output, format)
  

def main():
  import optparse
  
  # process command line parameters
  # e.g. sparqldump -g http://example.org/mygraph http://example.org/sparql
  usage = "Usage: %prog [options] endpoint "
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-o', '--output', type='string', default='-', help='Output file name. Default is "-" (stdout).')
  parser.add_option('-f', '--to-format', type='string', default='xml', help='Requested output format. Default is "xml". Possible values: xml, turtle. Not all endpoints will honor this setting.')
  parser.add_option('-g', '--graph', type='string', help='Named graph to query. Default is none (i.e. use the default graph of the endpoint)')
  parser.add_option('-m', '--multiple', type='int', help='Perform multiple queries, with the specified number of triples per query. Useful for endpoints that limit the response size.')
  parser.add_option('-O', '--ordered', action='store_true', help='In multiple mode, add an ORDER BY clause to ensure the correct triples are returned. This may be heavy to process for the endpoint.')
  parser.add_option('-D', '--debug', action="store_true", help='Show debug output.')
  parser.add_option('-d', '--no-debug', dest="debug", action="store_false", help='Hide debug output.')
  
  options, remainingArgs = parser.parse_args()
  if len(remainingArgs) != 1:
    parser.error("exactly one endpoint URL must be specified")
  
  # configure logging
  logformat = '%(levelname)s: %(message)s'
  loglevel = logging.INFO
  if options.debug:
    loglevel = logging.DEBUG
  logging.basicConfig(format=logformat, level=loglevel)
  
  totalsize = sparqldump(remainingArgs[0], options.graph, options.output, options.to_format, options.multiple, options.ordered)
  logging.debug("Total %d bytes dumped.", totalsize)

if __name__ == '__main__':
  main()
