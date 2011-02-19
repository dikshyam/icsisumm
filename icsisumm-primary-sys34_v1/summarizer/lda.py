import os, sys, re
import util, prob_util

def fix_text(text):
    """
    prepare text for ngram concept extraction
    """
    t = text
    t = util.remove_punct(t)
    t = re.sub('\s+', ' ', t)
    return t.lower()

def prep_docs(path, out_path):
    files = os.popen('ls %s*.sent' %path).read().splitlines()

    ## on the first pass, create a vocab mapping
    vocab = set()
    for file in files:
        if '-B' in file: continue
        sents = open(file).read().splitlines()
        doc = prob_util.Counter()

        for sent in sents[:20]:
            s = util.porter_stem_sent(util.tokenize(fix_text(sent)))
            concepts = set(util.get_ngrams(s, 1, bounds=False, as_string=True))
            vocab.update(concepts)

    fh = open(out_path+'vocab', 'w')
    vocab = zip(vocab, range(len(vocab)))
    for concept, count in vocab:
        fh.write('%s %d\n' %(concept, count))
    fh.close()
    vocab = dict(vocab)

    ## on the second pass, output one doc per line
    for file in files:
        if '-B' in file: continue
        sents = open(file).read().splitlines()
        doc = prob_util.Counter()

        for sent in sents[:20]:
            s = util.porter_stem_sent(util.tokenize(fix_text(sent)))
            concepts = set(util.get_ngrams(s, 1, bounds=False, as_string=True))
            for concept in concepts:
                doc[concept] += 1

        ## doc output
        output = '%d %s' %(len(doc), ' '.join(['%s:%d' %(vocab[t],c) for t,c in doc.items()]))
        print output


if __name__ == '__main__':

    data_path = '/u/dgillick/workspace/summ/bourbon/tac08_v2/'
    out_path = '/u/dgillick/workspace/summ/bourbon/lda/'

    prep_docs(data_path, out_path)
