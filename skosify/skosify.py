# encoding=utf8

import sys
import time
import logging
import datetime

from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, RDFS, OWL, DC, DCTERMS, XSD, SKOS
from .rdftools.namespace import SKOSEXT
from .rdftools import (
    read_rdf,
    replace_subject,
    replace_predicate,
    replace_object,
    replace_uri,
    delete_uri,
    localname,
    find_prop_overlap
)

from .config import Config
from . import infer


def mapping_get(uri, mapping):
    """Look up the URI in the given mapping and return the result.

    Throws KeyError if no matching mapping was found.

    """
    ln = localname(uri)
    # 1. try to match URI keys
    for k, v in mapping.items():
        if k == uri:
            return v
    # 2. try to match local names
    for k, v in mapping.items():
        if k == ln:
            return v
    # 3. try to match local names with * prefix
    # try to match longest first, so sort the mapping by key length
    l = list(mapping.items())
    l.sort(key=lambda i: len(i[0]), reverse=True)
    for k, v in l:
        if k[0] == '*' and ln.endswith(k[1:]):
            return v
    raise KeyError(uri)


def mapping_match(uri, mapping):
    """Determine whether the given URI matches one of the given mappings.

    Returns True if a match was found, False otherwise.

    """
    try:
        val = mapping_get(uri, mapping)
        return True
    except KeyError:
        return False


def in_general_ns(uri):
    """Return True iff the URI is in a well-known general RDF namespace.

    URI namespaces considered well-known are RDF, RDFS, OWL, SKOS and DC."""
    RDFuri = RDF.uri
    RDFSuri = RDFS.uri

    for ns in (RDFuri, RDFSuri, OWL, SKOS, DC):
        if uri.startswith(ns):
            return True
    return False


def get_concept_scheme(rdf):
    """Return a skos:ConceptScheme contained in the model.

    Returns None if no skos:ConceptScheme is present.
    """
    # add explicit type
    for s, o in rdf.subject_objects(SKOS.inScheme):
        if not isinstance(o, Literal):
            rdf.add((o, RDF.type, SKOS.ConceptScheme))
        else:
            logging.warning(
                "Literal value %s for skos:inScheme detected, ignoring.", o)
    css = list(rdf.subjects(RDF.type, SKOS.ConceptScheme))
    if len(css) > 1:
        css.sort()
        cs = css[0]
        logging.warning(
            "Multiple concept schemes found. "
            "Selecting %s as default concept scheme.", cs)
    elif len(css) == 1:
        cs = css[0]
    else:
        cs = None

    return cs


def detect_namespace(rdf):
    """Try to automatically detect the URI namespace of the vocabulary.

    Return namespace as URIRef.

    """

    # pick a concept
    conc = rdf.value(None, RDF.type, SKOS.Concept, any=True)
    if conc is None:
        logging.critical(
            "Namespace auto-detection failed. "
            "Set namespace using the --namespace option.")
        sys.exit(1)

    ln = localname(conc)
    ns = URIRef(conc.replace(ln, ''))
    if ns.strip() == '':
        logging.critical(
            "Namespace auto-detection failed. "
            "Set namespace using the --namespace option.")
        sys.exit(1)

    logging.info(
        "Namespace auto-detected to '%s' "
        "- you can override this with the --namespace option.", ns)
    return ns


def create_concept_scheme(rdf, ns, lname=''):
    """Create a skos:ConceptScheme in the model and return it."""

    ont = None
    if not ns:
        # see if there's an owl:Ontology and use that to determine namespace
        onts = list(rdf.subjects(RDF.type, OWL.Ontology))
        if len(onts) > 1:
            onts.sort()
            ont = onts[0]
            logging.warning(
                "Multiple owl:Ontology instances found. "
                "Creating concept scheme from %s.", ont)
        elif len(onts) == 1:
            ont = onts[0]
        else:
            ont = None

        if not ont:
            logging.info(
                "No skos:ConceptScheme or owl:Ontology found. "
                "Using namespace auto-detection for creating concept scheme.")
            ns = detect_namespace(rdf)
        elif ont.endswith('/') or ont.endswith('#') or ont.endswith(':'):
            ns = ont
        else:
            ns = ont + '/'

    NS = Namespace(ns)
    cs = NS[lname]

    rdf.add((cs, RDF.type, SKOS.ConceptScheme))

    if ont is not None:
        rdf.remove((ont, RDF.type, OWL.Ontology))
        # remove owl:imports declarations
        for o in rdf.objects(ont, OWL.imports):
            rdf.remove((ont, OWL.imports, o))
        # remove protege specific properties
        for p, o in rdf.predicate_objects(ont):
            prot = URIRef(
                'http://protege.stanford.edu/plugins/owl/protege#')
            if p.startswith(prot):
                rdf.remove((ont, p, o))
        # move remaining properties (dc:title etc.) of the owl:Ontology into
        # the skos:ConceptScheme
        replace_uri(rdf, ont, cs)

    return cs


def initialize_concept_scheme(rdf, cs, label, language, set_modified):
    """Initialize a concept scheme: Optionally add a label if the concept
    scheme doesn't have a label, and optionally add a dct:modified
    timestamp."""

    # check whether the concept scheme is unlabeled, and label it if possible
    labels = list(rdf.objects(cs, RDFS.label)) + \
        list(rdf.objects(cs, SKOS.prefLabel))
    if len(labels) == 0:
        if not label:
            logging.warning(
                "Concept scheme has no label(s). "
                "Use --label option to set the concept scheme label.")
        else:
            logging.info(
                "Unlabeled concept scheme detected. Setting label to '%s'" %
                label)
            rdf.add((cs, RDFS.label, Literal(label, language)))

    if set_modified:
        curdate = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        rdf.remove((cs, DCTERMS.modified, None))
        rdf.add((cs, DCTERMS.modified, Literal(curdate, datatype=XSD.dateTime)))


def transform_sparql_update(rdf, update_query):
    """Perform a SPARQL Update transformation on the RDF data."""

    logging.debug("performing SPARQL Update transformation")

    if update_query[0] == '@':  # actual query should be read from file
        update_query = file(update_query[1:]).read()

    logging.debug("update query: %s", update_query)
    rdf.update(update_query)


def transform_sparql_construct(rdf, construct_query):
    """Perform a SPARQL CONSTRUCT query on the RDF data and return a new graph."""

    logging.debug("performing SPARQL CONSTRUCT transformation")

    if construct_query[0] == '@':  # actual query should be read from file
        construct_query = file(construct_query[1:]).read()

    logging.debug("CONSTRUCT query: %s", construct_query)

    newgraph = Graph()
    for triple in rdf.query(construct_query):
        newgraph.add(triple)

    return newgraph


def transform_concepts(rdf, typemap):
    """Transform Concepts into new types, as defined by the config file."""

    # find out all the types used in the model
    types = set()
    for s, o in rdf.subject_objects(RDF.type):
        if o not in typemap and in_general_ns(o):
            continue
        types.add(o)

    for t in types:
        if mapping_match(t, typemap):
            newval = mapping_get(t, typemap)
            newuris = [v[0] for v in newval]
            logging.debug("transform class %s -> %s", t, str(newuris))
            if newuris[0] is None:  # delete all instances
                for inst in rdf.subjects(RDF.type, t):
                    delete_uri(rdf, inst)
                delete_uri(rdf, t)
            else:
                replace_object(rdf, t, newuris, predicate=RDF.type)
        else:
            logging.info("Don't know what to do with type %s", t)


def transform_literals(rdf, literalmap):
    """Transform literal properties of Concepts, as defined by config file."""

    affected_types = (SKOS.Concept, SKOS.Collection,
                      SKOSEXT.DeprecatedConcept)

    props = set()
    for t in affected_types:
        for conc in rdf.subjects(RDF.type, t):
            for p, o in rdf.predicate_objects(conc):
                if isinstance(o, Literal) \
                   and (p in literalmap or not in_general_ns(p)):
                    props.add(p)

    for p in props:
        if mapping_match(p, literalmap):
            newval = mapping_get(p, literalmap)
            newuris = [v[0] for v in newval]
            logging.debug("transform literal %s -> %s", p, str(newuris))
            replace_predicate(
                rdf, p, newuris, subjecttypes=affected_types)
        else:
            logging.info("Don't know what to do with literal %s", p)


def transform_relations(rdf, relationmap):
    """Transform YSO-style concept relations into SKOS equivalents."""

    affected_types = (SKOS.Concept, SKOS.Collection,
                      SKOSEXT.DeprecatedConcept)

    props = set()
    for t in affected_types:
        for conc in rdf.subjects(RDF.type, t):
            for p, o in rdf.predicate_objects(conc):
                if isinstance(o, (URIRef, BNode)) \
                   and (p in relationmap or not in_general_ns(p)):
                    props.add(p)

    for p in props:
        if mapping_match(p, relationmap):
            newval = mapping_get(p, relationmap)
            logging.debug("transform relation %s -> %s", p, str(newval))
            replace_predicate(
                rdf, p, newval, subjecttypes=affected_types)
        else:
            logging.info("Don't know what to do with relation %s", p)


def transform_labels(rdf, defaultlanguage):
    # fix labels and documentary notes with extra whitespace
    for labelProp in (
            SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel,
            SKOSEXT.candidateLabel, SKOS.note, SKOS.scopeNote,
            SKOS.definition, SKOS.example, SKOS.historyNote,
            SKOS.editorialNote, SKOS.changeNote, RDFS.label):
        for conc, label in sorted(rdf.subject_objects(labelProp)):
            if not isinstance(label, Literal):
                continue
            # strip extra whitespace, if found
            if len(label.strip()) < len(label):
                logging.warning(
                    "Stripping whitespace from label of %s: '%s'", conc, label)
                newlabel = Literal(label.strip(), label.language)
                rdf.remove((conc, labelProp, label))
                rdf.add((conc, labelProp, newlabel))
                label = newlabel
            # set default language
            if defaultlanguage and label.language is None:
                logging.warning(
                    "Setting default language of '%s' to %s",
                    label, defaultlanguage)
                newlabel = Literal(label, defaultlanguage)
                rdf.remove((conc, labelProp, label))
                rdf.add((conc, labelProp, newlabel))

    # make skosext:candidateLabel either prefLabel or altLabel
    # make a set of (concept, language) tuples for concepts which have
    # candidateLabels in some language
    conc_lang = set([(c, l.language)
                     for c, l in rdf.subject_objects(SKOSEXT.candidateLabel)])
    for conc, lang in conc_lang:
        # check whether there are already prefLabels for this concept in this
        # language
        if lang not in [pl.language
                        for pl in rdf.objects(conc, SKOS.prefLabel)]:
            # no -> let's transform the candidate labels into prefLabels
            to_prop = SKOS.prefLabel
        else:
            # yes -> let's make them altLabels instead
            to_prop = SKOS.altLabel

        # do the actual transform from candidateLabel to prefLabel or altLabel
        for label in rdf.objects(conc, SKOSEXT.candidateLabel):
            if label.language != lang:
                continue
            rdf.remove((conc, SKOSEXT.candidateLabel, label))
            rdf.add((conc, to_prop, label))

    for conc, label in rdf.subject_objects(SKOSEXT.candidateLabel):
        rdf.remove((conc, SKOSEXT.candidateLabel, label))
        if label.language not in [pl.language
                                  for pl in rdf.objects(conc, SKOS.prefLabel)]:
            # no prefLabel found, make this candidateLabel a prefLabel
            rdf.add((conc, SKOS.prefLabel, label))
        else:
            # prefLabel found, make it an altLabel instead
            rdf.add((conc, SKOS.altLabel, label))


def transform_collections(rdf):
    for coll in sorted(rdf.subjects(RDF.type, SKOS.Collection)):
        for prop in (SKOS.broader, SKOSEXT.broaderGeneric):
            broaders = set(rdf.objects(coll, prop))
            narrowers = set(rdf.subjects(prop, coll))
            # remove the Collection from the hierarchy
            for b in broaders:
                rdf.remove((coll, prop, b))
            # replace the broader relationship with inverse skos:member
            for n in narrowers:
                rdf.remove((n, prop, coll))
                rdf.add((coll, SKOS.member, n))
                # add a direct broader relation to the broaders of the
                # collection
                for b in broaders:
                    rdf.add((n, prop, b))

        # avoid using SKOS semantic relations as they're only meant
        # to be used for concepts (i.e. have rdfs:domain skos:Concept)
        # FIXME should maybe use some substitute for exactMatch for
        # collections?
        for relProp in (SKOS.semanticRelation,
                        SKOS.broader, SKOS.narrower, SKOS.related,
                        SKOS.broaderTransitive, SKOS.narrowerTransitive,
                        SKOS.mappingRelation,
                        SKOS.closeMatch, SKOS.exactMatch,
                        SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch,
                        SKOS.topConceptOf, SKOS.hasTopConcept):
            for o in sorted(rdf.objects(coll, relProp)):
                logging.warning(
                    "Removing concept relation %s -> %s from collection %s",
                    localname(relProp), o, coll)
                rdf.remove((coll, relProp, o))
            for s in sorted(rdf.subjects(relProp, coll)):
                logging.warning(
                    "Removing concept relation %s <- %s from collection %s",
                    localname(relProp), s, coll)
                rdf.remove((s, relProp, coll))


def transform_aggregate_concepts(rdf, cs, relationmap, aggregates):
    """Transform YSO-style AggregateConcepts into skos:Concepts within their
       own skos:ConceptScheme, linked to the regular concepts with
       SKOS.narrowMatch relationships. If aggregates is False, remove
       all aggregate concepts instead."""

    if not aggregates:
        logging.debug("removing aggregate concepts")

    aggregate_concepts = []

    relation = relationmap.get(
        OWL.equivalentClass, [(OWL.equivalentClass, False)])[0][0]
    for conc, eq in rdf.subject_objects(relation):
        eql = rdf.value(eq, OWL.unionOf, None)
        if eql is None:
            continue
        if aggregates:
            aggregate_concepts.append(conc)
            for item in rdf.items(eql):
                rdf.add((conc, SKOS.narrowMatch, item))
        # remove the old equivalentClass-unionOf-rdf:List structure
        rdf.remove((conc, relation, eq))
        rdf.remove((eq, RDF.type, OWL.Class))
        rdf.remove((eq, OWL.unionOf, eql))
        # remove the rdf:List structure
        delete_uri(rdf, eql)
        if not aggregates:
            delete_uri(rdf, conc)

    if len(aggregate_concepts) > 0:
        ns = cs.replace(localname(cs), '')
        acs = create_concept_scheme(rdf, ns, 'aggregateconceptscheme')
        logging.debug("creating aggregate concept scheme %s", acs)
        for conc in aggregate_concepts:
            rdf.add((conc, SKOS.inScheme, acs))


def transform_deprecated_concepts(rdf, cs):
    """Transform deprecated concepts so they are in their own concept
    scheme."""

    deprecated_concepts = []

    for conc in rdf.subjects(RDF.type, SKOSEXT.DeprecatedConcept):
        rdf.add((conc, RDF.type, SKOS.Concept))
        rdf.add((conc, OWL.deprecated, Literal("true", datatype=XSD.boolean)))
        deprecated_concepts.append(conc)

    if len(deprecated_concepts) > 0:
        ns = cs.replace(localname(cs), '')
        dcs = create_concept_scheme(
            rdf, ns, 'deprecatedconceptscheme')
        logging.debug("creating deprecated concept scheme %s", dcs)
        for conc in deprecated_concepts:
            rdf.add((conc, SKOS.inScheme, dcs))


# { ?a skos:broader ?b . ?b skos:broader => ?c }
# => { ?a skos:broaderTransitive ?b, ?c . ?b skos:broaderTransitive ?c }
def infer_broaderTransitive(rdf):
    for conc in rdf.subjects(RDF.type, SKOS.Concept):
        for bt in rdf.transitive_objects(conc, SKOS.broader):
            if bt == conc:
                continue
            rdf.add((conc, SKOS.broaderTransitive, bt))


# { ?a skos:broader ?b . ?b skos:broader => ?c }
# => { ?c skos:narrowerTransitive ?a, ?b . ?b skos:narrowerTransitive ?a }
def infer_narrowerTransitive(rdf):
    for conc in rdf.subjects(RDF.type, SKOS.Concept):
        for bt in rdf.transitive_objects(conc, SKOS.broader):
            if bt == conc:
                continue
            rdf.add((bt, SKOS.narrowerTransitive, conc))


# { ?a skos:broader ?b } <=> { ?b skos:narrower ?a }
def infer_broader_narrower(rdf):
    for s, o in rdf.subject_objects(SKOS.broader):
        rdf.add((o, SKOS.narrower, s))
    for s, o in rdf.subject_objects(SKOS.narrower):
        rdf.add((o, SKOS.broader, s))


def enrich_relations(rdf, enrich_mappings, use_narrower, use_transitive):
    """Enrich the SKOS relations according to SKOS semantics, including
    subproperties of broader and symmetric related properties. If use_narrower
    is True, include inverse narrower relations for all broader relations. If
    use_narrower is False, instead remove all narrower relations, replacing
    them with inverse broader relations. If use_transitive is True, calculate
    transitive hierarchical relationships.

    (broaderTransitive, and also narrowerTransitive if use_narrower is
    True) and include them in the model.

    """

    # 1. first enrich mapping relationships (because they affect regular ones)

    if enrich_mappings:
        infer.skos_symmetric_mappings(rdf)
        infer.skos_hierarchical_mappings(rdf, use_narrower)

    # 2. then enrich regular relationships

    # related <-> related
    infer.skos_related(rdf)

    # broaderGeneric -> broader + inverse narrowerGeneric
    for s, o in rdf.subject_objects(SKOSEXT.broaderGeneric):
        rdf.add((s, SKOS.broader, o))

    # broaderPartitive -> broader + inverse narrowerPartitive
    for s, o in rdf.subject_objects(SKOSEXT.broaderPartitive):
        rdf.add((s, SKOS.broader, o))

    infer.skos_hierarchical(rdf, use_narrower)

    # transitive closure: broaderTransitive and narrowerTransitive
    if use_transitive:
        infer.skos_transitive(rdf, use_narrower)
    else:
        # transitive relationships are not wanted, so remove them
        for s, o in rdf.subject_objects(SKOS.broaderTransitive):
            rdf.remove((s, SKOS.broaderTransitive, o))
        for s, o in rdf.subject_objects(SKOS.narrowerTransitive):
            rdf.remove((s, SKOS.narrowerTransitive, o))

    infer.skos_topConcept(rdf)


def setup_top_concepts(rdf, mark_top_concepts):
    """Determine the top concepts of each concept scheme and mark them using
    hasTopConcept/topConceptOf."""

    for cs in sorted(rdf.subjects(RDF.type, SKOS.ConceptScheme)):
        for conc in sorted(rdf.subjects(SKOS.inScheme, cs)):
            if (conc, RDF.type, SKOS.Concept) not in rdf:
                continue  # not a Concept, so can't be a top concept
            # check whether it's a top concept
            broader = rdf.value(conc, SKOS.broader, None, any=True)
            if broader is None:  # yes it is a top concept!
                if (cs, SKOS.hasTopConcept, conc) not in rdf and \
                   (conc, SKOS.topConceptOf, cs) not in rdf:
                    if mark_top_concepts:
                        logging.info(
                            "Marking loose concept %s "
                            "as top concept of scheme %s", conc, cs)
                        rdf.add((cs, SKOS.hasTopConcept, conc))
                        rdf.add((conc, SKOS.topConceptOf, cs))
                    else:
                        logging.debug(
                            "Not marking loose concept %s as top concept "
                            "of scheme %s, as mark_top_concepts is disabled",
                            conc, cs)


def setup_concept_scheme(rdf, defaultcs):
    """Make sure all concepts have an inScheme property, using the given
    default concept scheme if necessary."""
    for conc in rdf.subjects(RDF.type, SKOS.Concept):
        # check concept scheme
        cs = rdf.value(conc, SKOS.inScheme, None, any=True)
        if cs is None:  # need to set inScheme
            rdf.add((conc, SKOS.inScheme, defaultcs))


def cleanup_classes(rdf):
    """Remove unnecessary class definitions: definitions of SKOS classes or
       unused classes. If a class is also a skos:Concept or skos:Collection,
       remove the 'classness' of it but leave the Concept/Collection."""
    for t in (OWL.Class, RDFS.Class):
        for cl in rdf.subjects(RDF.type, t):
            # SKOS classes may be safely removed
            if cl.startswith(SKOS):
                logging.debug("removing SKOS class definition: %s", cl)
                replace_subject(rdf, cl, None)
                continue
            # if there are instances of the class, keep the class def
            if rdf.value(None, RDF.type, cl, any=True) is not None:
                continue
            # if the class is used in a domain/range/equivalentClass
            # definition, keep the class def
            if rdf.value(None, RDFS.domain, cl, any=True) is not None:
                continue
            if rdf.value(None, RDFS.range, cl, any=True) is not None:
                continue
            if rdf.value(None, OWL.equivalentClass, cl, any=True) is not None:
                continue

            # if the class is also a skos:Concept or skos:Collection, only
            # remove its rdf:type
            if (cl, RDF.type, SKOS.Concept) in rdf \
               or (cl, RDF.type, SKOS.Collection) in rdf:
                logging.debug("removing classiness of %s", cl)
                rdf.remove((cl, RDF.type, t))
            else:  # remove it completely
                logging.debug("removing unused class definition: %s", cl)
                replace_subject(rdf, cl, None)


def cleanup_properties(rdf):
    """Remove unnecessary property definitions.

    Reemoves SKOS and DC property definitions and definitions of unused
    properties."""
    for t in (RDF.Property, OWL.DatatypeProperty, OWL.ObjectProperty,
              OWL.SymmetricProperty, OWL.TransitiveProperty,
              OWL.InverseFunctionalProperty, OWL.FunctionalProperty):
        for prop in rdf.subjects(RDF.type, t):
            if prop.startswith(SKOS):
                logging.debug(
                    "removing SKOS property definition: %s", prop)
                replace_subject(rdf, prop, None)
                continue
            if prop.startswith(DC):
                logging.debug("removing DC property definition: %s", prop)
                replace_subject(rdf, prop, None)
                continue

            # if there are triples using the property, keep the property def
            if len(list(rdf.subject_objects(prop))) > 0:
                continue

            logging.debug("removing unused property definition: %s", prop)
            replace_subject(rdf, prop, None)


def find_reachable(rdf, res):
    """Return the set of reachable resources starting from the given resource,
    excluding the seen set of resources.

    Note that the seen set is modified
    in-place to reflect the ongoing traversal.

    """

    starttime = time.time()

    # This is almost a non-recursive breadth-first search algorithm, but a set
    # is used as the "open" set instead of a FIFO, and an arbitrary element of
    # the set is searched. This is slightly faster than DFS (using a stack)
    # and much faster than BFS (using a FIFO).
    seen = set()			# used as the "closed" set
    to_search = set([res])  # used as the "open" set

    while len(to_search) > 0:
        res = to_search.pop()
        if res in seen:
            continue
        seen.add(res)
        # res as subject
        for p, o in rdf.predicate_objects(res):
            if isinstance(p, URIRef) and p not in seen:
                to_search.add(p)
            if isinstance(o, URIRef) and o not in seen:
                to_search.add(o)
        # res as predicate
        for s, o in rdf.subject_objects(res):
            if isinstance(s, URIRef) and s not in seen:
                to_search.add(s)
            if isinstance(o, URIRef) and o not in seen:
                to_search.add(o)
        # res as object
        for s, p in rdf.subject_predicates(res):
            if isinstance(s, URIRef) and s not in seen:
                to_search.add(s)
            if isinstance(p, URIRef) and p not in seen:
                to_search.add(p)

    endtime = time.time()
    logging.debug("find_reachable took %f seconds", (endtime - starttime))

    return seen


def cleanup_unreachable(rdf):
    """Remove triples which cannot be reached from the concepts by graph
    traversal."""

    all_subjects = set(rdf.subjects())

    logging.debug("total subject resources: %d", len(all_subjects))

    reachable = find_reachable(rdf, SKOS.Concept)
    nonreachable = all_subjects - reachable

    logging.debug("deleting %s non-reachable resources", len(nonreachable))

    for subj in nonreachable:
        delete_uri(rdf, subj)


def check_labels(rdf, preflabel_policy):
    # check that resources have only one prefLabel per language
    resources = set(
        (res for res, label in rdf.subject_objects(SKOS.prefLabel)))
    for res in sorted(resources):
        prefLabels = {}
        for label in rdf.objects(res, SKOS.prefLabel):
            lang = label.language
            if lang not in prefLabels:
                prefLabels[lang] = []
            prefLabels[lang].append(label)
        for lang, labels in prefLabels.items():
            if len(labels) > 1:
                if preflabel_policy == 'all':
                    logging.warning(
                        "Resource %s has more than one prefLabel@%s, "
                        "but keeping all of them due to preflabel-policy=all.",
                        res, lang)
                    continue

                if preflabel_policy == 'shortest':
                    chosen = sorted(sorted(labels), key=len)[0]
                elif preflabel_policy == 'longest':
                    chosen = sorted(sorted(labels), key=len)[-1]
                else:
                    logging.critical(
                        "Unknown preflabel-policy: %s", preflabel_policy)
                    sys.exit(1)

                logging.warning(
                    "Resource %s has more than one prefLabel@%s: "
                    "choosing %s (policy: %s)",
                    res, lang, chosen, preflabel_policy)
                for label in labels:
                    if label != chosen:
                        rdf.remove((res, SKOS.prefLabel, label))
                        rdf.add((res, SKOS.altLabel, label))

    # check overlap between disjoint label properties
    for res, label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.altLabel):
        logging.warning(
            "Resource %s has '%s'@%s as both prefLabel and altLabel; "
            "removing altLabel",
            res, label, label.language)
        rdf.remove((res, SKOS.altLabel, label))
    for res, label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.hiddenLabel):
        logging.warning(
            "Resource %s has '%s'@%s as both prefLabel and hiddenLabel; "
            "removing hiddenLabel",
            res, label, label.language)
        rdf.remove((res, SKOS.hiddenLabel, label))
    for res, label in find_prop_overlap(rdf, SKOS.altLabel, SKOS.hiddenLabel):
        logging.warning(
            "Resource %s has '%s'@%s as both altLabel and hiddenLabel; "
            "removing hiddenLabel",
            res, label, label.language)
        rdf.remove((res, SKOS.hiddenLabel, label))


def check_hierarchy_visit(rdf, node, parent, break_cycles, status):
    if status.get(node) is None:
        status[node] = 1  # entered
        for child in sorted(rdf.subjects(SKOS.broader, node)):
            check_hierarchy_visit(
                rdf, child, node, break_cycles, status)
        status[node] = 2  # set this node as completed
    elif status.get(node) == 1:  # has been entered but not yet done
        if break_cycles:
            logging.info("Hierarchy cycle removed at %s -> %s",
                         localname(parent), localname(node))
            rdf.remove((node, SKOS.broader, parent))
            rdf.remove((node, SKOS.broaderTransitive, parent))
            rdf.remove((node, SKOSEXT.broaderGeneric, parent))
            rdf.remove((node, SKOSEXT.broaderPartitive, parent))
            rdf.remove((parent, SKOS.narrower, node))
            rdf.remove((parent, SKOS.narrowerTransitive, node))
        else:
            logging.info(
                "Hierarchy cycle detected at %s -> %s, "
                "but not removed because break_cycles is not active",
                localname(parent), localname(node))
    elif status.get(node) == 2:  # is completed already
        pass


def check_hierarchy(rdf, break_cycles, keep_related, mark_top_concepts,
                    eliminate_redundancy):
    # check for cycles in the skos:broader hierarchy
    # using a recursive depth first search algorithm
    starttime = time.time()

    top_concepts = sorted(rdf.subject_objects(SKOS.hasTopConcept))
    status = {}
    for cs, root in top_concepts:
        check_hierarchy_visit(
            rdf, root, None, break_cycles, status=status)
    # double check that all concepts were actually visited in the search,
    # and visit remaining ones if necessary
    recheck_top_concepts = False
    for conc in sorted(rdf.subjects(RDF.type, SKOS.Concept)):
        if conc not in status:
            recheck_top_concepts = True
            check_hierarchy_visit(
                rdf, conc, None, break_cycles, status=status)
    if recheck_top_concepts:
        logging.info(
            "Some concepts not reached in initial cycle detection. "
            "Re-checking for loose concepts.")
        setup_top_concepts(rdf, mark_top_concepts)

    # check overlap between disjoint semantic relations
    # related and broaderTransitive
    for conc1, conc2 in sorted(rdf.subject_objects(SKOS.related)):
        if conc2 in sorted(rdf.transitive_objects(conc1, SKOS.broader)):
            if keep_related:
                logging.warning(
                    "Concepts %s and %s connected by both "
                    "skos:broaderTransitive and skos:related, "
                    "but keeping it because keep_related is enabled",
                    conc1, conc2)
            else:
                logging.warning(
                    "Concepts %s and %s connected by both "
                    "skos:broaderTransitive and skos:related, "
                    "removing skos:related",
                    conc1, conc2)
                rdf.remove((conc1, SKOS.related, conc2))
                rdf.remove((conc2, SKOS.related, conc1))

    # check for hierarchical redundancy and eliminate it, if configured to do
    # so
    for conc, parent1 in rdf.subject_objects(SKOS.broader):
        for parent2 in rdf.objects(conc, SKOS.broader):
            if parent1 == parent2:
                continue  # must be different
            if parent2 in rdf.transitive_objects(parent1, SKOS.broader):
                if eliminate_redundancy:
                    logging.warning(
                        "Eliminating redundant hierarchical relationship: "
                        "%s skos:broader %s",
                        conc, parent2)
                    rdf.remove((conc, SKOS.broader, parent2))
                    rdf.remove((conc, SKOS.broaderTransitive, parent2))
                    rdf.remove((parent2, SKOS.narrower, conc))
                    rdf.remove((parent2, SKOS.narrowerTransitive, conc))
                else:
                    logging.warning(
                        "Redundant hierarchical relationship "
                        "%s skos:broader %s found, but not eliminated "
                        "because eliminate_redundancy is not set",
                        conc, parent2)

    endtime = time.time()
    logging.debug("check_hierarchy took %f seconds", (endtime - starttime))


def skosify(*sources, **config):
    """Convert, extend, and check SKOS vocabulary."""

    cfg = Config()
    for key in config:
        if hasattr(cfg, key):
            setattr(cfg, key, config[key])
    config = cfg

    namespaces = config.namespaces
    typemap = config.types
    literalmap = config.literals
    relationmap = config.relations

    logging.debug("Skosify starting. $Revision$")
    starttime = time.time()

    logging.debug("Phase 1: Parsing input files")
    try:
        voc = read_rdf(sources, config.from_format)
    except:
        logging.critical("Parsing failed. Exception: %s",
                         str(sys.exc_info()[1]))
        sys.exit(1)

    inputtime = time.time()

    logging.debug("Phase 2: Performing inferences")
    if config.update_query is not None:
        transform_sparql_update(voc, config.update_query)
    if config.construct_query is not None:
        voc = transform_sparql_construct(voc, config.construct_query)
    if config.infer:
        logging.debug("doing RDFS subclass and properties inference")
        infer.rdfs_classes(voc)
        infer.rdfs_properties(voc)

    logging.debug("Phase 3: Setting up namespaces")
    for prefix, uri in namespaces.items():
        voc.namespace_manager.bind(prefix, uri)

    logging.debug("Phase 4: Transforming concepts, literals and relations")
    # transform concepts, literals and concept relations
    transform_concepts(voc, typemap)
    transform_literals(voc, literalmap)
    transform_relations(voc, relationmap)

    # special transforms for labels: whitespace, prefLabel vs altLabel
    transform_labels(voc, config.default_language)

    # special transforms for collections + aggregate and deprecated concepts
    transform_collections(voc)

    # find/create concept scheme
    cs = get_concept_scheme(voc)
    if not cs:
        cs = create_concept_scheme(voc, config.namespace)
    initialize_concept_scheme(voc, cs, label=config.label,
                              language=config.default_language,
                              set_modified=config.set_modified)

    transform_aggregate_concepts(
        voc, cs, relationmap, config.aggregates)
    transform_deprecated_concepts(voc, cs)

    logging.debug("Phase 5: Performing SKOS enrichments")
    # enrichments: broader <-> narrower, related <-> related
    enrich_relations(voc, config.enrich_mappings,
                     config.narrower, config.transitive)

    logging.debug("Phase 6: Cleaning up")
    # clean up unused/unnecessary class/property definitions and unreachable
    # triples
    if config.cleanup_properties:
        cleanup_properties(voc)
    if config.cleanup_classes:
        cleanup_classes(voc)
    if config.cleanup_unreachable:
        cleanup_unreachable(voc)

    logging.debug("Phase 7: Setting up concept schemes and top concepts")
    # setup inScheme and hasTopConcept
    setup_concept_scheme(voc, cs)
    setup_top_concepts(voc, config.mark_top_concepts)

    logging.debug("Phase 8: Checking concept hierarchy")
    # check hierarchy for cycles
    check_hierarchy(voc, config.break_cycles,
                    config.keep_related, config.mark_top_concepts,
                    config.eliminate_redundancy)

    logging.debug("Phase 9: Checking labels")
    # check for duplicate labels
    check_labels(voc, config.preflabel_policy)

    processtime = time.time()

    logging.debug("reading input file took  %d seconds",
                  (inputtime - starttime))
    logging.debug("processing took          %d seconds",
                  (processtime - inputtime))

    logging.debug("Phase 10: Writing output")

    return voc
