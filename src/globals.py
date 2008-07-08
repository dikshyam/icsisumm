"""
global paths for shared use
change the ROOT to your installation directory
"""

#############################################
ROOT = '/u/dgillick/workspace/summ/'
ROOT = '/u/favre/work/summarization/systems/icsi_tac08/summ_2008-06-24/'
#############################################

#############################################
STATIC_DATA_ROOT = ROOT + 'static_data/'
STOPWORDS = STATIC_DATA_ROOT + 'stopwords/english'

DATA_ROOT = ROOT + 'data/'
TOOLS_ROOT = ROOT + 'tools/'

ILP_SUMMARIZER = TOOLS_ROOT + 'ilp/glpsol'
GENETIC_SUMMARIZER = TOOLS_ROOT + 'genetic/greedy_concept_summarizer'
BERKELEY_PARSER_CMD = '%s/parser_bin/distribute.sh %s/parser_bin/berkeleyParser+Postagger.sh' %(TOOLS_ROOT, TOOLS_ROOT)
#############################################

#############################################
FORMAT_START = '#START'
NEWSWIRE_PATTERN = '\w{2,3}\d+[\.\-]\d+'
#############################################

#############################################
class Task:
    """
    Class for holding paths to the important Task elements
    self.topic_file     sgml file specifying problems (DUC)
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
        self.punkt_pickle = '%s/%s_punkt.pickle' %(DATA_ROOT, self.name)
        self.problems = None

_update_docs_2008 = '/u/favre/work/summarization/tac08_data/UpdateSumm08_test_docs_files/'
_update_docs_2007 = '/u/drspeech/data/DUC/07/duc07.results.data/testdata/duc2007_testdocs/update/'
_main_docs_2007 = '/u/drspeech/data/DUC/07/duc07.results.data/testdata/duc2007_testdocs/main/'
_main_docs_2006 = '/u/drspeech/data/DUC/06/testdata/duc2006_docs/'
_main_docs_2005 = '/u/drspeech/data/DUC/05/testdata/duc2005_docs/'

_update_topics_2008 = '/u/favre/work/summarization/tac08_data/UpdateSumm08_test_topics.xml' 
_update_topics_2007 = '%s/duc2007_update_topics.sgml' %STATIC_DATA_ROOT
_main_topics_2007 = '%s/duc2007_topics.sgml' %STATIC_DATA_ROOT
_main_topics_2006 = '%s/duc2006_topics.sgml' %STATIC_DATA_ROOT
_main_topics_2005 = '%s/duc2005_topics.sgml' %STATIC_DATA_ROOT

_update_manual_2008 = None
_update_manual_2007 = '/u/drspeech/data/DUC/07/duc07.results.data/results/updateEval/ROUGE/models/'
_main_manual_2007 = '/u/drspeech/data/DUC/07/duc07.results.data/results/mainEval/ROUGE/models/'
_main_manual_2006 = '/u/drspeech/data/DUC/06/results/NIST/NISTeval/ROUGE/models/'
_main_manual_2005 = '/u/drspeech/data/DUC/05/results/NIST/results/ROUGE/models/'

TAC_2008_UPDATE_TASK = Task('u08', _update_topics_2008, _update_docs_2008, _update_manual_2008, 100)
DUC_2007_UPDATE_TASK = Task('u07', _update_topics_2007, _update_docs_2007, _update_manual_2007, 100)
DUC_2007_MAIN_TASK = Task('m07', _main_topics_2007, _main_docs_2007, _main_manual_2007, 250)
DUC_2006_MAIN_TASK = Task('m06', _main_topics_2006, _main_docs_2006, _main_manual_2006, 250)
DUC_2005_MAIN_TASK = Task('m05', _main_topics_2005, _main_docs_2005, _main_manual_2005, 250)
#############################################

def unit_test():
    import os
    print '--- Testing for valid paths ---'
    print 'your current dir        [%s]' %os.path.abspath(os.curdir)
    print
    print 'ROOT                    [%s] exists? [%s]' %(ROOT, os.path.exists(ROOT))
    print 'DATA_ROOT               [%s] exists? [%s]' %(DATA_ROOT, os.path.exists(DATA_ROOT))
    print 'STATIC_DATA_ROOT        [%s] exists? [%s]' %(STATIC_DATA_ROOT, os.path.exists(STATIC_DATA_ROOT))
    print 'ILP_SUMMARIZER          [%s] exists? [%s]' %(ILP_SUMMARIZER, os.path.exists(ILP_SUMMARIZER))
    print 'GENETIC_SUMMARIZER      [%s] exists? [%s]' %(GENETIC_SUMMARIZER, os.path.exists(GENETIC_SUMMARIZER))
    print '-------------------------------'


if __name__ == '__main__':
    """
    make sure all paths exist
    """
    unit_test()
    
