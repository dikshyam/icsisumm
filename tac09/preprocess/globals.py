"""
global paths for shared use
change the ROOT to your installation directory
"""
import os, sys

#ROOT = os.path.realpath(os.path.dirname(sys.argv[0])) + '/../'
ROOT = '/u/dgillick/workspace/summ/'

DATA_ROOT = ROOT + 'data/'
TOOLS_ROOT = ROOT + 'tools/'
STATIC_DATA_ROOT = ROOT + 'static_data/'

STOPWORDS = STATIC_DATA_ROOT + 'stopwords/english'
ILP_SOLVER = TOOLS_ROOT + 'ilp/glpsol'
GENETIC_SUMMARIZER = TOOLS_ROOT + 'genetic/greedy_concept_summarizer'
BERKELEY_PARSER_CMD = '%s/parser_bin/distribute.sh %s/parser_bin/berkeleyParser+Postagger.sh' %(TOOLS_ROOT, TOOLS_ROOT)
BOOSTING_LEARNER = '%s/boost/icsiboost' %TOOLS_ROOT
ROUGE_SCORER = '/u/favre/work/summarization/tools/ROUGE-1.5.5/ROUGE-1.5.5_faster.pl'

def unit_test():

    python_test = True
    try: x = set()
    except: python_test = False

    nltk_test = True
    try:
        import nltk
        import nltk.stem.porter
        import nltk.tokenize.punkt
    except: nltk_test = False

    print '--- Testing for required components ---'
    print 'ROOT              [%s]' %ROOT
    print 'STATIC_DATA_ROOT  [%s] exists? [%s]' %(STATIC_DATA_ROOT, os.path.exists(STATIC_DATA_ROOT))
    print 'ILP_SOLVER        [%s] exists? [%s]' %(ILP_SOLVER, os.path.exists(ILP_SOLVER))
    print 'ROUGE_SCORER      [%s] exists? [%s]' %(ROUGE_SCORER, os.path.exists(ROUGE_SCORER))
    print 'Python version 2.5? [%s]' %python_test
    print 'NLTK exists? [%s]' %nltk_test
    print '-------------------------------'


if __name__ == '__main__':
    """
    make sure all paths exist
    """
    unit_test()
    
