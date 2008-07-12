from treenode import *
from ilp import *
import re, sys

class TreebankNode (TreeNode):
    def __init__(self, text, start = 0, parent = None, root = None):
        TreeNode.__init__(self, text, start, parent, root)

    def firstNonPunctuationLeaf(self):
        for leaf in self.leaves:
            if re.match(r'[a-zA-Z0-9]', leaf.label):
                return leaf
        return None

    def lastNonPunctuationLeaf(self):
        for leaf in reversed(self.leaves):
            if re.match(r'[a-zA-Z0-9]', leaf.label):
                return leaf
        return None

    def getNounPhraseHead(self):
        candidate = self.children[-1]
        for child in self.children:
            if child.label == "," and candidate.text != "":
                break
            if child.label in ("QP", "NP", "NN", "NNS", "NNP", "NNPS", "NX"):
                candidate = child
                if candidate.label in ("NP", "QP", "NX"):
                    candidate = candidate.getNounPhraseHead()
        return candidate

    def isDayNounPhrase(self):
        if self.label != "NP":
            return False
        head = self.getNounPhraseHead()
        if head.text in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday") \
            or head.text in ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December") \
            or head.text in ("year", "years", "month", "months", "week", "weeks", "today", "tomorrow", "yesterday") \
            or head.text in ("afternoon", "morning", "evening", "night", "noon"):
            return True
        return False

    def isMandatoryRemoval(self):
        if self.label == "NP" and not self.hasParent("PP"):
            text = " ".join(x.text for x in self.leaves)
            if re.match(r'^(((last|next|this|today|tomorrow|yesterday) )?((Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day|afternoon|morning|evening|night))$', text, re.I):
                return True
        if self.label == "PP":
            text = " ".join(x.text for x in self.leaves)
            if re.match(r'^on (Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day$', text, re.I):
                return True
        if self.label == "ADVP" and len(self.children) == 1:
            if re.match(r'ly$', self.leaves[0].text):
                return True
            text = " ".join(x.text for x in self.leaves)
            if re.match(r'\b(However|Hence|Indeed|Now|Otherwise|Then|Still|Nonetheless|nevertheless|Therefore|Again|There|Later|Well|Also|Instead|Meanwhile|Overall|Already|Alike|Sometimes|Soon|Perhaps|next|Further|Furthermore|Yet|Rather|Regardless|Even|Afterward|After|First|Second|Thrid|Thereafter|Anyway|So|Altogether|Alone|Likewise|Either|Nevertheless|Moreover|Overnight|Thus|So Far|And|Besides|By the way|Henceforth|Although|Despite|Notwithstanding)\b', text, re.I):
# Never|Hardly
                return True
        if self.label == "NNP" and self.text in ("Inc.", "Ltd."):
            return True
        # remove But, And, Or in sentence start
        if self.root.firstNonPunctuationLeaf() == self and self.label == "CC":
            return True

    def isRemovable(self):
        # don't remove the root
        if self.parent == None:
            self.reason = 1
            return False

        # prevent breaking conjonctive and disjonctives
        if self.parent.hasChild("CC"):
            self.reason = 2
            return False

        # some expressions are removed definitively
        if self.isMandatoryRemoval():
            self.mandatory_removal = True
            return True

        # temporal phrases can be removed unless they are specific (Jan. 1 1999, 12pm)
        if self.label in ("PP", "ADVP"):
            children = self.getChildrenByFilter(self.__class__.isDayNounPhrase)
            parentDays = self.parent.getNodesByFilter(self.__class__.isDayNounPhrase)
            if len(parentDays) > 1:
                self.reason = 81
                return False
            if len(children) == 1:
                self.reason = 8
                return True
        if self.isDayNounPhrase() and self.parent.label not in ("PP", "ADVP"):
            parentDays = self.parent.getNodesByFilter(self.__class__.isDayNounPhrase)
            if len(parentDays) > 1:
                self.reason = 91
                return False
            if self.hasChild("POS") or self.hasChild("CD") or self.hasChild("QP"):
                self.reason = 9
                return False
            self.reason = 10
            return True

        # don't remove things before the verb in a verbal phrase
        if self.parent.label == "VP":
            verb_children = self.parent.getChildrenByFilter(lambda x: re.match(r'^(V|MD)', x.label))
            if len(verb_children) == 0:
                self.reason = 21
                return False
            if self.index <= verb_children[-1].index + 1:
                self.reason = 22
                return False

        # parentheses and a few appositives are removable
        if self.label == "PRN":
            self.reason = 5
            return True    

        # comma enclosed appositives
        if self.label in ("NP", "PP") and self.parent.label == "NP":
            num_commas = len(self.parent.getChildrenByLabel(","))
            # more than 2 commas: might be a list
            if num_commas > 0 and num_commas != 2:
                self.reason = 6
                return False
            # verify comma enclosure
            if self.nextSlibling != None and self.nextSlibling.label == "," and self.previousSlibling != None and self.previousSlibling.label == ",":
                self.reason = 7
                return True

        # try to remove subordinate clauses
        if self.label == "SBAR":
            if self.leaves[0].text == "that": # that after a verb might be the object
                verb = filter(lambda x: re.match(r'^V', x.label), self.parent.children[0:self.index])
                if len(verb) > 0:
                    self.reason = 15
                    return False
            # prevent "He said (+R on Thursday) (+R that he is going to ...)"
            if self.previousSlibling != None and self.previousSlibling.isRemovable():
                self.reason = 14
                return False
            # would break "as soon as and comparatives" (but "as" used as "because" can be removed)
            if self.leaves[0].text == "as" and self.parent.hasLeaf(lambda x: x.text == "as" and not x.hasParent(self)):
                self.reason = 11
                return False
            # would break comparatives "it was longer *than* when he went home"
            if self.leaves[0].text == "than":
                self.reason = 12
                return False
            # "he is such a small person that he ..."
            if self.leaves[0].text == "that" and self.parent.hasLeaf(lambda x: x.text in ("such", "so") and not x.hasParent(self)):
                self.reason = 31
                return False
            # hack: prevent errors like "... advice on (+R where to go)"
            if self.leaves[0].previousLeaf != None and self.leaves[0].previousLeaf.label == "IN":
                self.reason = 3
                return False
            if self.leaves[-1].nextLeaf != None and self.leaves[-1].nextLeaf.label == "IN":
                self.reason = 4
                return False
            # the SBAR might be specifing a quantifier
            if self.leaves[0].previousLeaf != None and re.match(r'^(those|most|many|few|some)$', self.leaves[0].previousLeaf.text, re.I):
                self.reason = 41
                return False
            self.reason = 13
            return True

        # try to remove adverbial phrases (the parser seems to do a lot of errors regarding those)
        if self.label == "ADVP" and self.hasChild("RB") and not self.hasParent("ADVP"):
            # the phrase could be subject of a verb
            if len(self.parent.children) < 3:
                self.reason = 24
                return False
            # the adverbial phrase is anchored at the begining or the end of the sentence
            if self.root.firstNonPunctuationLeaf() == self.leaves[0] or self.root.lastNonPunctuationLeaf() == self.leaves[-1]:
                self.reason = 23
                return True

        # try to remove prepositional phrases
        if self.label == 'PP':
            # don't break double prepositions
            if self.previousLeaf != None and self.previousLeaf.label == "IN":
                reason = 83
                return False
            # 
            previous = filter(lambda x: re.match(r'^(N|PP)', x.label), self.parent.children[0:self.index])
            if len(previous) > 0 and self.previousLeaf.label != 'DT':
                reason = 82
                return True

        return False

    def isSubsentence(self):
        if self.label != "S":
            return False
        if len(self.children) < 2:
            return False
        subjectChildren = self.getChildrenByLabel("NP")
        verbChildren = self.getChildrenByLabel("VP")
        if(len(subjectChildren) == 0 or len(verbChildren) == 0):
            return False
        if verbChildren[0].index < subjectChildren[0].index:
            return False
        if verbChildren[0].hasChild("VBG") or verbChildren[0].hasChild("TO"):
            return False
        if subjectChildren[0].getNounPhraseHead().label == "PRP" or subjectChildren[0].leaves[0].label == "PRP$":
            return False
        return True

    def getCandidates(self, beam = 0, mapping = None, use_mandatory_removals=True):
        if use_mandatory_removals and self.isRemovable() and hasattr(self, "mandatory_removal") and self.mandatory_removal:
            return {}
        output = {"":0}
        if self.text != "":
            output = {" %s" % self.text:1}
        for child in self.children:
            child_output = child.getCandidates(beam, mapping, use_mandatory_removals)
            new_output = {}
            for i in output.keys():
                for j in child_output.keys():
                    new_output["%s%s" % (i, j)] = output[i] + child_output[j]
            output = new_output
        if beam > 0 and len(output) > beam:
            keys = output.keys()
            keys.sort(lambda y, x: output[x] - output[y])
            new_output = {}
            for key in keys[0:beam]:
                new_output[key] = output[key]
            output = new_output
        if self.isRemovable():
            output[""] = 0
        if mapping and self.label == "NP":
            text = " ".join(str(leaf) for leaf in self.leaves)
            leaves_text = " ".join(leaf.text for leaf in self.leaves)
            if text in mapping:
                mapped_text = re.sub(r'(\([^ ]+ |\))', '', mapping[text])
                if leaves_text != mapped_text:
                    output[" " + mapped_text] = len(mapped_text.split())
        return output

    def getNonCompressedTree(self):
        output = "(+S"
        for leaf in self.leaves:
            if leaf.text != "":
                output += " " + "(" + leaf.label + " " + leaf.text + ")"
        output += ")"
        return output

    def getNonCompressedCandidate(self):
        return "(+S " + " ".join(map(str, self.leaves)) + ")"

    def getCandidateTree(self, mapping = None):
        output = ""
        if self.isLeaf():
            return " " + str(self)
        removable = self.isRemovable()
        subsentence = self.isSubsentence()
        children_already_processed = False
        alternative = False
        alternative_text = ""
        if mapping and self.label == "NP":
            text = " ".join(str(leaf) for leaf in self.leaves)
            if text in mapping:
                alternative = True
                alternative_text = mapping[text]
                removable = False
        if subsentence:
            output += " (+S"
        elif removable:
            output += " (+R"
        elif alternative:
            output += " ( (+A"
        if not children_already_processed:
            for child in self.children:
                output += child.getCandidateTree(mapping)
        if removable or subsentence:
            output += ")"
        elif alternative:
            output += ") (+A "+ alternative_text + "))"
        return output

    def getPrettyCandidates(self, attributes = []):
        output = " (" + self.label
        if type(attributes) != type([]):
            attributes = [attributes]
        for attribute in attributes:
            if hasattr(self, attribute):
                output += ":" + attribute + "=" + getattr(self, attribute)
        for child in self.children:
            if child.text != "":
                output += " " + child.text
            else:
                output += child.getPrettyCandidates(attributes)
        output += " )"
        return output

    def getFlatTree(self):
        output = "(" + self.label
        if self.isRemovable():
            output += "+R"
        if self.isSubsentence():
            output += "+S"
        for child in self.children:
            output += " " + child.getFlatTree()
        if len(self.children) == 0 or self.parent == None:
            output = output + " " + self.text
        output = output + ")"
        return output

    def getMandatoryRemovalCandidate(self):
        output = ""
        if self.isRemovable():
            if hasattr(self, "mandatory_removal") and self.mandatory_removal:
                output = " (+M"
            else:
                output += " (+R"
        if self.isLeaf():
            output = " " + self.text
        for child in self.children:
            output += child.getMandatoryRemovalCandidate()
        if self.isRemovable():
            output += ")"
        return output

    def getMinimalCandidate(self):
        if self.isRemovable():
            return ""
        output = ""
        if self.isLeaf():
            output = " " + self.text
        for child in self.children:
            output += child.getMinimalCandidate()
        return output

    def getTabbedRepresentation(self, tabs = "", firstChild = True):
        label = self.label
        if self.isDayNounPhrase():
            label += "+D"
        if self.isRemovable():
            label += "+R"
        if self.isSubsentence():
            label += "+S"
        if hasattr(self, "reason"):
            label += ":" + str(self.reason)
        if firstChild:
            output = "(" + label + " "
        else:
            output = "\n" + tabs + "(" + label + " "
        tabs = tabs + (" " * (len(label) + 2))
        firstChild = True
        for child in self.children:
            output +=  child.getTabbedRepresentation(tabs, firstChild)
            firstChild = False
        if len(self.children) == 0 or self.parent == None:
            output += self.text
        output = output + ")"
        return output

class SentenceSelectionILP(IntegerLinearProgram):
    def __init__(self, concept_weight, length_limit, \
            use_removables = True, \
            use_subsentences = True, \
            use_alternatives = True, \
            use_min_length = True, \
            min_length = 10, \
            use_min_length_ratio = False, \
            min_length_ratio = 0.5):
        IntegerLinearProgram.__init__(self)
        self.use_removables = use_removables
        self.use_subsentences = use_subsentences
        self.use_alternatives = use_alternatives
        self.use_min_length = use_min_length
        self.min_length = min_length
        self.use_min_length_ratio = use_min_length_ratio
        self.min_length_ratio = min_length_ratio
        self.next_sentence_id = 0
        self.concept_weight = concept_weight
        self.length_limit = length_limit
        self.concept_dict = {}
        self.dict_to_weight = {}
        next_concept_id = 0
        for concept in self.concept_weight:
            id = "c" + str(next_concept_id)
            self.concept_dict[concept] = id
            self.dict_to_weight[id] = concept_weight[concept]
            next_concept_id += 1
        self.constraints["length"] = ""

    def nodeHasSelectedParent(self, node):
        if node.parent != None:
            if hasattr(node.parent, "id") and node.parent.id in self.output and self.output[node.parent.id] == 1:
                return True
            return self.nodeHasSelectedParent(node.parent)
        return False

    def getSelectedText(self, node):
        output = ""
        if node.id in self.output and self.output[node.id] == 1:
            for child in node.children:
                if child.text != "":
                    output += " " + child.text
                else:
                    output += self.getSelectedText(child)
        return output

    def nodeIsSubsentence(self, node):
        if self.use_subsentences:
            return node.label.endswith("+S")
        return node.label.endswith("+S") and len(node.getParentsByLabel("+S")) == 0

    def nodeIsRemovable(self, node):
        if self.use_removables:
            return len(node.getParentsByFilter(lambda x: self.nodeIsSubsentence(x))) > 0 and node.label.endswith("+R")
        return False

    def nodeIsAlternative(self, node):
        if self.use_alternatives:
            return len(node.getParentsByFilter(lambda x: self.nodeIsSubsentence(x))) > 0 and node.label.endswith("+A")
        return False

    def getConcepts(self, node, get_concepts_from_node):
        length, concepts = get_concepts_from_node(node)
        for child in node.children:
            if not child.isLeaf():
                concepts.update(self.getConcepts(child, get_concepts_from_node))
        return concepts

    def addSentence(self, node, get_concepts_from_node):
        if self.nodeIsSubsentence(node) or self.nodeIsRemovable(node) or self.nodeIsAlternative(node):
            node.id = "s%d" % self.next_sentence_id
            self.next_sentence_id += 1
            self.binary[node.id] = node
        elif node.parent != None and hasattr(node.parent, "id"):
            node.id = node.parent.id
        cumulative_length = 0
        for child in node.children:
            if not child.isLeaf():
                cumulative_length += self.addSentence(child, get_concepts_from_node)
            if not hasattr(node, "id"):
                continue
            if self.nodeIsSubsentence(child):
                self.constraints["sub_%s_%s" % (node.id, child.id)] = "%s - %s <= 0" % (node.id, child.id)
            if self.nodeIsRemovable(child):
                self.constraints["rem_%s_%s" % (node.id, child.id)] = "%s - %s <= 0" % (child.id, node.id)
            if self.nodeIsAlternative(child):
                name = "alt_%s_%d" % (node.id, node.index) # hack: prevent collision with another alternative from the parent
                if name not in self.constraints:
                    self.constraints[name] = " - " + node.id + " + " + child.id
                else:
                    self.constraints[name] += " + " + child.id
        if not node.isLeaf():
            node.length, node.concepts = get_concepts_from_node(node)
            cumulative_length += node.length
        if self.nodeIsSubsentence(node) or self.nodeIsRemovable(node) or self.nodeIsAlternative(node):
            node.length = cumulative_length
            cumulative_length = 0
            self.constraints["length"] += " + %d %s" % (node.length, node.id)
            for concept in node.concepts:
                if concept not in self.concept_dict:
                    continue
                concept = self.concept_dict[concept]
                name = "in_%s_%s" % (node.id, concept)
                self.constraints[name] = node.id + " - " + concept + " <= 0"
                self.binary[concept] = 1
                name = "presence_" + concept
                if name not in self.constraints:
                    self.constraints[name] = " - " + concept
                self.constraints[name] += " + " + node.id
            if self.use_min_length or self.use_min_length_ratio \
                    and len(node.getParentsByFilter(lambda x: self.nodeIsSubsentence(x) or self.nodeIsRemovable(x))) == 0:
                from_same_sentence = [x for x in node if self.nodeIsSubsentence(x) or self.nodeIsRemovable(x) or self.nodeIsAlternative(x)]
                total_length = reduce(lambda x, y: x + y, [x.length for x in from_same_sentence], 0)
                for removable in from_same_sentence:
                    name = "min_length_%s" % removable.id
                    self.constraints[name] = " + ".join("%d %s" % (x.length, x.id) for x in from_same_sentence if x != removable) 
                    actual_length = removable.length
                    min_length_ratio = int(total_length * self.min_length_ratio)
                    if self.use_min_length:
                        actual_length -= self.min_length
                        if self.use_min_length_ratio and self.min_length < min_length_ratio:
                            actual_length -= min_length_ratio
                    else:
                        actual_length -= min_length_ratio
                    self.constraints[name] += " %+d %s >= 0" % (actual_length, removable.id)
        return cumulative_length

    def run(self):
        self.constraints["length"] += " <= %d" % self.length_limit
        #del self.constraints["length"]
        self.objective["score"] = ""
        for constraint in self.constraints:
            if constraint.startswith("alt_"):
                self.constraints[constraint] += " = 0"
        for concept in self.binary.keys():
            if concept.startswith("c"):
                if self.dict_to_weight[concept] >= 0:
                    self.objective["score"] += " +"
                else:
                    self.objective["score"] += " -"
                self.objective["score"] += " %f %s" % (self.dict_to_weight[concept], concept)
                self.constraints["presence_%s" % concept] += " >= 0" 
        IntegerLinearProgram.run(self)

def postProcess(text):
    import re
    text = re.sub('-LRB-', '(', text)
    text = re.sub('-RRB-', ')', text)
    text = re.sub(' +', ' ', text)
    text = re.sub('^ ', '', text)
    text = re.sub(' $', '', text)
    text = re.sub(' ?,( ?,)+ ?', ' ', text)
    text = re.sub('`` ', '', text)
    text = re.sub(' \'\'', '', text)
    text = re.sub('\( ', '(', text)
    text = re.sub(' \)', ')', text)
    text = re.sub(' n\'t', 'n\'t', text)
    text = re.sub(r'\$ ([0-9])', r'$\1', text)
    text = re.sub(' ([^a-zA-Z0-9\-()\$])', r'\1', text)
    text = re.sub('^([,.;:?! ])+', '', text)
    text = re.sub('([,.;:?! ])+$', '', text)
    text = re.sub('([A-Za-z0-9])', (lambda x: x.group(1).capitalize()), text, 1)
    if not re.match(r'\.[^a-zA-Z0-9]+$', text):
        text = text + '.'
    return text

def get_concepts(words):
    alpha_numeric = re.compile(r'[a-zA-Z0-9]')
    output = []
    if type(words) != type([]):
        words = words.split()
    words = filter(alpha_numeric.match, words)
    for i in range(len(words) - 1):
        concept = (words[i], words[i + 1])
        output.append(concept)
    return output

regex_is_alpha_numeric = re.compile(r'[a-zA-Z0-9]')
regex_is_not_stopword = re.compile(r'^[NVJF]')

def get_bigrams_from_node(node, \
        node_skip = (lambda x: not regex_is_not_stopword.match(x.label)), \
        node_transform = (lambda x: x.text), \
        node_breaker = (lambda x: not x.isLeaf()), \
        use_leaves = False, return_length = True, generate_unigrams=False):
    tokens = []
    nodes = node.children
    if use_leaves:
        nodes = node.leaves
    output = {}
    filtered_nodes = filter(lambda x: not (x.isLeaf() and node_skip(x)), nodes)
    #output = dict((node_transform(x), 1) for x in filtered_nodes)
    for i in range(len(filtered_nodes) - 1):
        if node_breaker(filtered_nodes[i]) or node_breaker(filtered_nodes[i + 1]):
            continue
        if generate_unigrams:
            concept = tuple([node_transform(filtered_nodes[i])])
            output[concept] = 1
        concept = (node_transform(filtered_nodes[i]), node_transform(filtered_nodes[i + 1]))
        output[concept] = 1
    if generate_unigrams:
        concept = tuple([node_transform(filtered_nodes[-1])])
        output[concept] = 1
    if return_length:
        length = len(filter(lambda x: regex_is_alpha_numeric.match(x.text), nodes))
        return length, output
    return output

def generateNounPhraseMapping(treenodes):
    potential_mappings = {}
    for root in treenodes:
        # get all potential noun phrases
        noun_phrases = root.getNodesByFilter(lambda x: x.label == "NP" and not x.hasChild("CC") and not x.hasChild("QP") and not x.hasChild("CD"))
        for noun_phrase in noun_phrases:
            head = noun_phrase.getNounPhraseHead()
            noun_phrase.head_cache = head

        # restrict to minimal noun phrases (not having a parent with the same head)
        noun_phrases = [x for x in noun_phrases if len(x.getParentsByFilter(lambda y: hasattr(y, "head_cache") and y.head_cache == x.head_cache)) == 0]

        # fix heads with determiners and possessives to prevent ungrammatical mappings
        for noun_phrase in noun_phrases:
            head = noun_phrase.head_cache
            noun_phrase.head_cache = head.text
            parent_leaves = head.parent.leaves
            if parent_leaves[-1].label == "POS":
                noun_phrase.head_cache += parent_leaves[-1].text
            if parent_leaves[0].label in ("DT", "PRP$") :
                noun_phrase.head_cache = parent_leaves[0].text + " " + noun_phrase.head_cache

        # count potential head-nounphrase relations
        for noun_phrase in noun_phrases:
            #noun_phrase.getText_cache = str(noun_phrase) #.getText()
            noun_phrase.getText_cache = " ".join(str(leaf) for leaf in noun_phrase.leaves)
            if noun_phrase.head_cache not in potential_mappings: potential_mappings[noun_phrase.head_cache] = {}
            if noun_phrase.getText_cache not in potential_mappings[noun_phrase.head_cache]: potential_mappings[noun_phrase.head_cache][noun_phrase.getText_cache] = 0
            potential_mappings[noun_phrase.head_cache][noun_phrase.getText_cache] += 1

    # remove unfrequent mappings
    for head, list_of_np in potential_mappings.items():
        for text, frequency in list_of_np.items():
            if frequency < 2:
                del list_of_np[text]
        if len(list_of_np) < 2:
            del potential_mappings[head]

    # map each noun phrase to the smallest in the same class
    final_mapping = {}
    for head, list_of_np in potential_mappings.items():
        for np in list_of_np:
            min_length = sys.maxint
            words = np.split()
            mapping = np
            for peer in list_of_np:
                if peer == np: continue
                peer_words = peer.split()
                skip = 0
                for word in peer_words:
                    if word not in words:
                        skip = 1
                        break
                if not skip:
                    if min_length > len(peer_words):
                        mapping = peer
                        min_length = len(peer_words)
            if mapping != np:
                final_mapping[np] = mapping
    return final_mapping

def min_backtrack(values):
    argmin = 0
    for i in range(len(values)):
        if values[argmin] > values[i]:
            argmin = i
    return values[argmin], argmin

def alignAcronym(sequence1, sequence2):
    len1 = len(sequence1) + 1
    len2 = len(sequence2) + 1
    if len1 <= 2 or len2 <= 2: return None
    cost = [[0 for x in range(len2)] for y in range(len1)]
    backtrack = [[0 for x in range(len2)] for y in range(len1)]
    for i in range(len1):
        cost[i][0] = i
        backtrack[i][0] = 1
    for i in range(len2):
        cost[0][i] = i
        backtrack[0][i] = 2
    for i in range(1, len1):
        for j in range(1, len2):
            local_cost = 0
            if sequence1[i - 1] != sequence2[j - 1][0]:
                local_cost += 3
            cost[i][j], backtrack[i][j] = min_backtrack((cost[i - 1][j - 1] + local_cost, cost[i - 1][j] + 1, cost[i][j - 1] + 1))
    i = len1 - 1
    j = len2 - 1
    output = []
    while i > 1 and j > 1:
        if backtrack[i][j] == 0:
            i -= 1
            j -= 1
        elif backtrack[i][j] == 1:
            i -= 1
        elif backtrack[i][j] == 2:
            j -= 1
    hypothesis = sequence2[j - 1:]
    if j - 1 >= len(sequence2) or sequence2[j - 1][0] != sequence1[0] or i != 1 or len(hypothesis) < len1 - 1:
        return None
    return " ".join(hypothesis)

def generateAcronymMapping(sentences):
    output = {}
    for sentence in sentences:
        found = re.search(r'([^\)\(]+) *\( *([A-Z]+) *\)', sentence.original)
        if found:
            acronym = found.group(2)
            words = found.group(1).strip().split()
            filtered = []
            while len(words) > 0:
                word = words.pop()
                if word in ("the", "The") and len(filtered) >= len(acronym):
                    break
                filtered.append(word)
            filtered.reverse()
            words = filtered
            if len(words) > len(acronym) * 2:
                words = words[len(words) - len(acronym) * 2:]
            mapping = alignAcronym(acronym, words)
            if mapping:
                output[mapping] = acronym
    return output

def replaceAcronyms(sentences, mapping):
    for sentence in sentences:
        text = sentence.original
        for definition, acronym in mapping.items():
            definition = re.sub(r'[^A-Za-z]+', '[^A-Za-z]+', definition)
            text = re.sub(r'\b' + definition + r'(\s*(\(' + acronym + r'\))|\b)', acronym, text)
        if text != sentence.original:
            sentence.set_text(text)

def addAcronymDefinitionsToSummary(summary, mapping):
    seen = {} 
    for definition, acronym in mapping.items():
        if acronym in seen: continue # the acronym might be mapped twice with different writings...
        summary = re.sub(r'\b' + acronym + r'([^A-Za-z0-9-])', definition + ' (' + acronym + r')\1', summary, 1)
        seen[acronym] = 1
    summary = re.sub(r'( +\([^\)]+\))\'s ', r"'s\1 ", summary)
    return summary

if __name__ == "__main__":
    import sys
    id = 1
    for line in sys.stdin.readlines():
        root = TreebankNode(line.strip())
        #subsentences = root.getNodesByFilter(TreebankNode.isSubsentence)
        #for node in subsentences:
        #    print id, postProcess(node.getMinimalCandidate())
        print root.getMandatoryRemovalCandidate()
        #candidates = TreebankNode(root.getCandidateTree())
        #print id, candidates.getPrettyCandidates()
        #print root.getTabbedRepresentation()
        #print
        id += 1
    sys.exit(0)

if __name__ == "__main__":
    import sys
    lines = sys.stdin.readlines()

    # gather concepts (as an example)
    concept_weight = {}
    roots = []
    for line in lines:
        root = TreebankNode(line.strip())
        roots.append(root)
        for concept in get_bigrams_from_node(root, use_leaves = True, return_length = False):
            if concept not in concept_weight: concept_weight[concept] = 0
            concept_weight[concept] += 1
    for concept in concept_weight.keys():
        if type(concept) == type("") and concept_weight[concept] < 10:
            del concept_weight[concept]
        elif concept_weight[concept] < 3:
            del concept_weight[concept]

    # the ILP keeps tracks of the constraints
    # s<num> variables handle sentences, subsentences and removable subtrees
    # c<num> variables represent concepts in those selected pseudo-sentences
    program = SentenceSelectionILP(concept_weight, 100, use_subsentences = True, use_removables = True, use_min_length = True, use_min_length_ratio = False)

    nounPhraseMapping = generateNounPhraseMapping(roots)
    
    for root in roots:
        # generate a compression candidate tree (or a non compressed tree)
        candidates = root.getCandidateTree(nounPhraseMapping)
        candidate_root = TreebankNode(candidates)
        #candidate_root = TreeNode(root.getNonCompressedCandidate())
        candidate_root.original = root
        candidate_root.original_text = candidates

        # update ILP with the new sentence
        program.addSentence(candidate_root, get_bigrams_from_node)

    # finish and run the program (and get the output)
    program.debug = 1
    program.run()

    # get the selected sentences
    for id in program.output:
        if id.startswith("s") and program.output[id] == 1:
            node = program.binary[id] # gives you back the actual node (which can be a subsentence, or a chunk not removed)
            if not program.nodeHasSelectedParent(node): # only start printing at the topmost nodes
                #print node.root.original_text
                print postProcess(program.getSelectedText(node))
                print "    " + str(node.root.original)
                print "    " + node.root.getPrettyCandidates()

