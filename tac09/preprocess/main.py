import sys, os, re, time
import framework, concept_mapper, ordering, berkeleyparser, compression, util, prob_util, ir
from globals import *
import scipy, ilp, text

## use these to specify source document paths
doc_source = {}
doc_source['u09'] = '/u/favre/work/summarization/tac09_data/UpdateSumm09_test_docs_files/'
doc_source['u08'] = '/u/favre/work/summarization/tac08_data/UpdateSumm08_test_docs_files/'
doc_source['u07'] = '/u/drspeech/data/DUC/07/duc07.results.data/testdata/duc2007_testdocs/update/'
doc_source['m07'] = '/u/drspeech/data/DUC/07/duc07.results.data/testdata/duc2007_testdocs/main/'
doc_source['m06'] = '/u/drspeech/data/DUC/06/testdata/duc2006_docs/'
doc_source['m05'] = '/u/drspeech/data/DUC/05/testdata/duc2005_docs/'

## use these to specify manual summary paths
man_source = {}
man_source['u08'] = '/u/favre/work/summarization/tac08_results/ROUGE/models/' 
man_source['u07'] = '/u/drspeech/data/DUC/07/duc07.results.data/results/updateEval/ROUGE/models/'
man_source['m07'] = '/u/drspeech/data/DUC/07/duc07.results.data/results/mainEval/ROUGE/models/'
man_source['m06'] = '/u/drspeech/data/DUC/06/results/NIST/NISTeval/ROUGE/models/'
man_source['m05'] = '/u/drspeech/data/DUC/05/results/NIST/results/ROUGE/models/'

class Task:
    """
    Class for holding paths to the important Task elements
    self.topic_file     xml/sgml file specifying problems (TAC/DUC)
    self.data_path      path containing all source documents
    self.manual_path    path containing manual (human; gold) summaries
    """
    def __init__(self, task_name, topic_file, doc_path, manual_path=None, length_limit=250):
        self.name = task_name
        self.topic_file = topic_file
        self.doc_path = doc_path
        self.manual_path = manual_path
        self.length_limit = length_limit
        self.data_pickle = '%s/%s_data.pickle' %(DATA_ROOT, self.name)
        self.problems = None

def parse_options():
    """
    set up command line parser options
    """
    
    from optparse import OptionParser
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage=usage)

    parser.add_option('-t', '--task', dest='task', type='str',
                      help='tasks: u09, u08, u07, m07, m06, m05')
    parser.add_option('--docpath', dest='docpath', type='str',
                      help='source document path')
    parser.add_option('--manpath', dest='manpath', type='str',
                      help='manual summary path')
    parser.add_option('-d', '--dataroot', dest='dataroot', type='str', default=DATA_ROOT,
                      help='dataroot: directory to store partial state')
    parser.add_option('-c', '--cheat', dest='cheat', default=False, action='store_true',
                      help='get concepts from gold summaries to get maximum ROUGE results (cheating)')
    parser.add_option('-u', '--units', dest='units', default='n2', type='str',
                      help='units: n1 (unigrams), n2 (bigrams), su4 (skip bigrams + unigrams)')
    parser.add_option('-l', '--length', dest='length', type='int',
                      help='maximum number of words in summaries')
    parser.add_option('--compress', dest='compress', default=False, action='store_true',
                      help='use sentence compression when generating summaries')
    parser.add_option('--reload', dest='reload', default=False, action='store_true',
                      help='reload document data from scratch')
    parser.add_option('--output', dest='output', default='%s/%s/out' %(ROOT, 'output'), type='str',
                      help='output directory for summaries')
    parser.add_option('--ir', dest='ir', default=0, type='int',
                      help='number of documents to retrieve using IR')
    (options, args) = parser.parse_args()

    ## setup a Task instance
    if not options.task in ['u09', 'u08', 'u07', 'm07', 'm06', 'm05']:
        parser.error('unrecognized task [%s], use --help to get a list of valid tasks' %options.task)

    if not options.docpath:
        if options.task in doc_source: options.docpath = doc_source[options.task]
        else: parser.error('must specify a document path')

    if not options.manpath:
        if options.task in man_source: options.manpath = man_source[options.task]
        else:
            if options.cheat: parser.error('must specify a manual summary path to run a cheating experiment')

    if not options.length:
        if options.task.startswith('u'): options.length = 100
        else: options.length = 250
        
    topics_file = '%s/topics_%s' %(STATIC_DATA_ROOT, options.task)
    
    task = Task(options.task, topics_file, options.docpath, options.manpath, options.length)
    
    ## check valid units
    if not options.units in set(['n1', 'n2', 'n3', 'n4', 'su4']):
        parser.error('unrecognized unit selection [%s], use --help to get a list of valid units' %options.units)

    ## create data root directory
    if options.dataroot:
        os.popen('mkdir -p %s' %options.dataroot)
        task.data_pickle = '%s/%s_data.pickle' %(options.dataroot, task.name)

    return options, task

def run_standard(options, max_sents=10000):

    ## create output directory
    try: os.popen('rm -rf %s' %options.output)
    except: pass
    try: os.popen('mkdir -p %s' %options.output)
    except:
        sys.stderr.write('Error: could not create output directory [%s]\n')
        sys.exit()

    ## summarize!
    sys.stderr.write('generating summaries for task [%s]\n' %options.task)
    sys.stderr.write('length limit [%d]\n' %task.length_limit)
    sys.stderr.write('writing output to [%s]\n' %options.output)

    map_times, run_times = {}, {}
    
    ## sentence compression
    if options.compress:
        for problem in task.problems:
            if not '-A' in problem.id: continue
            sys.stderr.write("%s %d\n" % (problem.id, sum([len(doc.sentences) for doc in problem.new_docs])))
            #mapper = concept_mapper.HeuristicMapper(problem, "n2")
            mapper = concept_mapper.CheatingMapper(problem, "n2")
            mapper.map_concepts()
            mapper.choose_sents()
            concept_weights = mapper.concept_weights
            #print concept_weight
            #program = framework.build_program(problem, concept_weight, length=task.length_limit, sentences=mapper.relevant_sent_sets[0])
            program = framework.build_alternative_program(problem, concept_weights, length=task.length_limit, sentences=mapper.relevant_sents, longuest_candidate_only=False)
            # run the program and get the output
            program.debug = 0
            program.run()
            #selection = framework.get_program_result(program)
            selection = []
            for variable in program.output:
                if re.match(r'^s\d+$', variable) and program.output[variable] == 1:
                    selection.append(program.binary[variable])
            selection = ordering.by_date(selection)
            summary = "\n".join(sentence.original for sentence in selection)
            #summary = compression.addAcronymDefinitionsToSummary(summary, program.acronyms)

            ## TAC id convention is annoying
            output_id = problem.id
            if options.task in ['u09', 'u08']: output_id = problem.id[:5]+problem.id[6:]
            output_file = open('%s/%s' % (options.output, output_id), 'w')
            output_file.write(summary)
            output_file.close()
    
    elif options.mcd:
        for problem in task.problems:
            num_problem_sentences = len(problem.get_new_sentences())
            if num_problem_sentences < 500: continue
            used_sent_count = 0
            for sentence in problem.get_new_sentences():
                used_sent_count += 1
                sentence.set_text(sentence.original)
                if used_sent_count < max_sents: sentence.used = True
                else: sentence.used = False
            problem.query.set_text(problem.query.original)
            sys.stdout.write("%s %d\n" % (problem.id, sum([len(doc.sentences) for doc in problem.new_docs])))
    
            # compute idf values
            word_idf = {}
            for doc in problem.new_docs:
                seen_words = {}
                for sentence in doc.sentences:
                    if not sentence.used: continue
                    for word in sentence.no_stop_freq:
                        if word not in seen_words: seen_words[word] = 1
                for word in seen_words:
                    if word not in word_idf: word_idf[word] = 1
                    else: word_idf[word] += 1
            for word in word_idf:
                word_idf[word] = 1.0 / word_idf[word]
            
            # compare sentences to centroid and derive McDonald's relevance score
            sentences = []
            index = 0
            for doc in problem.new_docs:
                doc_text = " ".join([sentence.original for sentence in doc.sentences if sentence.used])
                centroid = text.Sentence(doc_text)
                centroid.compute_norm()
                problem.query.compute_norm()
                for sentence in doc.sentences:
                    if not sentence.used: continue
                    sentence.compute_norm()
                    sentence.rel_score = sentence.sim_cosine(centroid, word_idf) + 1 / (sentence.order + 1)
                    #sentence.rel_score = sentence.sim_cosine(centroid, word_idf) + sentence.sim_cosine(problem.query, word_idf)
                    sentences.append(sentence)
                    sentence.index = index
                    index += 1
    
            # apply cutoff
            sentences.sort(lambda x, y: 1 if x.rel_score < y.rel_score else -1)
            if options.cutoff > 0 and len(sentences) > options.cutoff:
                sentences = sentences[0:options.cutoff]
    
            # construct ILP
            program = ilp.IntegerLinearProgram(debug=0)
            objective = []
            length_constraint = []
            for sentence in sentences:
                objective.append("%+g s%d" % (sentence.rel_score, sentence.index))
                program.binary["s%d" % sentence.index] = sentence
                length_constraint.append("%+g s%d" % (sentence.length, sentence.index))
                for peer in sentences:
                    if sentence == peer: continue
                    score = sentence.sim_cosine(peer, word_idf)
                    if score > 0:
                        objective.append("%+g s%d_%d" % (-score, sentence.index, peer.index))
                        program.binary["s%d_%d" % (sentence.index, peer.index)] = [sentence, peer]
                        program.constraints["c1_%d_%d" % (sentence.index, peer.index)] = \
                            "s%d_%d - s%d <= 0" % (sentence.index, peer.index, sentence.index)
                        program.constraints["c2_%d_%d" % (sentence.index, peer.index)] = \
                            "s%d_%d - s%d <= 0" % (sentence.index, peer.index, peer.index)
                        program.constraints["c3_%d_%d" % (sentence.index, peer.index)] = \
                            "s%d + s%d - s%d_%d <= 1" % (sentence.index, peer.index, sentence.index, peer.index)
            program.objective["score"] = " ".join(objective)
            program.constraints["length"] = " ".join(length_constraint) + " <= %g" % task.length_limit

            run_times[problem.id] = time.time()    
            program.run()
            run_times[problem.id] = time.time() - run_times[problem.id]
            
            selection = []
            score = 0
            # get solution and check consistency
            for variable in program.binary:
                if variable in program.output and program.output[variable] == 1:
                    if type(program.binary[variable]) == type(sentences[0]):
                        selection.append(program.binary[variable])
                        score += program.binary[variable].rel_score
                        for peer in program.output:
                            if program.output[peer] == 0 or peer == variable or type(program.binary[peer]) != type(sentences[0]):
                                continue
                            if program.binary[variable].sim_cosine(program.binary[peer], word_idf) == 0:
                                continue
                            quadratic = "s%d_%d" % (program.binary[variable].index, program.binary[peer].index)
                            if quadratic not in program.output or program.output[quadratic] != 1:
                                print "WARNING: %s selected but %s not selected" % (variable, quadratic)
    
                    else:
                        score -= program.binary[variable][0].sim_cosine(program.binary[variable][1], word_idf)
                        if program.output["s%d" % program.binary[variable][0].index] != 1:
                            print "WARNING: %s selected while s%d not selected" % (variable, program.binary[variable][0].index)
                        if program.output["s%d" % program.binary[variable][1].index] != 1:
                            print "WARNING: %s selected while s%d not selected" % (variable, program.binary[variable][1].index)
            #if math.fabs(program.result["score"] - score) > .1:
            #    print "WARNING: difference between score = %g and expected = %g" % (program.result["score"], score)
            selection = ordering.by_date(selection)
            new_id = re.sub(r'.-(.)$', r'-\1', problem.id)
            output_file = open("%s/%s" % (options.output, new_id), "w")
            for sentence in selection:
                output_file.write(sentence.original + "\n")
            output_file.close()
        
    else:
        hist = prob_util.Counter()
        input_sents = []
        for problem in task.problems:
            num_problem_sentences = len(problem.get_new_sentences())
            #if num_problem_sentences < 300: continue
            if not '-A' in problem.id: continue

            if options.ir: 
                #docs = [doc for doc, val in problem.ir_docs]
                #for doc in docs: doc.get_sentences()
                num_overlap = len(set([d.id for d in problem.ir_docs]).intersection(set([d.id for d in problem.new_docs])))
                print '%s overlap: %d' %(problem.id, num_overlap)
                info_fh.write('%s overlap [%d]\n' %(problem.id, num_overlap))

            sys.stderr.write('problem [%s] input sentences [%d]' %(problem.id, num_problem_sentences))
            input_sents.append(num_problem_sentences)
    
            ## select a concept mapper
            map_times[problem.id] = time.time()
            if options.cheat:
                mapper = concept_mapper.CheatingMapper(problem, options.units)
            else:
                mapper = concept_mapper.HeuristicMapperExp(problem, options.units)
            
            ## timing test
            mapper.max_sents = max_sents
    
            ## map input concepts to weights
            success = mapper.map_concepts()
            if not success: sys.exit()
    
            ## choose a subset of the input sentences based on the mapping
            success = mapper.choose_sents()
            if not success: sys.exit()
            map_times[problem.id] = time.time() - map_times[problem.id]
            
            ## testing
            #fh = open('concept_matrix', 'w')
            for sent in mapper.relevant_sent_concepts:
                hist[len(sent)] += 1
                #fh.write(''.join(['%d, ' %concept for concept in sent[:-1]]))
                #fh.write('%d\n' %sent[-1])
            hist[0] += (num_problem_sentences-len(mapper.relevant_sent_concepts))
            #hist.displaySorted(N=100)
            #sys.exit()
            ## end testing

            ## setup and run the ILP
            run_times[problem.id] = time.time()
            selection = mapper.run(task.length_limit)
            selection = ordering.by_date(selection)
            run_times[problem.id] = time.time() - run_times[problem.id]

            ## TAC id convention is annoying
            output_id = problem.id
            if options.task in ['u09', 'u08']: output_id = problem.id[:5]+problem.id[6:]

            output_file = open('%s/%s' % (options.output, output_id), 'w')
            word_count = 0
            for sentence in selection:
                output_file.write(sentence.original + '\n')
                word_count += len(sentence.original.split())
            output_file.close()
            curr_time = map_times[problem.id] + run_times[problem.id]
            sys.stderr.write(' word count [%d] time [%1.2fs]\n' %(word_count, curr_time))

    ## timing information
    #avg_run_time = 1.0*sum(run_times.values())/len(run_times)
    #std_run_time = scipy.array(run_times.values()).std()
    #sys.stderr.write('\nTiming results\n')
    #sys.stderr.write('Mapper time:  total [%1.2fs]  min [%1.2fs]  max [%1.2fs]\n' %(sum(map_times.values()), min(map_times.values()), max(map_times.values())))
    #sys.stderr.write('Run time:     total [%1.2fs]  min [%1.2fs]  max [%1.2fs] avg [%1.4f] std [%1.4f]\n' %(sum(run_times.values()), min(run_times.values()), max(run_times.values()), avg_run_time, std_run_time))
    #sys.stderr.write('------\n')    

    #prob_util.normalize(hist).displaySorted(N=100)
    #print 1.0*sum(input_sents)/len(input_sents)

    #return avg_run_time, std_run_time

def test():
    import sentence_cleaner
    total, reg, agg = 0, 0, 0
    for problem in task.problems:
        for doc in problem.new_docs:
            for sent in doc.sentences:
                if sent.original[0].islower(): print '**', sent.original
                if sent.order == 0:
                    cleaned = sentence_cleaner.clean_aggressive(sent.original)
                    agg += len(cleaned.split())
                    reg += len(sentence_cleaner.clean(sent.original).split())
                else:
                    cleaned = sentence_cleaner.clean(sent.original)
                    agg += len(cleaned.split())
                    reg += len(cleaned.split())
                total += len(sent.original.split())    
                if sent.original == cleaned: continue
                print sent.original
                print cleaned
                print '----------'
                #if sent.order == 0: print sent
            print '+++'
    print 'total [%d] reg [%d] agg [%d]' %(total, reg, agg)
            
def dump_data(path):
    
    ## get an empty directory
    if os.path.isdir(path): os.system('rm -rf %s' %path)
    os.mkdir(path)
    
    import sentence_cleaner
    
    for problem in task.problems:
        sent_file = '%s/%s.sent' %(path, problem.id)
        doc_file = '%s/%s.doc' %(path, problem.id)
        par_file = '%s/%s.par' %(path, problem.id)
        sent_fh = open(sent_file, 'w')
        doc_fh = open(doc_file, 'w')
        par_fh = open(par_file, 'w')
        for doc in problem.new_docs:
            count = 0
            for sent in doc.sentences:
                
                ## cleaning
                if sent.original[0:2].islower(): 
                    print 'bad parse:', sent.original
                    continue
                if sent.order == 0: cleaned = sentence_cleaner.clean_aggressive(sent.original)
                else: cleaned = sentence_cleaner.clean(sent.original)
                
                sent_fh.write('%s\n' %cleaned)
                doc_fh.write('%s\n' %(doc.id))
                par_fh.write('%d\n' %int(sent.paragraph_starter))
        sent_fh.close()
        doc_fh.close()
        par_fh.close()
            
        query_file = '%s/%s.query' %(path, problem.id)
        query_fh = open(query_file, 'w')
        query_fh.write('%s\n' %problem.title)
        query_fh.write('%s\n' %problem.narr)
        query_fh.close()

        gold_file = '%s/%s.gold_sent' %(path, problem.id)
        gold_doc_file = '%s/%s.gold_doc' %(path, problem.id)
        gold_fh = open(gold_file, 'w')
        gold_doc_fh = open(gold_doc_file, 'w')
        for ann, sents in problem.training.items():
            for sent in sents:
                gold_fh.write('%s\n' %sent)
                gold_doc_fh.write('%s\n' %ann)
        gold_fh.close()
        gold_doc_fh.close()
        
if __name__ == '__main__':
    
    options, task = parse_options()

    ## create SummaryProblem instances
    setup_start_time = time.time()
    if options.task in ['u09', 'u08']: framework.setup_TAC08(task)
    else: framework.setup_DUC_basic(task, skip_updates=False)

    ## only run the parser if compression is required (this is not known by the pickle stuff)
    parser = None
    if options.compress:
        print 'compress'
        parser = berkeleyparser.CommandLineParser(BERKELEY_PARSER_CMD)
    framework.setup_DUC_sentences(task, parser, reload=options.reload)

    ## testing
    #test()
    #sys.exit()

    ## dump
    dump_data('../bourbon/tac08_v4')
    #dump_data('../bourbon/duc07_v4')
    #dump_data('../bourbon/duc07m_v4')
    #dump_data('../bourbon/duc06m_v4')
    #dump_data('../bourbon/tac09_v4')
    
    sys.exit()

    setup_time = time.time() - setup_start_time

    ## open set documents
    if options.ir > 0:
        task = ir.get_docs(task, options.ir, reload=True)

    ## go!
    options.mcd = False
    options.cutoff = 0
    run_standard(options)

    #info_fh = open('info.txt', 'w')
    #for max_sents in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]:
    #    avg_run_time, std_run_time = run_standard(options, max_sents)    
        #info_fh.write('%d %1.4f %1.4f\n' %(max_sents, avg_run_time, std_run_time))
        #util.flushFile(info_fh)
        
    sys.stderr.write('Setup time [%1.2fs]\n' %setup_time)
    

    ## evaluate
    if not options.manpath:
        sys.stderr.write('no manual path specified, skipping evaluation\n')
    else:
        import evaluate_duc
        sys.stderr.write('\nROUGE results\n')
        config_file = evaluate_duc.create_config(task.manual_path, options.output)
        evaluate_duc.run_rouge(ROUGE_SCORER, config_file, options.length, verbose=False)
        os.remove(config_file)

