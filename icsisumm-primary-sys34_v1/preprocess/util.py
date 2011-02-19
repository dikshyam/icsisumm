import treenode
from globals import *
import re, cPickle, os, gzip

def save_pickle(data, path):
    o = gzip.open(path, 'wb')
    cPickle.dump(data, o)
    o.close()

def load_pickle(path):
    i = gzip.open(path, 'rb')
    data = cPickle.load(i)
    i.close()
    return data

def flushFile(fh):
   """
   flush file handle fh contents -- force write
   """
   fh.flush()
   os.fsync(fh.fileno())

def remove_tags(text):
    """
    remove html style tags from some text
    """
    cleaned = re.sub('<[^>]+>', '', text)
    return re.sub('\s+',' ', cleaned).strip()

def remove_punct(sent):
    """
    remove any character that is not in [a-z], [A-Z], [0-9], -, or a space
    also strips leading and trailing spaces
    """
    return re.sub(r'[^a-zA-Z0-9- ]', '', sent).strip()

def is_punct(text):
    """
    returns true if the text consists solely of non alpha-numeric characters
    """
    for letter in text.lower():
        if letter in set('abcdefghijklmnopqrstuvwxyz1234567890'): return False
    return True

def get_files(path, pattern):
    """
    Recursively find all files rooted in <path> that match the regexp <pattern>
    """
    L = []
    
    # base case: path is just a file
    if (re.match(pattern, os.path.basename(path)) != None) and os.path.isfile(path):
        L.append(path)
        return L

    # general case
    if not os.path.isdir(path):
        return L

    contents = os.listdir(path)
    for item in contents:
        item = path + item
        if (re.search(pattern, os.path.basename(item)) != None) and os.path.isfile(item):
            L.append(item)
        elif os.path.isdir(path):
            L.extend(get_files(item + '/', pattern))

    return L

def get_ngrams(sent, n=2, bounds=False):
    """
    Given a sentence (as a string or a list of words), return all ngrams
    of order n in a list of tuples [(w1, w2), (w2, w3), ... ]
    bounds=True includes <start> and <end> tags in the ngram list
    """

    ngrams = []

    if type(sent) == type(''): words = sent.split()
    elif type(sent) == type([]): words = sent
    else:
        sys.stderr.write('unrecognized input type [%s]\n' %type(sent))
        return ngrams

    if bounds:
        words = ['<start>'] + words + ['<end>']

    N = len(words)
    for i in range(n-1, N):
        ngram = words[i-n+1:i+1]
        ngrams.append(tuple(ngram))
    return ngrams

def get_skip_bigrams(sent, k=2, bounds=False):
    """
    get bigrams with up to k words in between
    otherwise similar to get_ngrams
    duplicates removed
    """

    sb = set()

    if type(sent) == type(''): words = sent.split()
    elif type(sent) == type([]): words = sent
    else:
        sys.stderr.write('unrecognized input type [%s]\n' %type(sent))
        return sb

    if bounds:
        words = ['<start>'] + words + ['<end>']

    N = len(words)
    width = min(k+2, N)
    for i in range(width, N+1):
        for j in range(i-width, i):
            for k in range(j+1, i):
                g = (words[j], words[k])
                sb.add(g)
    return list(sb)
