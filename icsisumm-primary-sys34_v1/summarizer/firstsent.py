import os, sys, re, tempfile, random, time
import util

## globals
SVM_LEARN = '/u/dgillick/tools/svm_perf/svm_perf_learn'
SVM_CLASSIFY = '/u/dgillick/tools/svm_perf/svm_perf_classify'

def get_features(sent, tag):

    tokens = sent.split()
    tags = [t.split('/')[-1] for t in tag.split()]
    #structs = [p.split()[0] for p in parse.split('(') if len(p.strip())>0]

    feats = {}

    ## number of tokens
    length = len(tokens)
    feats['len'] = length / 30.0

    ## connector words
    connectors = set(['however', 'because', 'and', 'so', 'also', 'nonetheless',
                      'still', 'but'])
    feats['connect'] = tokens[0].lower() in connectors

    ## number of capitalized words (assume 1st word is always capitalized)
    num_cap = len([1 for token in tokens[1:] if token[0].isupper()])
    feats['cap'] = 1.0 * num_cap / max((length-1), 1)

    ## pronouns (PRP$ are possessive; WP are who, what, which, when)
    num_pron = len([1 for tag in tags if tag in ['PRP$']])
    feats['prn'] = 1.0 * num_pron / length

    ## definite articles
    num_da = len([1 for token in tokens if token.lower() in ['the', 'that', 'these', 'those', 'this']])
    feats['da'] = 1.0 * num_da / length

    ## the [A-Z] construction
    feats['cap_cons'] = len(re.findall('[t|T]he [A-Z]', sent))

    ## first word
    #feats['first=%s' %tokens[0].lower()] = 1
    #feats['first_pos=%s' %tags[0]] = 1

    ## token ngrams
    ngrams = util.get_ngrams(tokens, 1, False) + util.get_ngrams(tokens, 2, True) 
    for ngram in ngrams:
        feats['tok=%s' %'_'.join(ngram).lower()] = 1

    ## tag ngrams
    ngrams = util.get_ngrams(tags, 2, True) #+ util.get_ngrams(tags, 4, True)
    for ngram in ngrams:
        feats['pos=%s' %'_'.join(ngram)] = 1

    ## parser ngrams
    #ngrams = util.get_ngrams(structs, 4, True)
    #for ngram in ngrams:
    #    feats['struct=%s' %'_'.join(ngram)] = 1

    ## quotes
    feats['quotes'] = int('"' in tokens)
    #num_tokens_in_quotes = 0
    #num_quotes = 0
    #in_quotes = False
    #for token in tokens:
    #    if token == '"':
    #        in_quotes = not in_quotes
    #        num_quotes += 1
    #    else:
    #        if in_quotes: num_tokens_in_quotes += 1
    #feats['in_quotes'] = 1.0 * num_tokens_in_quotes / (length - num_quotes)
    
    return feats


class Hyp:
    def __init__(self):
        self.original = None
        self.features = None
        self.label = None        

class Model:
    def __init__(self, path):
        self.path = path
        self.featdict = {}

    def train(self, data):
        abstract

    def classify(self, data):
        abstract

    def save(self):
        util.save_pickle(self.featdict, self.path + 'feats')

    def load(self):
        self.featdict = util.load_pickle(self.path + 'feats')

class SVM_Model(Model):

    def train(self, data):

        model_file = '%s/svm_model' %self.path

        ## integer dictionary for features
        sys.stderr.write('training. making feat dict... ')
        feat_list = set()
        for hyp in data:
            for feat in hyp.features: feat_list.add(feat)
        self.featdict = dict(zip(feat_list, range(1,len(feat_list)+1)))
        
        ## training data file
        sys.stderr.write('writing... ')
        lines = []
        for hyp in data:
            if hyp.label == None: util.die('expecting labeled data')
            elif hyp.label > 0.0: svm_label = '+1'
            elif hyp.label < 0.0: svm_label = '-1'
            else: continue
            line = '%s ' %svm_label
            svm_feats = [(self.featdict[f], v) for (f,v) in hyp.features.items()]
            svm_feats.sort(lambda x,y: x[0]-y[0])
            line += ' '.join(['%d:%1.4f' %(f,v) for (f,v) in svm_feats])
            lines.append(line)

        unused, train_file = tempfile.mkstemp()
        fh = open(train_file, 'w')
        fh.write('\n'.join(lines) + '\n')
        fh.close()
    
        ## train an svm model
        start_time = time.time()
        sys.stderr.write('running svm... ')
        options = '-v 0 -c 1' #-t 1 -r 1 -d 2' #-c 1
        cmd = '%s %s %s %s' %(SVM_LEARN, options, train_file, model_file)
        os.system(cmd)
        total_time = time.time() - start_time
        sys.stderr.write('done! time [%1.2f]\n' %total_time)

        ## clean up
        os.remove(train_file)

    def classify(self, data):

        model_file = '%s/svm_model' %self.path
        if not self.featdict: util.die('Incomplete model')
        if not os.path.isfile(model_file): util.die('no model [%s]' %model_file)

        ## testing data file
        sys.stderr.write('SVM classifying... ')
        lines = []
        for hyp in data:
            if hyp.label == None: svm_label = '0'
            elif hyp.label == 1: svm_label = '+1'
            elif hyp.label == -1: svm_label = '-1'
            else: continue
            line = '%s ' %svm_label
            svm_feats = [(self.featdict[f], v) for (f,v) in hyp.features.items() if f in self.featdict]
            svm_feats.sort(lambda x,y: x[0]-y[0])
            line += ' '.join(['%d:%1.4f' %(f,v) for (f,v) in svm_feats])
            lines.append(line)

        unused, test_file = tempfile.mkstemp()
        fh = open(test_file, 'w')
        fh.write('\n'.join(lines) + '\n')
        fh.close()
    
        ## classify test data
        unused, pred_file = tempfile.mkstemp()
        options = '-v 0'
        cmd = '%s %s %s %s %s' %(SVM_CLASSIFY, options, test_file, model_file, pred_file)
        os.system(cmd)

        ## get predictions
        total = 0
        preds = map(float, open(pred_file).read().splitlines())
        for hyp in data:
            hyp.pred = preds[total] #util.logit(preds[total])
            total += 1

        ## clean up
        os.remove(test_file)
        os.remove(pred_file)
        sys.stderr.write('done!\n')

        return data

    def results(self, data):
        for hyp in data:
            print hyp.label, hyp.pred, hyp.original
    

def featurize(sent_file, tag_file):
    """
    root.data        sentences
    root.label       labels
    root.tagged      POS tags
    note: tagger splits 3,000 into: 3/CD ,/, 000/CD
    """

    data = []
    prev = None
    sents_fh = open(sent_file)
    tags_fh = open(tag_file)
    while True:
        (sent, tags) = (sents_fh.readline().strip(), tags_fh.readline().strip())
        if not (sent or tags): break

        ## create a new hyp
        hyp = Hyp()
        hyp.original = sent
        hyp.label = None
        
        hyp.features = get_features(sent, tags)
        data.append(hyp)

        #print hyp.label, sent
        #print hyp.features
        #print '-------'
        
    return data

def load_model(path):
    model = SVM_Model(path)
    model.load()
    return model

if __name__ == '__main__':

    path = '../bourbon/nyt/svm/'
    sent_file = sys.argv[1]
    tag_file = sys.argv[2]

    model = load_model(path)
    data = featurize(sent_file, tag_file)
    data = model.classify(data)
    
    model.results(data)
