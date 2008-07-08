import os, sys, re, math, prob_util, util, ilp, text
from globals import *

class Mapper:
    """
    self.problem             a SummaryProblem instance
    self.unit_selector       retrieve sub-sentence units (eg. ngrams)
        n1: word unigrams
        n2: word bigrams
        default: word bigrams
    """
    
    def __init__(self, summary_problem, units='n2', df=None):
        
        self.unit_name = units
        self.problem = summary_problem
        self.df = df

        use_bounds = False
        if   units == 'n1': self.unit_selector = lambda x: util.get_ngrams(x, n=1, bounds=use_bounds)
        elif units == 'n2': self.unit_selector = lambda x: util.get_ngrams(x, n=2, bounds=use_bounds)
        elif units == 'n3': self.unit_selector = lambda x: util.get_ngrams(x, n=3, bounds=use_bounds)
        elif units == 'n12': self.unit_selector = lambda x: util.get_ngrams(x, n=1) + util.get_ngrams(x, n=2)
        elif units == 'n23': self.unit_selector = lambda x: util.get_ngrams(x, n=2) + util.get_ngrams(x, n=3)
        elif units == 's2' : self.unit_selector = lambda x: get_skip_bigrams(x, k=4) + util.get_ngrams(x, n=1)
        else: units = util.get_ngrams  # default options

        ## variables to set later
        self.concept_sets = None
        self.concept_weight_sets = None
        self.concept_index_sets = None
        self.relevant_sent_sets = None
        self.relevant_sent_concepts = None

        ## defaults
        self.min_sent_length = 5
        
    def map_concepts(self):
        """
        Step 1: map concepts to weights
        assign self_concept_sets
        """
        abstract()

    def choose_sents(self):
        """
        Step 2: choose a subset of the problem sentences based on concepts, etc.
        """
        abstract()

    def format_output(self, style=None, max_length = 100):
        """
        Step 3: create formatted output
        """
        ## make sure step 2 has been completed
        if not self.relevant_sent_sets:
            sys.stderr.write('Error: need to run choose_sents first\n')
            return None

        outputs = {}
        sentences = {}
        self.concept_sents_sets = []  ## new member variable (clean this up!)

        for update_index in range(len(self.concept_sets)):
            output = []
            id = self.problem.id

            ## deal with update id convention
            if len(self.concept_sets) > 1:
                id += '-' + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')[update_index]

            id += '.%s.%d.%s.%d' %('M', max_length, self.problem.id, 1)

            curr_sents = self.relevant_sent_sets[update_index]                # list of sentences
            curr_sent_concepts = self.relevant_sent_concepts[update_index]    # dict of concepts in each sentence {0: [1, 4, ... ], 1: ... }
            curr_concept_weights = self.concept_weight_sets[update_index]     # dict of weight for each concept {'(he, said)': 3.4, ... }
            curr_concept_index = self.concept_index_sets[update_index]        # dict of index for each concept  {'(he, said)': 100, ... }
            curr_concept_sents = {}                                           # dict of sentences for each concept
            for sent_index in range(len(curr_sents)):
                concepts = curr_sent_concepts[sent_index]
                for concept in concepts:
                    if not concept in curr_concept_sents: curr_concept_sents[concept] = []
                    curr_concept_sents[concept].append(sent_index)
            self.concept_sents_sets.append(curr_concept_sents)
                    
            ## custom format
            if style != 'ilp':
                output.append('%s NUM_SENTENCES %d' %(id, len(curr_sents)))
                output.append('%s NUM_CONCEPTS %d' %(id, len(curr_concept_index)))
                output.append('%s TEXT TOPIC %s %s' %(id, self.problem.title, self.problem.narr))
    
                ## sentence info
                for sent_index in range(len(curr_sents)):
                    output.append('%s LENGTH %d %d' %(id, sent_index, curr_sents[sent_index].length))
                    output.append('%s TEXT %d %s' %(id, sent_index, curr_sents[sent_index].original))
                    concept_list = ' '.join(map(str, curr_sent_concepts[sent_index]))
                    output.append('%s CONCEPTS %d %d %s' %(id, sent_index, len(curr_sent_concepts[sent_index]), concept_list))
    
                ## concept info
                for concept in curr_concept_weights.keys():
                    str_concept = '_'.join(concept)
                    concept_weight = curr_concept_weights[concept]
                    concept_index = curr_concept_index[concept]
                    output.append('%s CONCEPT_INFO %d %1.4f %s' %(id, concept_index, concept_weight, str_concept))

            ## ILP output format used by glpsol (glpk)
            else:
                problem = ilp.IntegerLinearProgram()
                problem.objective["score"] = ' + '.join(['%f c%d' %(weight, curr_concept_index[concept]) for concept, weight in curr_concept_weights.items()])
                
                s1 = ' + '.join(['%d s%d' %(curr_sents[sent_index].length, sent_index) for sent_index in range(len(curr_sents))])
                s2 = ' <= %s\n' %max_length
                problem.constraints["length"] = s1 + s2
                
                for concept, concept_index in curr_concept_index.items():
                    ## at least one sentence containing a selected bigram must be selected
                    s1 = ' + '.join([ 's%d' %sent_index for sent_index in curr_concept_sents[concept_index]])
                    s2 = ' - c%d >= 0' %concept_index                    
                    problem.constraints["presence_%d" % concept_index] = s1 + s2
                    ## if a bigram is not selected then all sentences containing it are deselected
                    s1 = ' + '.join([ 's%d' %sent_index for sent_index in curr_concept_sents[concept_index]])
                    s2 = '- %d c%d <= 0' %(len(curr_concept_sents[concept_index]), concept_index)
                    problem.constraints["absence_%d" % concept_index] = s1 + s2
                for sent_index in range(len(curr_sents)):
                    problem.binary["s%d" % sent_index] = curr_sents[sent_index]
                for concept, concept_index in curr_concept_index.items():
                    problem.binary["c%d" % concept_index] = 1
                #problem.debug = 1
                problem.run()
                output = []
                for sent_index in range(len(curr_sents)):
                    if problem.output["s%d" % sent_index] == 1:
                        output.append(curr_sents[sent_index])
                return output
                    
            outputs[id] = output
            sentences[id] = curr_sents
        return outputs, sentences


class CheatingMapper(Mapper):
    """
    Use human summaries to pick weights
    For Maximum ROUGE experiments
    """

    def map_concepts(self):

        concepts = {}
        for annotator in self.problem.annotators:
            annotator_concepts = {}
            for text in self.problem.training[annotator]:
                sentence = Sentence(text)
                units = self.unit_selector(sentence.stemmed)
                for unit in units:
                    if unit not in annotator_concepts: annotator_concepts[unit] = 0
                    annotator_concepts[unit] += 1
            for concept in annotator_concepts:
                if concept not in concepts: concepts[concept] = 0
                concepts[concept] += 1

        self.concept_sets = [concepts]

    def map_concepts2(self):
        """
        weight(unit) = number of manual summaries in which it occurs
        """

        ## check that manual summaries exist
        #if not self.problem.training_sent_sets:
        #    sys.stderr.write('Error: no training set loaded for problem [%s]\n' %self.problem.id)
        #    return None

        ## get concepts from the training sentences
        self.concept_sets = []
        for training_sent_set in self.problem.training_sent_sets:
            concepts = {}
            for annotator in self.problem.annotators:
                annotator_concepts = set()

                for sent in training_sent_set:
                    if sent.source != annotator: continue
                
                    ## TODO: using sent.stemmed -- could make this more general
                    units = self.unit_selector(sent.stemmed)

                    ## get rid of stopwords
                    #units = [u for u in units if not text.text_processor.is_just_stopwords(u)]
                    
                    annotator_concepts.update(set(units))

                for annotator_concept in annotator_concepts:
                    if annotator_concept not in concepts: concepts[annotator_concept] = 0
                    concepts[annotator_concept] += 1

            ## remove concepts with only 1 appearance
            #for concept, count in concepts.items():
            #    if count <= 1: del concepts[concept]

            ## add concepts for each training sentence set
            self.concept_sets.append(concepts)

    def choose_sents(self):
        """
        """

        ## check that concepts exist
        if not self.concept_sets:
            sys.stderr.write('Error: no concepts identified -- use map_concepts first\n')
            return None

        ## initialize new member variables
        self.concept_weight_sets = []
        self.concept_index_sets = []
        self.relevant_sent_sets = []
        self.relevant_sent_concepts = []

        ## loop over update sets
        for update_set_index in [0]:
            concept_weights = self.concept_sets[update_set_index]
            docset = self.problem.new_docs
            sents = []
            for doc in docset: sents.extend(doc.sentences)
            used_concepts = set()
            relevant_sents = []
            sent_concepts = []

            for sent in sents:
                ## skip short sentences
                #if sent.length <= 5: continue

                ## don't consider sentences with no query overlap
                #if self.problem.query:
                #    sim = sent.sim_basic(self.problem.query)
                #else: sim = 1
                #if sim > 0: continue

                units = self.unit_selector(sent.stemmed)

                ## concepts that appear in this sentence
                curr_concepts = set([u for u in units if u in concept_weights])

                ## skip sentences with no concepts
                if len(curr_concepts) == 0: continue

                ## add sentence and its concepts
                relevant_sents.append(sent)
                sent_concepts.append(curr_concepts)
                used_concepts.update(curr_concepts)

            ## create an index for mapping concepts to integers
            concept_weights_final = {}
            concept_index = {}
            index = 0
            for concept in used_concepts:
                concept_index[concept] = index
                concept_weights_final[concept] = concept_weights[concept]
                index += 1
            concept_weights = concept_weights_final

            ## set member variables
            self.concept_weight_sets.append(concept_weights)
            self.concept_index_sets.append(concept_index)
            self.relevant_sent_sets.append(relevant_sents)
            self.relevant_sent_concepts.append([[concept_index[c] for c in cs] for cs in sent_concepts])

        return True


class HeuristicMapper(Mapper):
    """
    """

    def map_concepts(self):
        """
        """
        min_count = 3
        use_log_weights = False

        ## get document statistics
        concept_sets = []
        sent_count = 0
        used_sents = set()

        for doc_set in [self.problem.new_docs]:
            concept_set = prob_util.Counter()
            for doc in doc_set:
                #if doc.doctype != 'NEWS STORY': continue
                doc_concepts = {}
                for sent in doc.sentences:
                    
                    sent_count += 1

                    ## ignore short sentences
                    if sent.length < self.min_sent_length: continue

                    ## ignore duplicate sentences
                    sent_stemmed_str = ' '.join(sent.stemmed)
                    if sent_stemmed_str in used_sents: continue
                    used_sents.add(sent_stemmed_str)

                    ## don't consider sentences with no query overlap
                    if self.problem.query:
                        sim = sent.sim_basic(self.problem.query)
                    else: sim = 1
                    if sim <= 0: continue

                    ## TODO: using sent.stemmed -- could make this more general
                    units = self.unit_selector(sent.stemmed)

                    for unit in units:
                        if not unit in doc_concepts: doc_concepts[unit] = 0
                        doc_concepts[unit] += 1         # simple count

                use_doc_freq = len(doc_set) > min_count

                for concept, count in doc_concepts.items():
                    if not concept in concept_set: concept_set[concept] = 0
                    if use_doc_freq: concept_set[concept] += 1      # doc frequency
                    else: concept_set[concept] += count             # raw frequency

            concept_sets.append(concept_set)

        ## apply a few transformations
        self.concept_sets = []
        for update_index in range(len(concept_sets)):
        
            final_concept_set = {}
            num_used_concepts = 0

            for concept in concept_sets[update_index].sortedKeys():
                count = concept_sets[update_index][concept]

                remove = False
                
                ## remove low frequency concepts
                if count < min_count: remove = True

                ## remove stop word concepts (word ngrams only!)
                if self.unit_name[0] in ['n', 's']:
                    if text.text_processor.is_just_stopwords(concept): remove = True

                ## use log weights
                if use_log_weights: score = math.log(count, 2)
                else: score = count

                ## add to final concept set
                if not remove:
                    final_concept_set[concept] = score
                    num_used_concepts += 1

            self.concept_sets.append(final_concept_set)

    def choose_sents(self):
        """
        """

        ## check that concepts exist
        if not self.concept_sets:
            sys.stderr.write('Error: no concepts identified -- use map_concepts first\n')
            return None

        ## initialize new member variables
        self.concept_weight_sets = []
        self.concept_index_sets = []
        self.relevant_sent_sets = []
        self.relevant_sent_concepts = []
        
        used_sents = set()  # just for pruning duplicates

        ## loop over update sets
        for update_set_index in range(len(self.concept_sets)):
            concept_weights = self.concept_sets[update_set_index]
            docset = self.problem.new_docs
            sents = []
            for doc in docset:
                #if doc.doctype != 'NEWS STORY': continue
                sents.extend(doc.sentences)
            used_concepts = set()
            relevant_sents = []
            sent_concepts = []

            for sent in sents:

                ## ignore short sentences
                if sent.length < self.min_sent_length: continue

                ## ignore duplicate sentences
                sent_stemmed_str = ' '.join(sent.stemmed)
                if sent_stemmed_str in used_sents: continue
                used_sents.add(sent_stemmed_str)

                ## get units
                units = self.unit_selector(sent.stemmed)

                ## concepts that appear in this sentence
                curr_concepts = set([u for u in units if u in concept_weights])

                ## skip sentences with no concepts
                if len(curr_concepts) == 0: continue

                ## add sentence and its concepts
                relevant_sents.append(sent)
                sent_concepts.append(curr_concepts)
                used_concepts.update(curr_concepts)

            ## create an index for mapping concepts to integers
            concept_weights_final = {}
            concept_index = {}
            index = 0
            for concept in used_concepts:
                concept_index[concept] = index
                concept_weights_final[concept] = concept_weights[concept]
                index += 1
            concept_weights = concept_weights_final

            ## set member variables
            self.concept_weight_sets.append(concept_weights)
            self.concept_index_sets.append(concept_index)
            self.relevant_sent_sets.append(relevant_sents)
            self.relevant_sent_concepts.append([[concept_index[c] for c in cs] for cs in sent_concepts])

        return True

def map_iterative_docs(docs, unit_selector, query):

    ## initialize uniform doc priors
    doc_values = prob_util.Counter()
    for doc in docs:
        doc_values[doc.docid] = 1
    doc_values = doc_values.makeProbDist()

    ## get units in each doc
    doc_units = {}
    used_sents = set()
    for doc in docs:
        doc_units[doc.docid] = prob_util.Counter()
        for sent in doc.sentences:

            if query:
                sim = sent.sim_basic(query)
            else: sim = 1
            if sim <= 0: continue

            units = unit_selector(sent.stemmed)
            for unit in units:
                if text.text_processor.is_just_stopwords(unit): continue

                doc_units[doc.docid][unit] += 1

    ## repeat until convergence
    for iter in range(1, 51):
        prev_doc_values = doc_values.copy()
        
        ## get unit values from doc values
        unit_values = prob_util.Counter()
        for doc in doc_units:
            for unit in doc_units[doc]:
                unit_values[unit] += doc_values[doc]
        unit_values = unit_values.makeProbDist()

        ## get doc values from unit values
        doc_values = prob_util.Counter()
        for doc in doc_units:
            for unit in doc_units[doc]:
                doc_values[doc] += unit_values[unit] / len(doc_units[doc])
                #print '%d, %s %1.4f %d' %(iter, unit, unit_values[unit], len(doc_units[doc]))
        doc_values = doc_values.makeProbDist()

        #prob_util.Counter(unit_values).displaySorted(N=5)
        #prob_util.Counter(doc_values).displaySorted(N=10)

        ## check for convergence
        if iter == 1: break
        dist = prob_util.euclidianDistance(prev_doc_values, doc_values)
        print 'dist [%1.6f]' %dist
        if dist < 0.0001: break

    #sys.exit()

    return prob_util.Counter(unit_values), prob_util.Counter(doc_values)


def map_iterative_sents(docs, unit_selector, query):

    ## get sentence set
    sents = []
    for doc in docs:
        for sent in doc.sentences:
            ## skip short sentences
            #if sent.length <= 5: continue

            ## skip sentences with no query overlap
            if query: sim = sent.sim_basic(query)
            else: sim = 1
            if sim <= 0: continue

            sents.append(sent)
            
    ## initialize uniform sentence priors
    sent_values = prob_util.Counter()
    for sent in sents:
        sent_values[sent.original] = 1
    sent_values = sent_values.makeProbDist()

    ## get units in each sent
    sent_units = {}
    for sent in sents:
        sent_units[sent.original] = prob_util.Counter()
        units = unit_selector(sent.stemmed)
        for unit in units:
            if text.text_processor.is_just_stopwords(unit): continue
            sent_units[sent.original][unit] += 1

    ## repeat until convergence
    for iter in range(1, 51):
        prev_sent_values = sent_values.copy()
        
        ## get unit values from doc values
        unit_values = prob_util.Counter()
        for sent in sent_units:
            for unit in sent_units[sent]:
                unit_values[unit] += sent_values[sent]
        unit_values = unit_values.makeProbDist()

        ## get sent values from unit values
        sent_values = prob_util.Counter()
        for sent in sent_units:
            for unit in sent_units[sent]:
                sent_values[sent] += unit_values[unit] #/ len(sent_units[sent])
        sent_values = sent_values.makeProbDist()

        #prob_util.Counter(unit_values).displaySorted(N=5)
        #prob_util.Counter(sent_values).displaySorted(N=3)

        ## check for convergence
        entropy_sent = prob_util.entropy(sent_values)
        entropy_unit = prob_util.entropy(unit_values)
        dist = prob_util.klDistance(prev_sent_values, sent_values)
        #print '%d sent entropy [%1.4f]  unit entropy [%1.4f]  sent dist [%1.6f]' %(iter, entropy_sent, entropy_unit, dist)
        if iter == 2: break
        if dist < 0.0001:
            #print '----------------------------'
            break

    return prob_util.Counter(unit_values), prob_util.Counter(sent_values)

def query_expand(docs, unit_selector, query):
    ## get sentence set
    sents = []
    for doc in docs:
        #if doc.doctype != 'NEWS STORY': continue
        for sent in doc.sentences:
            ## skip short sentences
            #if sent.length <= 5: continue
            sents.append(sent)
            
    ## initialize sentences with query similarity
    sent_values = prob_util.Counter()
    for sent in sents:
        try: sent_values[sent.original] = sent.sim_basic(query)
        except: sent_values[sent.original] = 1
    sent_values = sent_values.makeProbDist()

    ## get units in each sent
    sent_units = {}
    for sent in sents:
        sent_units[sent.original] = prob_util.Counter()
        units = unit_selector(sent.stemmed)
        for unit in units:
            if text.text_processor.is_just_stopwords(unit): continue
            sent_units[sent.original][unit] += 1

    ## repeat until convergence
    for iter in range(1, 51):
        prev_sent_values = sent_values.copy()

        ## get new unit values from sent values
        unit_values = prob_util.Counter()
        for sent in sent_units:
            for unit in sent_units[sent]:
                unit_values[unit] += sent_values[sent]
        unit_values = unit_values.makeProbDist()

        ## get sent values from unit values
        sent_values = prob_util.Counter()
        for sent in sent_units:
            for unit in sent_units[sent]:
                sent_values[sent] += unit_values[unit] #/ len(sent_units[sent])
        sent_values = sent_values.makeProbDist()

        #prob_util.Counter(unit_values).displaySorted(N=5)
        #prob_util.Counter(sent_values).displaySorted(N=20)

        ## check for convergence
        entropy_sent = prob_util.entropy(sent_values)
        entropy_unit = prob_util.entropy(unit_values)
        dist = prob_util.klDistance(prev_sent_values, sent_values)
        print '%d sent entropy [%1.4f]  unit entropy [%1.4f]  sent dist [%1.6f]' %(iter, entropy_sent, entropy_unit, dist)
        if iter == 2: break
        if dist < 0.0001:
            print '----------------------------'
            break
        
    return prob_util.Counter(unit_values), prob_util.Counter(sent_values)

class HeuristicMapperExp(Mapper):
    """
    """

    def map_concepts(self):
        """
        """

        ## get document statistics
        concept_sets = []
        sent_count = 0
        used_sents = set()

        for doc_set in [self.problem.new_docs]:
            concept_set = prob_util.Counter()
            concept_set, doc_values = query_expand(doc_set, self.unit_selector, self.problem.query)
            concept_sets.append(concept_set)

        ## apply a few transformations
        max_concepts = 60
        self.concept_sets = []
        for update_index in range(len(concept_sets)):
        
            final_concept_set = {}
            num_used_concepts = 0

            for concept in concept_sets[update_index].sortedKeys():
                count = concept_sets[update_index][concept]

                ## don't include more than max_concepts
                if num_used_concepts >= max_concepts: break

                remove = False
                
                score = count

                ## downweight concepts appearing in previous sets
                #for prev_index in range(update_index):
                #    if concept in concept_sets[prev_index]: score = 0.5*score

                ## add to final concept set
                if not remove:
                    final_concept_set[concept] = score
                    num_used_concepts += 1
                    #print count, concept

            self.concept_sets.append(final_concept_set)


    def choose_sents(self):
        """
        """

        ## check that concepts exist
        if not self.concept_sets:
            sys.stderr.write('Error: no concepts identified -- use map_concepts first\n')
            return None

        ## initialize new member variables
        self.concept_weight_sets = []
        self.concept_index_sets = []
        self.relevant_sent_sets = []
        self.relevant_sent_concepts = []
        
        ## loop over update sets
        for update_set_index in range(len(self.concept_sets)):
            concept_weights = self.concept_sets[update_set_index]
            docset = self.problem.new_docs
            used_sents = set()  # just for pruning duplicates

            sents = []
            for doc in docset:
                #if doc.doctype != 'NEWS STORY': continue
                sents.extend(doc.sentences)
                #sents.extend(doc.paragraphs)

            used_concepts = set()
            relevant_sents = []
            sent_concepts = []

            for sent in sents:

                ## ignore short sentences
                if sent.length < self.min_sent_length: continue

                ## ignore duplicate sentences
                sent_stemmed_str = ' '.join(sent.stemmed)
                if sent_stemmed_str in used_sents: continue
                used_sents.add(sent_stemmed_str)

                ## remove sentences with no query overlap
                #if sent.sim_basic(self.problem.query) <= 0: continue

                ## get units
                units = self.unit_selector(sent.stemmed)

                ## concepts that appear in this sentence
                curr_concepts = set([u for u in units if u in concept_weights])

                ## skip sentences with no concepts
                if len(curr_concepts) == 0: continue

                ## add sentence and its concepts
                relevant_sents.append(sent)
                sent_concepts.append(curr_concepts)
                used_concepts.update(curr_concepts)

            ## create an index for mapping concepts to integers
            concept_weights_final = {}
            concept_index = {}
            index = 0
            for concept in used_concepts:
                concept_index[concept] = index
                concept_weights_final[concept] = concept_weights[concept]
                index += 1
            concept_weights = concept_weights_final

            ## set member variables
            self.concept_weight_sets.append(concept_weights)
            self.concept_index_sets.append(concept_index)
            self.relevant_sent_sets.append(relevant_sents)
            self.relevant_sent_concepts.append([[concept_index[c] for c in cs] for cs in sent_concepts])

        return True

def concept_compare(mapper, gold_mapper):
    """
    compare mapper's concepts to the gold concepts
    """
    ## get concepts for the gold mapper (mapper should already be done)
    gold_mapper.map_concepts()
    gold_mapper.choose_sents()
    gold_mapper.format_output()

    for update_index in [0]:
        print 'update [%d]' %update_index

        gold_sorted_keys = prob_util.Counter(gold_mapper.concept_weight_sets[update_index]).sortedKeys()
        for concept in gold_sorted_keys:
            gold_weight = gold_mapper.concept_weight_sets[update_index][concept]
            try: heuristic_weight = mapper.concept_weight_sets[update_index][concept]
            except: heuristic_weight = 0
            print 'my[%1.2f] gold[%1.2f]  [%s]' %(heuristic_weight, gold_weight, ' '.join(concept), )
            
        heur_sorted_keys = prob_util.Counter(mapper.concept_weight_sets[update_index]).sortedKeys()
        for concept in heur_sorted_keys:
            if concept in gold_sorted_keys: continue
            heuristic_weight = mapper.concept_weight_sets[update_index][concept]
            print 'my[%1.2f] gold[%1.2f]  [%s]' %(heuristic_weight, 0, ' '.join(concept))
        print '----------------------------'

