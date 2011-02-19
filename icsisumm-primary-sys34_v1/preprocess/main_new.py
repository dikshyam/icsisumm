import sys, os, re, time
import framework, concept_mapper, ordering, berkeleyparser, compression, util, prob_util, ir
import mapping
from globals import *
import scipy, ilp, text

## use these to specify source document paths
doc_source = {}
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
                      help='tasks: u08, u07, m07, m06, m05')
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
    if not options.task in ['u08', 'u07', 'm07', 'm06', 'm05']:
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

def run_standard(options):

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
    input_sents = []
    for problem in task.problems:
        if not 'A' in problem.id: continue
        sys.stderr.write('problem [%s] input sentences [%d]' %(problem.id, len(problem.get_new_sentences())))
        
        ## select a concept mapper
        map_times[problem.id] = time.time()
        if options.cheat:
            mapper = concept_mapper.CheatingMapper(problem, options.units)
        else:
            mapper = concept_mapper.HeuristicMapper(problem, options.units)
            
        ## map input concepts to weights
        success = mapper.map_concepts()
        if not success: sys.exit()
    
        ## choose a subset of the input sentences based on the mapping
        success = mapper.choose_sents()
        if not success: sys.exit()
        map_times[problem.id] = time.time() - map_times[problem.id]
            
        ## setup and run the ILP
        run_times[problem.id] = time.time()
        selection = mapper.run(task.length_limit)

        ## new ilp
        #mapper = mapping.LocationMapper(problem)
        #mapper.setup()
        
        selection = ordering.by_date(selection)
        run_times[problem.id] = time.time() - run_times[problem.id]

        ## TAC id convention is annoying
        output_id = problem.id
        if options.task == 'u08': output_id = problem.id[:5]+problem.id[6:]

        output_file = open('%s/%s' % (options.output, output_id), 'w')
        word_count = 0
        for sentence in selection:
            output_file.write(sentence.original + '\n')
            word_count += len(sentence.original.split())
        output_file.close()
        curr_time = map_times[problem.id] + run_times[problem.id]
        sys.stderr.write(' word count [%d] time [%1.2fs]\n' %(word_count, curr_time))

    ## timing information
    avg_run_time = 1.0*sum(run_times.values())/len(run_times)
    std_run_time = scipy.array(run_times.values()).std()
    sys.stderr.write('\nTiming results\n')
    sys.stderr.write('Mapper time:  total [%2.2fs]  min [%1.2fs]  max [%1.2fs]\n' %(sum(map_times.values()), min(map_times.values()), max(map_times.values())))
    sys.stderr.write('Run time:     total [%2.2fs]  min [%1.2fs]  max [%1.2fs] avg [%1.4f] std [%1.4f]\n' %(sum(run_times.values()), min(run_times.values()), max(run_times.values()), avg_run_time, std_run_time))
    sys.stderr.write('------\n')    


if __name__ == '__main__':
    
    options, task = parse_options()

    ## create SummaryProblem instances
    setup_start_time = time.time()
    if options.task == 'u08': framework.setup_TAC08(task)
    else: framework.setup_DUC_basic(task, skip_updates=False)

    ## only run the parser if compression is required (this is not known by the pickle stuff)
    parser = None
    if options.compress:
        parser = berkeleyparser.CommandLineParser(BERKELEY_PARSER_CMD)
    framework.setup_DUC_sentences(task, parser, reload=options.reload)

    setup_time = time.time() - setup_start_time

    ## go!
    run_standard(options)
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

