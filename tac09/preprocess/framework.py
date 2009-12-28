import os, sys, re
import util, compression, text, ilp
from globals import *    
import nltk

class SummaryProblem:
    """
    A class for representing elements of a summary problem
    self.id               'D0701'
    self.title            'Southern Poverty Law Center'
    self.narr             'Describe the activities of Morris Dees...'
    self.query            <title>: <narr>
    self.new_docs_paths    a list of paths to the input documents
    self.old_docs_paths    a list of paths to 'old' input docs (update task only)
    self.new_docs         [Document1, ... ]
    self.old_docs         [Document1, ... ]
    self.annotators       set(['A', 'B', 'C', 'D'])
    self.training         {'A': <summary A>, ... }
    """

    def __init__(self, id, title, narr, new_docs, old_docs):
        self.id = id
        self.title = title
        self.narr = narr
        self.query = text.Sentence(title+": "+ narr)
        self.new_docs_paths = new_docs[:]
        self.old_docs_paths = old_docs[:]
        
        ## for checking state
        self.loaded_docs = False
        self.parsed = False
        self.loaded_ir_docs = False

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

        self.loaded_docs = True
        
    def _load_training(self, path, source='DUC'):
        """
        load [human] summaries, setting these member variables:
        self.training_sent_sets = [[Sentence1, Sentence2, ... ], [ ... ], ... ]
        self.annotators = set(['A1', 'A2', ... ]
        """
        self.training = {}
        self.annotators = set()
        if source.startswith('DUC') or source.startswith('TAC'):
            for file in os.listdir(path):
                items = file.split('.')
                id = items[0]

                ## skip ids not relevant to this problem
                compare_id = self.id.upper()
                if source == 'TAC08':
                    compare_id = self.id.upper()[:5] + self.id.upper()[6:]

                if id.upper() != compare_id: continue

                annotator = items[-1]
                self.annotators.add(annotator)
                rawsents = open(path + file).read().splitlines()
                self.training[annotator] = rawsents

    def get_new_sentences(self):
        sents = []
        for doc in self.new_docs:
            for sent in doc.sentences:
                sents.append(sent)
        return sents
    
    def __str__(self):
        s = []
        s.append('%s SUMMARYPROBLEM' %'#START')
        s.append('ID %s' %self.id)
        s.append('TITLE %s' %self.title)
        s.append('NARR %s' %self.narr)
        s.append('NEW_DOCS %d\n%s' %(len(self.new_docs), '\n'.join(['%s' %n for n in self.new_docs])))
        s.append('OLD_DOCS %d\n%s' %(len(self.old_docs), '\n'.join(['%s' %n for n in self.old_docs])))
        for annotator in self.annotators:
            s.append('TRAIN %s\n%s' %(annotator, '\n'.join(['%s' %n for n in self.training[annotator]])))
        return '\n'.join(s)


def check_state(problems):
    checks = ['sentences', 'parsed', 'ir']
    results = dict.fromkeys(checks, True)
    for problem in problems:
        if not problem.loaded_docs: results['sentences'] = False
        if not problem.parsed: results['parsed'] = False
        if not problem.loaded_ir_docs: results['ir'] = False
    return results

### SETUP FUNCTIONS ###

def setup_simple(data_path, id='simple', title='', narr=''):
    """
    create a summary problem from a single clean (text only) input file
    """
    doc = text.Document(data_path, is_clean=True)
    problem = SummaryProblem(id, title, narr, [doc], [])
    return problem    

def setup_TAC08(task, skip_updates=False):
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
                if skip_updates: continue
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
            if task.manual_path: problem._load_training(task.manual_path, source='TAC08')

            problems.append(problem)

    sys.stderr.write('Setting up [%d] problems\n' %len(problems))
    task.problems = problems

def setup_DUC_basic(task, skip_updates=False):
    """
    task.topic_file: sgml file for DUC
    task.doc_path: path containing source documents
    task.manual_path: path for manual (human) summaries
    """

    ## get all document data
    all_docs = {}
    files = util.get_files(task.doc_path, '\w{2,3}\d+[\.\-]\d+')
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

            ## skip updates?
            if skip_updates: break

    task.problems = problems

def setup_DUC_sentences(task, parser=None, reload=False):

    ## load problems quickly from pickle file
    if (not reload) and os.path.isfile(task.data_pickle):
        sys.stderr.write('Loading [%s] problem data from [%s]\n' %(task.name, task.data_pickle))
        task.problems = util.load_pickle(task.data_pickle)
        return

    ## parse sentences
    text.text_processor.load_splitta_model('/u/dgillick/sbd/splitta/model_nb/')
    for problem in task.problems:
        sys.stderr.write('%s\n' %problem.id)
        problem.load_documents()
        if parser:
            for doc in problem.new_docs:
                doc.parse_sentences(parser)
                problem.parsed = True
                
    if parser:
        parser.run()
        for sentence, parsetree in parser.parsed.items():
            sentence.parsed = parsetree
        
    ## save pickled version for faster loading later
    sys.stderr.write('Saving [%s] problem data in [%s]\n' %(task.name, task.data_pickle))
    util.save_pickle(task.problems, task.data_pickle)


def build_program(problem, concept_weight, length=100, sentences = None):
    """
    the ILP keeps tracks of the constraints
    s<num> variables handle sentences, subsentences and removable subtrees
    c<num> variables represent concepts in those selected pseudo-sentences
    """
    program = compression.SentenceSelectionILP(concept_weight, length, use_subsentences=True, use_removables=True, 
                                                        use_min_length=True, use_min_length_ratio=False)
    if not sentences:
        sentences = problem.get_new_sentences()
    for sentence in sentences:
        if not hasattr(sentence, "compression_node"):
            sentence.compression_node = compression.TreebankNode(sentence.parsed)

    nounPhraseMapping = compression.generateNounPhraseMapping([s.compression_node for s in sentences])
    
    for sentence in sentences:
        ## generate a compression candidate tree
        candidates = sentence.compression_node.getCandidateTree(nounPhraseMapping)
        candidate_root = compression.TreebankNode(candidates)
        candidate_root.sentence = sentence
        
        ## (or a non compressed tree)
        #candidate_root = treenode.TreeNode(sentence.compression_node.getNonCompressedCandidate())
        
        if candidate_root.isLeaf(): continue
        
        ## debugging
        #candidate_root.original = root
        #candidate_root.original_text = candidates

        # update ILP with the new sentence
        program.addSentence(candidate_root, lambda x: compression.get_bigrams_from_node(x, 
            node_skip=lambda y: not re.match(r'[A-Za-z0-9]', y.label), node_transform=lambda y: text.text_processor.porter_stem(y.text.lower())))

        # skip debugging part
        continue
        sentence_concepts = program.getConcepts(candidate_root, lambda x: compression.get_bigrams_from_node(x,
                    node_skip=lambda y: not re.match(r'[A-Za-z0-9]', y.label), node_transform=lambda y: text.text_processor.porter_stem(y.text.lower())))
        print sentence.original
        print candidate_root.getPrettyCandidates()
        for concept in sentence_concepts.keys():
            if concept not in concept_weight:
                del sentence_concepts[concept]
        print sorted(sentence_concepts.keys())
        units = dict([(x, 1) for x in util.get_ngrams(sentence.stemmed, n=2, bounds=False)])
        for concept in units.keys():
            if concept not in concept_weight:
                del units[concept]
        print sorted(units.keys())

    return program

def get_program_result(program):
    # get the selected sentences
    selection = []
    for id in program.output:
        if id.startswith("s") and program.output[id] == 1:
            node = program.binary[id] # gives you back the actual node (which can be a subsentence, or a chunk not removed)
            if not program.nodeHasSelectedParent(node): # only start printing at the topmost nodes
                # create a fake sentence to hold the compressed content
                sentence = text.Sentence(compression.postProcess(program.getSelectedText(node)), \
                        node.root.sentence.order, node.root.sentence.source, node.root.sentence.date)
                sentence.parsed = str(node)
                sentence.original_node = node
                selection.append(sentence)
                #print node.root.getPrettyCandidates()
    return selection           

def build_alternative_program(problem, concept_weight, length=100, sentences = None, longuest_candidate_only=False):
    if not sentences:
        sentences = problem.get_new_sentences()

    for sentence in sentences:
        if not hasattr(sentence, "compression_node"):
            sentence.compression_node = compression.TreebankNode(sentence.parsed)

    nounPhraseMapping = compression.generateNounPhraseMapping([s.compression_node for s in sentences])
    #print "generating acronyms"
    acronymMapping = compression.generateAcronymMapping(problem.get_new_sentences())
    print problem.id, acronymMapping
    
    compressed_sentences = []
    seen_sentences = {}
    group_id = 0
    for sentence in sentences:
        subsentences = sentence.compression_node.getNodesByFilter(compression.TreebankNode.isSubsentence)
        candidates = {}
        for node in subsentences:
            candidates.update(node.getCandidates(mapping=nounPhraseMapping))
        if longuest_candidate_only:
            max_length = 0
            argmax = None
            for candidate in candidates:
                if len(candidate) > max_length:
                    max_length = len(candidate)
                    argmax = candidate
            if argmax != None:
                candidates = [argmax]
        for candidate in candidates:
            new_sentence = text.Sentence(compression.postProcess(candidate), sentence.order, sentence.source, sentence.date)
            if new_sentence.length <= 5: continue # skip short guys
            new_sentence.group_id = group_id
            compressed_sentences.append(new_sentence)
            seen_sentences[new_sentence.original] = 1
        group_id += 1

    compression.replaceAcronyms(compressed_sentences, acronymMapping)
    log_file = open("%s.log" % problem.id, "w")
    for sentence in compressed_sentences:
        log_file.write("%d %s\n" %( group_id, str(sentence)))
    log_file.close()

    # generate ids for acronyms
    acronym_id = {}
    acronym_length = {}
    for definition, acronym in acronymMapping.items():
        if acronym not in acronym_id:
            acronym_id[acronym] = len(acronym_id)
            acronym_length[acronym] = len(definition.strip().split())
    
    # get concepts
    relevant_sentences = []
    sentence_concepts = []
    groups = {}
    used_concepts = set()
    acronym_index = {}
    sent_index = 0
    for sentence in compressed_sentences:
        units = util.get_ngrams(sentence.stemmed, n=2, bounds=False)
        overlapping = set([u for u in units if u in concept_weight])
        if len(overlapping) == 0: continue
        relevant_sentences.append(sentence)
        sentence_concepts.append(overlapping)
        used_concepts.update(overlapping)
        if sentence.group_id not in groups: groups[sentence.group_id] = []
        groups[sentence.group_id].append(sent_index)
        # generate an acronym index
        for acronym in acronym_id:
            if re.search(r'\b' + acronym + r'\b', sentence.original):
                if acronym not in acronym_index: acronym_index[acronym] = []
                acronym_index[acronym].append(sent_index)
        sent_index += 1

    # build inverted index
    filtered_concepts = {}
    concept_index = {}
    index = 0
    for concept in used_concepts:
        concept_index[concept] = index
        filtered_concepts[concept] = concept_weight[concept]
        index += 1
    relevant_sent_concepts = [[concept_index[c] for c in cs] for cs in sentence_concepts]
    concept_weights = filtered_concepts
    curr_concept_sents = {}
    for sent_index in range(len(relevant_sentences)):
        concepts = relevant_sent_concepts[sent_index]
        for concept in concepts:
            if not concept in curr_concept_sents: curr_concept_sents[concept] = []
            curr_concept_sents[concept].append(sent_index)

    # generate the actual ILP
    program = ilp.IntegerLinearProgram()

    program.objective["score"] = ' + '.join(['%f c%d' %(concept_weight[concept], concept_index[concept]) for concept in concept_index])
    
    s1 = ' + '.join(['%d s%d' %(relevant_sentences[sent_index].length, sent_index) for sent_index in range(len(relevant_sentences))])
    # add enough space to fit the definition of each acronym employed in the summary
    s_acronyms = ' + '.join(['%d a%d' %(acronym_length[acronym], acronym_id[acronym]) for acronym in acronym_id])
    if s_acronyms != "":
        s_acronyms = " + " + s_acronyms
    s2 = ' <= %s\n' %length
    program.constraints["length"] = s1 + s_acronyms + s2
    
    for concept, index in concept_index.items():
        ## at least one sentence containing a selected bigram must be selected
        s1 = ' + '.join([ 's%d' %sent_index for sent_index in curr_concept_sents[index]])
        s2 = ' - c%d >= 0' %index                    
        program.constraints["presence_%d" % index] = s1 + s2
        ## if a bigram is not selected then all sentences containing it are deselected
        s1 = ' + '.join([ 's%d' %sent_index for sent_index in curr_concept_sents[index]])
        s2 = '- %d c%d <= 0' %(len(curr_concept_sents[index]), index)
        program.constraints["absence_%d" % index] = s1 + s2

    # constraints so that acronyms get selected along with sentences they belong to
    for acronym, index in acronym_index.items():
        s1 = ' + '.join([ 's%d' %sent_index for sent_index in index])
        s2 = ' - a%d >= 0' %acronym_id[acronym]                    
        program.constraints["acronym_presence_%d" % acronym_id[acronym]] = s1 + s2
        s1 = ' + '.join([ 's%d' %sent_index for sent_index in index])
        s2 = '- %d a%d <= 0' %(len(index), acronym_id[acronym])
        program.constraints["acronym_absence_%d" % acronym_id[acronym]] = s1 + s2

    # add sentence compression groups
    for group in groups:
        program.constraints["group_%d" % group] = " + ".join(["s%d" % sent_index for sent_index in groups[group]]) + " <= 1"

    for sent_index in range(len(relevant_sentences)):
        program.binary["s%d" % sent_index] = relevant_sentences[sent_index]
    for concept, concept_index in concept_index.items():
        program.binary["c%d" % concept_index] = 1
    for acronym, id in acronym_id.items():
        program.binary["a%d" % id] = 1

    sys.stderr.write("compression candidates: %d, original: %d\n" % (len(relevant_sentences), len(sentences)))
    program.acronyms = acronymMapping
    return program
