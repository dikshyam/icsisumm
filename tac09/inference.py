import sys, os, util, re, collections
import prob_util

class Sentence:
    def __init__(self, id, order, orig, doc, tok=None, parse=None, par=None, unresolved=False):
        self.id = id
        self.order = order
        self.orig = orig
        self.tok = tok
        self.tok2 = util.porter_stem_sent(util.tokenize(fix_text(self.orig)))
        self.doc = doc
        self.parse = parse
        self.new_par = (par == '1')
        self.length = len(self.orig.split())
        self.ignore = False
        self.depends = set()
        self.groups = []
        self.skip = False
        self.unresolved = unresolved
        self.atleast = ""

    def __str__(self):
        return self.orig

def load_gold_sents(path, id):
    data_path = path + id
    orig_fh = open(data_path + '.gold_sent')
    doc_fh = open(data_path + '.gold_doc')
    
    sents = []
    count = 0
    order = 0
    prev_doc = ''
    
    while True:
        [orig, doc] = map(str.strip, [orig_fh.readline(), doc_fh.readline()])
        if not (orig or doc): break
        if doc != prev_doc: order = 0
        sents.append(Sentence(count, order, orig, doc))
        count += 1
        order += 1
        prev_doc = doc
        
    return sents

def load_unresolved(sents, path, id):
    unresolved_fh = open(path + id + ".sent.tok.unresolved")
    sentence = 0
    for sent in sents:
        line = unresolved_fh.readline()
        if float(line) > 0.4:
            sent.unresolved = True
        #if line.startswith("1"):
        #    sent.depends.add(1111111111)
        sentence += 1

def load_sents_compress(path, id):
    
    data_path = path + id
    orig_fh = open(data_path + '.sent.tok.compressed')
    unresolved_fh = open(data_path + '.sent.tok.compressed.unresolved')
    groups_fh = open(data_path + '.sent.tok.groups')
    
    sents = []
    count = 0
    prev_doc = ''
    while True:
        [orig, unresolved, groups] = map(lambda x: x.readline().strip(), [orig_fh, unresolved_fh, groups_fh])
        if not (orig or groups or unresolved): break
        sents.append(Sentence(count, 0, orig, None, unresolved=(float(unresolved) > 0.4)))#unresolved.startswith("1")))
        for token in groups.split():
            sents[-1].groups.append(token)
        count += 1

    sys.stderr.write('>compressed: got [%d] sentences\n' %(count))
    return sents


def load_sents(path, id):
    
    data_path = path + id
    orig_fh = open(data_path + '.sent')
    tok_fh = open(data_path + '.sent.tok')
    doc_fh = open(data_path + '.doc')
    par_fh = open(data_path + '.par')
    parse_fh = open(data_path + '.sent.tok.parsed')
    
    sents = []
    count = 0
    order = 0
    prev_doc = ''
    while True:
        [doc, orig, tok, parse, par] = map(str.strip, [doc_fh.readline(), orig_fh.readline(), 
                                                       tok_fh.readline(), parse_fh.readline(), par_fh.readline()])
        if not (doc or orig or tok or parse): break
        if doc != prev_doc: order = 0
        sents.append(Sentence(count, order, orig, doc, tok, parse, par))
        count += 1
        order += 1
        prev_doc = doc

    sys.stderr.write('topic [%s]: got [%d] sentences\n' %(id, count))
    return sents

def fix_text(text):
    """
    prepare text for ngram concept extraction
    """
    t = text
    t = util.remove_punct(t)
    t = re.sub('\s+', ' ', t)
    return t.lower()

def create_ilp_output(sents, concepts, path):

    ## output concepts in each sentence and lengths
    sentence_concepts_file = path + '.sent.concepts'
    sentence_group_file = path + '.sent.groups'
    sentence_depend_file = path + '.sent.depend'
    sentence_atleast_file = path + '.sent.atleast'
    length_file = path + '.sent.lengths'
    orig_file = path + '.sent.orig'
    sent_fh = open(sentence_concepts_file, 'w')
    length_fh = open(length_file, 'w')
    orig_fh = open(orig_file, 'w')
    group_fh = open(sentence_group_file, 'w')
    depend_fh = open(sentence_depend_file, 'w')
    atleast_fh = open(sentence_atleast_file, 'w')
    used_concepts = set()
    for sent in sents:
        #if len(sent.concepts) == 0: continue
        used_concepts.update(sent.concepts)
        sent_fh.write(' '.join(list(sent.concepts)) + '\n')
        length_fh.write('%d\n' %sent.length)
        orig_fh.write('%s\n' %sent.orig)
        group_fh.write(' '.join([str(x) for x in sent.groups]) + '\n')
        depend_fh.write(' '.join([str(x) for x in sent.depends]) + '\n')
        atleast_fh.write(str(sent.atleast) + "\n")
    length_fh.close()
    sent_fh.close()
    orig_fh.close()
    depend_fh.close()
    group_fh.close()
    atleast_fh.close()
    
    ## output concept weights
    concept_weights_file = path + '.concepts'
    concept_fh = open(concept_weights_file, 'w')
    for concept, value in concepts.items():
        #if not concept in used_concepts: continue
        concept_fh.write('%s %1.7f\n' %(concept, value))
    concept_fh.close()
        
    return sentence_concepts_file, concept_weights_file, length_file, orig_file, sentence_group_file, sentence_depend_file, sentence_atleast_file

def make_concepts_gold(id, path, sents, gold_sents):
    
    ## get gold concepts
    all_concepts = collections.defaultdict(set)
    for sent in gold_sents:
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))      
        for concept in concepts:
            all_concepts[concept].add(sent.doc)
            
    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        if util.is_just_stopwords(concept.split('_')): continue
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    ## get sentence concepts
    seen_sents = set()
    for sent_index in range(len(sents)):
        sent = sents[sent_index]
        sent.concepts = set([])
        
        ## skip some sents
        skip = False
        #if sent.order >= 3: skip = True
        if not sent.new_par: skip = True
        if sent.length < 20: skip = True
        
        if sent.orig in seen_sents: skip = True
        if sent.length <= 5: skip = True        
        if skip: continue
        
        seen_sents.add(sent.orig)
        s = util.porter_stem_sent(util.tokenize(fix_text(sent.orig)))
        concepts = set(util.get_ngrams(s, 2, bounds=False, as_string=True))
        sent.concepts = concepts.intersection(final_concept_set)
        
    return create_ilp_output(sents, final_concepts, path+id)


def make_concepts_baseline(id, path, sents, query):
    """
    only use first sentences
    TODO: choose best of first 3
    """
    
    query_words = set(util.porter_stem_sent(util.remove_stopwords(util.tokenize(fix_text(query)))).split())
    seen_sents = set()
    all_concepts = collections.defaultdict(set)
    max_order = 0
    for sent in sents:
        
        ## store this sentence's concepts
        sent.concepts = set([])
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))

        ## get query overlap
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)

        ## aggregate all concepts
        if len(query_overlap) > 0:
            for concept in concepts:
                all_concepts[concept].add(sent.doc)

            if sent.order == 0:
                for concept in concepts:
                    all_concepts[concept].add(sent.doc + 'first')

        ## ignore some sents
        if sent.order == 0: max_order = 0
        skip = False
        if sent.length <= 5: skip = True
        if sent.tok in seen_sents: skip = True
        #if sent.length < 20: skip = True
        if sent.order > max_order or max_order > 0: 
            skip = True
            max_order = 0
        
        if skip: 
            max_order += 1
            continue
        
        #print sent.order, max_order, sent.doc, sent
        seen_sents.add(sent.tok)
        sent.concepts = concepts

    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        #if count < 3: continue
        if util.is_just_stopwords(concept.split('_')): continue
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    for sent in sents:
        sent.concepts = sent.concepts.intersection(final_concept_set)
        
    return create_ilp_output(sents, final_concepts, path+id)
    
def make_concepts(id, path, sents, query):
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

    for sent in sents:
        
        ## store this sentence's concepts
        sent.concepts = set()
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        #concepts = set(util.get_skip_bigrams(sent.tok2, 4, bounds=False, as_string=True))

        ## get query overlap
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)

        ## aggregate all concepts
        if len(query_overlap) >= query_thresh:
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
        if skip: continue
        
        seen_sents.add(sent.tok)
        sent.concepts = concepts

    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        firsts = len([1 for d in docs if '<first>_' in d])
        count = count + (first_weight * firsts)
        if count < count_thresh: continue
        if util.is_just_stopwords(concept.split('_')): continue
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    for sent in sents:
        sent.concepts = sent.concepts.intersection(final_concept_set)
        
    return create_ilp_output(sents, final_concepts, path+id)

def make_concepts_compress(id, path, sents, query, compressed_sents):
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

    for sent in sents:
        
        ## store this sentence's concepts
        sent.concepts = set()
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        #concepts = set(util.get_skip_bigrams(sent.tok2, 4, bounds=False, as_string=True))

        ## get query overlap
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)

        ## aggregate all concepts
        if len(query_overlap) >= query_thresh:
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
        #if sent.ignore: skip = True
        if skip: continue
        
        seen_sents.add(sent.tok)
        sent.concepts = concepts

    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        firsts = len([1 for d in docs if '<first>_' in d])
        count = count + (first_weight * firsts)
        if count < count_thresh: continue
        if util.is_just_stopwords(concept.split('_')): continue
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    for sent in sents:
        sent.concepts = sent.concepts.intersection(final_concept_set)
        
    for sent in compressed_sents:
        sent.concepts = set([])
        if sent.unresolved: continue
        if sent.length < 10: continue
        if re.match('^["(].*[")]$', sent.orig): continue
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        sent.concepts = concepts.intersection(final_concept_set)

    return create_ilp_output(compressed_sents, final_concepts, path+id)

def make_concepts_compress2(id, path, sents, query, compressed_sents):
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

    for sent in sents:
        
        ## store this sentence's concepts
        sent.concepts = set()
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))

        ## get query overlap
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)

        ## aggregate all concepts
        if len(query_overlap) >= query_thresh:
            for concept in concepts:
                if sent.order == 0: all_concepts[concept].add('first' + sent.doc)
                else: all_concepts[concept].add(sent.doc)

        ## ignore some sents
        skip = False
        #if not sent.new_par: skip = True
        #if sent.length <= 20: skip = True
        if sent.tok in seen_sents: skip = True
        #if sent.ignore: skip = True
        if skip: continue
        
        seen_sents.add(sent.tok)
        sent.concepts = concepts

    ## create final concept set
    final_concepts = {}
    for concept, docs in all_concepts.items():
        count = len(docs)
        firsts = len([1 for d in docs if 'first' in d])
        count = count + (first_weight * firsts)
        if count < count_thresh: continue
        if util.is_just_stopwords(concept.split('_')): continue
        final_concepts[concept] = count
    final_concept_set = set(final_concepts.keys())

    for sent in sents:
        sent.concepts = sent.concepts.intersection(final_concept_set)
        
    for sent in compressed_sents:
        sent.concepts = set([])
        if sent.unresolved: continue
        if sent.length < 10: continue
        if re.match('^["(].*[")]$', sent.orig): skip = True
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        sent.concepts = concepts.intersection(final_concept_set)
        
    return create_ilp_output(compressed_sents, final_concepts, path+id)

def make_concepts_exp(id, path, sents, query):
    """
    """
    
    query_words = set(util.porter_stem_sent(util.remove_stopwords(util.tokenize(fix_text(query)))).split())

    ## get sentence values
    sent_vals = prob_util.Counter()
    for sent in sents:
        query_overlap = set(util.remove_stopwords(sent.tok2.split())).intersection(query_words)
        sent_vals[sent] = max(0, len(query_overlap))
        #if sent.relevance < 0.3: sent_vals[sent] = 0.0
        #else: sent_vals[sent] = 100000**sent.relevance
        concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
        sent.concepts = set()
        for concept in concepts:
            if util.is_just_stopwords(concept.split('_')): continue
            sent.concepts.add(concept)
    sent_vals = prob_util.normalize(sent_vals)

    ## get concept values
    concept_vals = prob_util.Counter()
    for sent in sents:
        for concept in sent.concepts:
            concept_vals[concept] += sent_vals[sent]            
    concept_vals = prob_util.normalize(concept_vals)
    
    iter = 0
    while True:
        iter += 1
        se = prob_util.entropy(sent_vals)
        ce = prob_util.entropy(concept_vals)
        print 'iter [%d] sent entropy [%1.4f] concept entropy [%1.4f]' %(iter, se, ce)
        if iter >= 1: break
        
        ## get sent vals again
        sent_vals = prob_util.Counter()
        for sent in sents:
            for concept in sent.concepts:
                sent_vals[sent] += concept_vals[concept]
        sent_vals = prob_util.normalize(sent_vals)
        
        ## get concept values
        concept_vals = prob_util.Counter()
        for sent in sents:
            for concept in sent.concepts:
                concept_vals[concept] += sent_vals[sent]            
        concept_vals = prob_util.normalize(concept_vals)
    
    sorted_sents = sent_vals.sortedKeys()
    #for sent in sorted_sents:
    #    print sent_vals[sent], sent.order, sent.new_par, sent

    sorted_concepts = concept_vals.sortedKeys()
    #for concept in sorted_concepts:
    #    print concept_vals[concept], concept
        
    ## create final concept set
    final_concepts = {}
    for concept in sorted_concepts:
        val = concept_vals[concept]
        #if val < 0.00001: continue
        final_concepts[concept] = val
    final_concept_set = set(final_concepts.keys())

    ## get final sentence list and their concepts
    seen_sents = set()
    for sent in sents:
        skip = False
        if sent.length <= 5: skip = True
        if sent in seen_sents: skip = True
        if sent.order > 0: skip = True
        else: seen_sents.add(sent)
        if skip: sent.concepts = set()
        else: sent.concepts = sent.concepts.intersection(final_concept_set)        
        
    return create_ilp_output(sents, final_concepts, path+id)



def get_topic_ids(path):
    ids = map(str.strip, os.popen('ls %s*.doc' %path).readlines())
    ids = [f.split('.')[0] for f in map(os.path.basename, ids)]
    return ids

def order_func(x, y):
    if x.order == 0 and y.order == 0:
        if x.length > y.length:
            return -1
        elif x.length < y.length:
            return 1
        return 0
    if x.order == 0 and y.order != 0:
        return -1
    if y.order == 0 and x.order != 0:
        return 1
    return 0

def order(sents):
    """
    TODO: order summary sentences
    """
    
    ordered = []
    
    ## is there a first sent
    first_sents = [int(sent.order == 0) * sent.length for sent in sents]
    if sents[0].order != 0 and sum(first_sents) >= 1:
        f = max(zip(first_sents, sents))[1]
        ordered.append(f)
        sents.remove(f)
        for sent in sents[:]:
            if sent.doc == f.doc:
                ordered.append(sent)
                sents.remove(sent)
    ordered += sents
    return ordered


import firstsent
def make_summary(data_path, id, out_path, summ_path, length):
    
    ## load sents
    sents = load_sents(data_path, id)
    #load_coref(sents, '/u/yangl/raid_array/TAC/tac08_v1_coref_mark_diffsent/', id)
    #load_unresolved(sents, '/u/favre/work/summarization/tac09/unresolved/tac08_v4/', id)
    load_unresolved(sents, '/u/favre/work/summarization/tac09/unresolved/tac09_v4/', id)
    #compressed_sents = load_sents_compress("/u/favre/work/summarization/tac09/system4/tac09_compressed_v4/", id)
    #for sent in compressed_sents:
    #    group = int(sent.groups[0])
    #    sent.order = sents[group].order
        #if sent.order == 0 and sent.length > 20:
        #    sent.atleast = "1"
        #if sent.length < 15:
        #    sent.depends.add(9999999)
        #if sent.orig.startswith('"') and sent.orig.endswith('"'):
        #    sent.depends.add(9999999)
    
    ## load query
    query = open(data_path + id + '.query').read().replace('\n', ' ')
    #query = open('/u/yangl/raid_array/TAC/query_expansion/expanded/08/' + id + '.query.tok').read().replace('\n', ' ')
    
    ## load gold sentences
    #gold_sents = load_gold_sents(data_path, id)
    
    ## load similarity scores
#    sim_path = '/n/whiskey/xf/drspeech/GALE/shasha/TAC08/redundancy/score/' + id + '.sim'
#    if not os.path.isfile(sim_path): sim_scores = None
#    else: sim_scores = [max(map(float, line.split())) for line in open(sim_path).read().splitlines()]
#    if sim_scores and len(sim_scores) == len(sents):
#        ordered = zip(sim_scores, sents)
#        ordered.sort()
#        count = 0
#        for val, sent in ordered:
#            count += 1
#            if count > 100: sent.ignore = True
    
    ## get first sentence classifier scores
#    data = map(float, open(data_path + id + '.firstsent').read().splitlines())
#    if len(data) == len(sents):
#        ordered = zip(data, sents)
#        ordered.sort()
#        ordered.reverse()
#        count = 0
#        for val, sent in ordered:
#            count += 1
#            if count > 20: sent.ignore = True

    ## get sentence relevance scores
#    data = map(float, open(data_path + id + '.score').read().splitlines())
#    if len(data) == len(sents):
#        ordered = zip(data, sents)
#        ordered.sort()
#        ordered.reverse()
#        count = 0
#        for val, sent in ordered:
#            count += 1
#            #if count > 100: sent.ignore = True
#            sent.relevance = val

    ## create concepts
    #sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file, atleast_file = make_concepts_compress(id, out_path, sents, query, compressed_sents)
    sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file, atleast_file = make_concepts(id, out_path, sents, query)
    #sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file = make_concepts_baseline_depends(id, out_path, sents, query)
    #sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file = make_concepts_baseline_depends(id, out_path, sents, query)
    #sentence_concepts_file, concept_weights_file, length_file, orig_file, group_file, depend_file = make_concepts_gold(id, out_path, sents, gold_sents)

    ## run decoder
    cmd = 'python2.5 decoder2.py %d %s %s %s %s %s %s' %(length, length_file, sentence_concepts_file, concept_weights_file, group_file, depend_file, atleast_file)
    summ_sent_nums = map(int, os.popen(cmd).read().splitlines())
    #usable_sents = open(orig_file).read().splitlines()
    #summary = [usable_sents[i] for i in summ_sent_nums]
    #summary = [compressed_sents[i] for i in summ_sent_nums]
    summary = [sents[i] for i in summ_sent_nums]
    
    ## order sentences
    summary = order(summary)
    ## output summary goes in the summary directory in the out_path
    if 'tac08' in out_path: id = id[:5] + id[6:]
    summary_fh = open(summ_path + id, 'w')
    for sent in summary:
        summary_fh.write('%s\n' %sent)

if __name__ == '__main__':
    
    from optparse import OptionParser
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage=usage)

    parser.add_option('-t', '--task', dest='task', type='str',
                      help='tasks: u09, u08, u07, m07, m06, m05')
    parser.add_option('--docpath', dest='docpath', type='str',
                      help='source document path')
    parser.add_option('--manpath', dest='manpath', type='str',
                      help='manual summary path')
    parser.add_option('-c', '--cheat', dest='cheat', default=False, action='store_true',
                      help='get concepts from gold summaries to get maximum ROUGE results (cheating)')
    parser.add_option('-l', '--length', dest='length', type='int',
                      help='maximum number of words in summaries')
    (options, args) = parser.parse_args()
    
    ## new output
    out_path = 'tac09_out_normal/'
    summ_path = out_path + 'summary/'
    os.popen('rm -rf %s' %out_path)
    os.popen('mkdir %s' %out_path)
    os.popen('mkdir %s' %summ_path)

    ## where the data is
    data_path = '/u/dgillick/workspace/summ/bourbon/tac09_v4/'
    #data_path = '/u/dgillick/workspace/summ/bourbon/duc07_v3/'
    
    ## parameters
    length = 100
    
    ## run through all topics
    ids = get_topic_ids(data_path)
    for id in ids:
        if '-C' in id: continue
        make_summary(data_path, id, out_path, summ_path, length)
        
    ## ROUGE evaluation
    ROUGE_SCORER = '/u/favre/work/summarization/tools/ROUGE-1.5.5/ROUGE-1.5.5_faster.pl'
    man_source = {}
    man_source['u08'] = '/u/favre/work/summarization/tac08_results/ROUGE/models/' 
    man_source['u07'] = '/u/drspeech/data/DUC/07/duc07.results.data/results/updateEval/ROUGE/models/'
    man_source['m07'] = '/u/drspeech/data/DUC/07/duc07.results.data/results/mainEval/ROUGE/models/'
    man_source['m06'] = '/u/drspeech/data/DUC/06/results/NIST/NISTeval/ROUGE/models/'
    man_source['m05'] = '/u/drspeech/data/DUC/05/results/NIST/results/ROUGE/models/'
    
    #sys.exit()
    manual_path = man_source['u08']
    import evaluate_duc
    sys.stderr.write('\nROUGE results\n')
    config_file = evaluate_duc.create_config(manual_path, summ_path)
    evaluate_duc.run_rouge(ROUGE_SCORER, config_file, length, verbose=False)
    os.remove(config_file)
