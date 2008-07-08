import os, sys, re
import util, sentence_compression, text
from globals import *    
import nltk

class SummaryProblem:
    """
    A class for representing elements of a summary problem
    self.id           'D0701'
    self.title        'Southern Poverty Law Center'
    self.narr         'Describe the activities of Morris Dees...'
    """

    def __init__(self, id, title, narr, new_docs, old_docs):
        self.id = id
        self.title = title
        self.narr = narr
        self.query = text.Sentence(title)#+": "+ narr)
        self.new_docs_paths = new_docs[:]
        self.old_docs_paths = old_docs[:]

        ## variables that might get set later
        self.new_docs = None
        self.old_docs = None
        self.training = {}
        self.annotators = set()
        
    def load_documents(self):
        """
        """
        self.new_docs = []
        for path in self.new_docs_paths:
            doc = text.Document(path)
            doc.get_sentences()
            self.new_docs.append(doc)
            
        self.old_docs = []
        for path in self.old_docs_paths:
            doc = text.Document(path)
            self.old_docs.append(doc)

    def _load_training(self, path, source='DUC'):
        """
        load [human] summaries, setting these member variables:
        self.training_sent_sets = [[Sentence1, Sentence2, ... ], [ ... ], ... ]
        self.annotators = set(['A1', 'A2', ... ]

        DUC update format    D0703-A.M.100.A.A
        DUC main format      D0701.M.250.A.A
        """
        self.training = {}
        self.annotators = set()
        if source == 'DUC':
            for file in os.listdir(path):
                items = file.upper().split('.')
                id = items[0]
                
                ## skip ids not relevant to this problem
                if id != self.id: continue

                annotator = items[-1]
                self.annotators.add(annotator)
                rawsents = open(path + file).read().splitlines()
                self.training[annotator] = rawsents

    def get_new_sentences(self):
        #return [sent for sent in doc.sentences for doc in self.new_docs]
        sents = []
        for doc in self.new_docs:
            for sent in doc.sentences:
                sents.append(sent)
        return sents
    
    def __str__(self):
        s = []
        s.append('%s SUMMARYPROBLEM' %FORMAT_START)
        s.append('ID %s' %self.id)
        s.append('TITLE %s' %self.title)
        s.append('NARR %s' %self.narr)
        s.append('NEW_DOCS %d\n%s' %(len(self.new_docs), '\n'.join(['%s' %n for n in self.new_docs])))
        s.append('OLD_DOCS %d\n%s' %(len(self.old_docs), '\n'.join(['%s' %n for n in self.old_docs])))
        for annotator in self.annotators:
            s.append('TRAIN %s\n%s' %(annotator, '\n'.join(['%s' %n for n in self.training[annotator]])))
        return '\n'.join(s)

### SETUP FUNCTIONS ###

def setup_simple(data_path, id='simple', title='', narr=''):
    """
    create a summary problem from a single clean (text only) input file
    """
    doc = text.Document(data_path, is_clean=True)
    problem = SummaryProblem(id, title, narr, [doc], [])
    return problem    

def setup_TAC08(task):
    """
    task.topic_file: xml file for TAC
    task.doc_path: path containing source documents
    task.manual_path: path for manual (human) summaries
    """

    ## get all document data
    all_docs = {}
    files = util.get_files(task.doc_path, r'[^_]+_[^_]+_\d+[\.\-]\d+')
    sys.stderr.write('Loading [%d] files\n' %len(files))
    for file in files:
        id = os.path.basename(file)
        all_docs[id] = file
    
    ## initialize problems
    problems = []
    # load XML task definition
    from xml.etree import ElementTree
    root = ElementTree.parse(task.topic_file).getroot()
    for topic in root:
        if topic.tag != "topic": continue
        id = topic.attrib["id"]
        title = None
        narr = None
        docsets = []
        docset_ids = []
        for node in topic:
            if node.tag == "title":
                title = node.text.strip()
            elif node.tag == "narrative":
                narr = node.text.strip()
            elif node.tag == "docsetA":
                documents = node.findall("doc")
                docsets.append([doc.attrib["id"] for doc in documents])
                docset_ids.append(node.attrib["id"])
            elif node.tag == "docsetB":
                documents = node.findall("doc")
                docsets.append([doc.attrib["id"] for doc in documents])
                docset_ids.append(node.attrib["id"])

        old_docs = []
        for docset_index in range(len(docsets)):
            
            ## map docids to documents
            new_docs = [all_docs[doc] for doc in docsets[docset_index]]

            ## create a SummaryProblem
            problem = SummaryProblem(docset_ids[docset_index], title, narr, new_docs, old_docs)
            old_docs += new_docs

            ## include training data in problem
            if task.manual_path: problem._load_training(task.manual_path)

            problems.append(problem)

    sys.stderr.write('Setting up [%d] problems\n' %len(problems))
    task.problems = problems

def setup_DUC_basic(task):
    """
    task.topic_file: sgml file for DUC
    task.doc_path: path containing source documents
    task.manual_path: path for manual (human) summaries
    """

    ## get all document data
    all_docs = {}
    files = util.get_files(task.doc_path, NEWSWIRE_PATTERN)
    sys.stderr.write('Loading [%d] files\n' %len(files))
    for file in files:
        id = os.path.basename(file)
        all_docs[id] = file
    
    ## initialize problems
    problems = []
    data = open(task.topic_file).read().replace('\n', ' ')
    topics = re.findall('<topic>.+?</topic>', data)
    sys.stderr.write('Setting up [%d] problems\n' %len(topics))
    for topic in topics:
        id = util.remove_tags(re.findall('<num>.+?</num>', topic)[0])[:-1]
        title = util.remove_tags(re.findall('<title>.+?</title>', topic)[0])
        narr = util.remove_tags(re.findall('<narr>.+?</narr>', topic)[0])
        docsets = re.findall('<docs.*?>.+?</docs.*?>', topic)
        docsets = map(util.remove_tags, docsets)
        docsets = [d.split() for d in docsets]

        old_docs = []
        for docset_index in range(len(docsets)):
            
            ## update naming convention different from main
            if len(docsets) > 1: id_ext = '-' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[docset_index]
            else: id_ext = ''
            
            new_docs = [all_docs[doc] for doc in docsets[docset_index]]

            ## create a SummaryProblem
            problem = SummaryProblem(id+id_ext, title, narr, new_docs, old_docs)
            old_docs += new_docs

            ## include training data in problem
            if task.manual_path: problem._load_training(task.manual_path)

            problems.append(problem)

    task.problems = problems

def setup_DUC_sentences(task, parser=None, reload=False):

    ## load problems quickly from pickle file
    if (not reload) and os.path.isfile(task.data_pickle):
        sys.stderr.write('Loading [%s] problem data from [%s]\n' %(task.name, task.data_pickle))
        task.problems = util.load_pickle(task.data_pickle)
        return

    ## only parse sentences if needed
    for problem in task.problems:
        print problem.id
        problem.load_documents()
        if parser:
            for doc in problem.new_docs:
                doc.parse_sentences(parser)
                
    if parser:
        parser.run()
        for sentence, parsetree in parser.parsed.items():
            sentence.parsed = parsetree
        
    ## save pickled version for faster loading later
    sys.stderr.write('Saving [%s] problem data in [%s]\n' %(task.name, task.data_pickle))
    util.save_pickle(task.problems, task.data_pickle)

#def concept_mapper(problem):
#    concept_weight = {}
#
#    for sentence in problem.get_new_sentences():
#        sentence.compression_node = sentence_compression.SentenceCompressionNode(sentence.parsed)
#        for concept in sentence_compression.get_bigrams_from_node(sentence.compression_node, use_leaves = True, return_length = False):
#            if concept not in concept_weight: concept_weight[concept] = 0
#            concept_weight[concept] += 1
#    for concept in concept_weight.keys():
#        if concept_weight[concept] < 3:
#            del concept_weight[concept]
#
#    return concept_weight

def build_program(problem, concept_weight, length=100, sentences = None):

    # the ILP keeps tracks of the constraints
    # s<num> variables handle sentences, subsentences and removable subtrees
    # c<num> variables represent concepts in those selected pseudo-sentences
    program = sentence_compression.SentenceSelectionILP(concept_weight, length, use_subsentences=True, use_removables=True, 
                                                        use_min_length=True, use_min_length_ratio=False)
    if not sentences:
        sentences = problem.get_new_sentences()
    for sentence in sentences:
        if not hasattr(sentence, "compression_node"):
            sentence.compression_node = sentence_compression.SentenceCompressionNode(sentence.parsed)

    mapper = sentence_compression.EquivalentNounPhraseMapper()
    nounPhraseMapping = mapper.getMappings([s.compression_node for s in sentences])
    
    for sentence in sentences:
        ## generate a compression candidate tree
        candidates = sentence.compression_node.getCandidateTree(nounPhraseMapping)
        candidate_root = sentence_compression.SentenceCompressionNode(candidates)
        
        ## (or a non compressed tree)
        #candidate_root = treenode.TreeNode(sentence.compression_node.getNonCompressedCandidate())
        
        if candidate_root.isLeaf(): continue
        
        ## debugging
        #candidate_root.original = root
        #candidate_root.original_text = candidates

        # update ILP with the new sentence
        program.addSentence(candidate_root, lambda x: sentence_compression.get_bigrams_from_node(x, 
            node_skip=lambda y: False, node_transform=lambda y: text.text_processor.porter_stem(y.text)))

    return program

def get_program_result(program, path):
    # get the selected sentences
    text = []
    for id in program.output:
        if id.startswith("s") and program.output[id] == 1:
            node = program.binary[id] # gives you back the actual node (which can be a subsentence, or a chunk not removed)
            if not program.nodeHasSelectedParent(node): # only start printing at the topmost nodes
                text.append(sentence_compression.postProcess(program.getSelectedText(node)))
                #print node.root.getPrettyCandidates()
                
    fh = open(path, 'w')
    fh.write('\n'.join(text) + '\n')
    fh.close()


