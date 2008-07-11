import text, util

def by_date(sentences):
    return sorted(sentences, lambda x, y: cmp(x.order, y.order) if x.date == y.date else cmp(x.date, y.date))

class Cluster:
    def __init__(self, words, child1 = None, child2 = None, text = None):
        self.words = words
        self.child1 = child1
        self.child2 = child2
        self.text = text
        self.no_stop = set(self.words)

    def similarity(self, other):
        similarity = 0
        for word in self.words:
            if word in other.words:
                similarity += 1.0 * self.words[word] #/ other.words[word]
        similarity /= len(self.words)
        return similarity

    def __str__(self):
        output = str(self.text)
        if self.child1 and self.child2:
            if len(self.child1.words) > len(self.child2.words):
                output += str(self.child1) + str(self.child2)
            else:
                output += str(self.child2) + str(self.child1)
        return output

    def get_ordered(self, query):
        output = []
        if self.text != None:
            output = [self.text]
        else:
            #if len(self.child1.words) > len(self.child2.words):
            #if sum(self.child1.words.values()) > sum(self.child2.words.values()):
            if query.sim_basic(self.child1) > query.sim_basic(self.child2):
                output.extend(self.child1.get_ordered(query))
                output.extend(self.child2.get_ordered(query))
            else:
                output.extend(self.child2.get_ordered(query))
                output.extend(self.child1.get_ordered(query))
        return output

def merge_vectors(words1, words2):
    merged = {}
    for word in words1:
        if word not in merged: merged[word] = 0.0
        merged[word] += words1[word]
    for word in words2:
        if word not in merged: merged[word] = 0.0
        merged[word] += words2[word]
    return merged

def by_dendrogram(sentences, concept_weight, problem):
    cooccurrences = build_cooccurrence_matrix(problem)
    clusters = []
    for sentence in sentences:
        #concepts = util.get_ngrams(sentence.stemmed, n=1, bounds=False)
        #concepts = dict([(x, concept_weight[x]) for x in concepts if x in concept_weight])
        concepts = dict([(x, 1.0) for x in sentence.no_stop])
        clusters.append(Cluster(concepts, text=sentence))
    while len(clusters) > 1:
        max_sim = -1
        argmax = (None, None)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                #similarity = clusters[i].similarity(clusters[j]) + clusters[j].similarity(clusters[i])
                similarity = 0.0
                for word in clusters[i].words:
                    for peer in clusters[j].words:
                        occurrence = tuple(sorted([word, peer]))
                        if occurrence in cooccurrences:
                            similarity += cooccurrences[occurrence]
                similarity /= len(clusters[i].words) * len(clusters[j].words)
                #print similarity, i, j
                if(similarity > max_sim):
                    max_sim = similarity
                    argmax = (i, j)
        child1 = clusters[argmax[0]]
        child2 = clusters[argmax[1]]
        #print max_sim, child1.original_order, child2.original_order
        #clusters[argmax[0]] = Cluster(child1.words | child2.words, child1, child2)
        clusters[argmax[0]] = Cluster(merge_vectors(child1.words, child2.words), child1, child2)
        del clusters[argmax[1]]
    #print clusters[0]
    fake_query = text.Sentence('')
    fake_query.no_stop = {}
    for concept in concept_weight:
        for gram in concept:
                if gram not in text.text_processor._stopwords:
                    fake_query.no_stop[gram] = 1
    return clusters[0].get_ordered(fake_query)

def build_cooccurrence_matrix(problem):
    occurrences = {}
    for sentence in problem.get_new_sentences():
        for word in sentence.no_stop:
            for peer in sentence.no_stop:
                if word == peer: continue
                occurrence = tuple(sorted([word, peer]))
                if occurrence not in occurrences: occurrences[occurrence] = 0
                occurrences[occurrence] += 1
    return occurrences
