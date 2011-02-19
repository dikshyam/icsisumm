from inference import *

def make_concepts_ie(id, path, sents, query, options):
    """
    """
    
    query_words = set(util.porter_stem_sent(util.remove_stopwords(util.tokenize(fix_text(query)))).split())
    seen_sents = set()
    all_concepts = collections.defaultdict(set)
    ## different processing for set A and set B
    if '-B' in id: 
        first_weight = 2
        count_thresh = 4
        query_thresh = 0
    else: 
        first_weight = 1
        count_thresh = 3
        query_thresh = 1
    ie_count_thresh = 1
    if options.experiment.startswith("ie-valued-concepts"):
        current = 0
        ie_valued_concepts = 0
        for line in open(options.concepts + "/" + id + options.extension).xreadlines():
            line = line.strip()
            if line == "<TEXT>" or line == "</TEXT>": continue
            if "|" in line:
                parts = ['__ie__:' + x for x in line.split("|")[1:]]
                sents[current].ie_valued_concepts = {}
                for part in parts:
                    found = re.match("(.*)\[([\d\.]*),([\d\.]*)\]", part)
                    if found:
                        sents[current].ie_valued_concepts[found.group(1)] = float(found.group(2))
                        print found.group(1), found.group(2)
                    else:
                        print >>sys.stderr, "WARNING:", part
            else:
                sents[current].ie_valued_concepts = {}
            ie_valued_concepts += len(sents[current].ie_valued_concepts)
            current += 1
        print >>sys.stderr, "ie_valued_concepts=%d" % ie_valued_concepts
    elif options.experiment.startswith("ie-concepts"):
        current = 0
        ie_concepts = 0
        for line in open(options.concepts + "/" + id + options.extension).xreadlines():
            line = line.strip()
            if line == "<TEXT>" or line == "</TEXT>": continue
            if "|" in line:
                parts = ['__ie__:' + x for x in line.split("|")[1:]]
                sents[current].ie_concepts = set(parts)
            else:
                sents[current].ie_concepts = set()
            ie_concepts += len(sents[current].ie_concepts)
            current += 1
        print >>sys.stderr, "ie_concepts=%d" % ie_concepts

    for sent in sents:
        
        ## store this sentence's concepts
        sent.concepts = set()
        if options.experiment == "ie-concepts":
            concepts = sent.ie_concepts
        elif options.experiment == "ie-concepts+regular-concepts":
            concepts = sent.ie_concepts
            concepts |= set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        else:
            concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        #concepts = set(util.get_skip_bigrams(sent.tok2, 4, bounds=False, as_string=True))

        ## get query overlap
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)

        ## aggregate all concepts
        if not sent.skip_concepts and len(query_overlap) >= query_thresh:
            for concept in concepts:
                if sent.order == 0: all_concepts[concept].add('<first>_' + sent.doc)
                #if len(query_overlap) > 3: all_concepts[concept].add('<query>_' + sent.doc)
                else: all_concepts[concept].add(sent.doc)

        ## ignore some sents
        skip = False
        #if not sent.new_par: skip = True
        if sent.length < 10: skip = True
        if sent.tok in seen_sents: skip = True
        #if sent.order > 0: skip = True
        if re.match('^["(].*[")]$', sent.orig): skip = True
        if sent.unresolved: 
            skip = True
        #if sent.ignore: skip = True
        if skip or sent.skip: continue
        
        seen_sents.add(sent.tok)
        sent.concepts = concepts

    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        firsts = len([1 for d in docs if '<first>_' in d])
        count = count + (first_weight * firsts)
        if concept.startswith('__ie__:'):
            if count < ie_count_thresh: continue
        else:
            if count < count_thresh: continue
        if util.is_just_stopwords(concept.split('_')): continue
        if concept.startswith('__ie__:'):
            count *= options.fudge
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    for sent in sents:
        sent.concepts = sent.concepts.intersection(final_concept_set)
        
    return create_ilp_output(sents, final_concepts, path+id)

def make_summary_ie(data_path, id, out_path, summ_path, length, options):
    
    sents = load_sents(data_path, id)
    num_filtered = 0
    if options.experiment == "filter1":
        current = 0
        for line in open(options.filter1 + "/" + id + ".sent.ie.filter1").xreadlines():
            line = line.strip()
            if line == "<TEXT>" or line == "</TEXT>": continue
            if line.endswith("|0"):
                sents[current].skip = True
                num_filtered += 1
            current += 1
        sys.stderr.write('filtered %d/%d\n' % (num_filtered, len(sents)))
    elif options.experiment == "filter2":
        current = 0
        for line in open(options.filter2 + "/" + id + ".sent.ie.filter2").xreadlines():
            line = line.strip()
            if line == "<TEXT>" or line == "</TEXT>": continue
            if line.endswith("|0"):
                sents[current].skip = True
                num_filtered += 1
            current += 1
        sys.stderr.write('filtered %d/%d\n' % (num_filtered, len(sents)))
    elif options.experiment == "shortened":
        current = 0
        for line in open(options.shortened + "/" + id + ".sent").xreadlines():
            line = line.strip()
            if line == "<TEXT>" or line == "</TEXT>": continue
            if not line.endswith("|1"):
                sents[current].skip = True
                num_filtered += 1
            current += 1
        sys.stderr.write('filtered %d/%d\n' % (num_filtered, len(sents)))
    query = open(data_path + id + '.query').read().replace('\n', ' ')
    sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file, atleast_file = make_concepts_ie(id, out_path, sents, query, options)
    if num_filtered < len(sents):
        if options.decoder == "localsolver":
            summ_sent_nums = decoder_localsolver.decode(length, length_file, sentence_concepts_file, concept_weights_file, group_file, depend_file, atleast_file)
        else:
            summ_sent_nums = decoder2.decode(length, length_file, sentence_concepts_file, concept_weights_file, group_file, depend_file, atleast_file)

        summary = [sents[i] for i in summ_sent_nums]
        summary = order(summary)
        summary_fh = open(summ_path + id, 'w')
        for sent in summary:
            summary_fh.write('%s\n' %sent)
    else:
        open(summ_path + id, 'w').close() # empty summary

##########################
if __name__ == '__main__':
    parser = OptionParser(usage="USAGE: %prog [options]")
    parser.add_option('-e', '--experiment', dest='experiment', type='str', help='experiments: filter1, filter2, ie-concepts, ie-concepts+regular-concepts, shortened, eval', default="")
    parser.add_option('--filter1', dest='filter1', type='str', help='directory for filter1 experiment')
    parser.add_option('--filter2', dest='filter2', type='str', help='directory for filter2 experiment')
    parser.add_option('--concepts', dest='concepts', type='str', help='directory for ie-concepts experiments')
    parser.add_option('--ext', dest='extension', type='str', help='file extension for ie experiments', default=".sent.ie.concept")
    parser.add_option('--fudge', dest='fudge', type='float', help='fudge factor', default=1.0)
    parser.add_option('--shortened', dest='shortened', type='str', help='location of .sent files for shortening experiment')
    (options, args) = get_options(parser)

    if options.experiment != 'eval':
        os.popen('mkdir -p %s' %options.outpath + '/summary/')
        ids = get_topic_ids(options.inputpath)
        for id in ids:
            if '-C' in id: continue
            make_summary_ie(options.inputpath, id, options.outpath, options.outpath + '/summary/', options.length, options)

    else:
        import evaluate_duc
        sys.stderr.write('\nROUGE results\n')
        config_file = evaluate_duc.create_config(options.manpath, options.outpath + '/summary/', chop_annotator_id=True)
        ROUGE_SCORER = 'scoring/ROUGE-1.5.5/ROUGE-1.5.5_faster.pl'
        evaluate_duc.run_rouge(ROUGE_SCORER, config_file, options.length, verbose=True)
        os.remove(config_file)
