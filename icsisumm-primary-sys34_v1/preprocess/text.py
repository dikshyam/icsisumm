import os, sys, re, math
import util
from globals import *    
import nltk
import sbd

class TextProcessor:
    
    def __init__(self):
        self._no_punct_pattern = re.compile('[a-zA-Z0-9- ]')
        self._stopwords = set(open(STOPWORDS).read().splitlines())
        self._porter_stemmer = nltk.stem.porter.PorterStemmer()
        #self._sent_tokenizer = util.load_pickle('%s%s' %(STATIC_DATA_ROOT, 'punkt/m07_punkt.pickle'))
        self._sent_split_ABBR_LIST = set(['Mr.', 'Mrs.', 'Sen.', 'No.', 'Dr.', 'Gen.', 'St.', 'Lt.', 'Col.', 'Capt.'])
        self._sent_split_PUNCT_LIST = set(['\" ', '\")', ') ', '\' ', '\"\''])

    def load_splitta_model(self, path):
        use_svm = False
        if 'svm' in path.lower(): use_svm = True
        self._splitta_model = sbd.load_sbd_model(path, use_svm)

    def load_punkt_model(self, path):
        self._sent_tokenizer = util.load_pickle(path)

    def train_punkt_model(self, text, save_path=None):
        """
        unsupervised training given some text
        optional save_path for future use
        """
        
        ## train tokenizer
        sys.stderr.write('Training...\n')
        t = nltk.tokenize.punkt.PunktSentenceTokenizer()
        t.ABBREV = 0.1  # threshold for identifying abbrevs (lower is more aggressive)
        t.train(rawtext)  
        self._sent_tokenizer = t
        
        ## pickle it
        if save_path:
            util.save_pickle(t, save_path)
            sys.stderr.write('Saved model as [%s]\n' %output)

    def split_sents(self, text):
        sents = []
        psents = self._sent_tokenizer.tokenize(text)
                
        ## fix end of sentence punctuation errors
        for i in range(len(psents)-1, -1, -1):
            if psents[i][0:2] in self._sent_split_PUNCT_LIST:
                psents[i-1] += psents[i][0]
                psents[i] = psents[i][2:]
            elif psents[i] in ['"', ')', '\'']:
                psents[i-1] += psents[i][0]
                psents[i] = ''
            elif psents[i][0] in [',', ';', ':']:
                psents[i-1] += psents[i]
                psents[i] = ''
            elif i+1 < len(psents) and psents[i].split()[-1] in self._sent_split_ABBR_LIST:
                psents[i] += ' ' + psents[i+1]
                psents[i+1] = ''
            
        sents.extend([p for p in psents if len(p) > 1])
        return sents
    
    def splitta(self, text):
        return sbd.sbd_text(self._splitta_model, text, do_tok=False)
        
    def tokenize(self, text):
        return nltk.tokenize.punkt_word_tokenize(text)

    def porter_stem(self, word):
        return self._porter_stemmer.stem(word)
    
    def remove_stopwords(self, words):
        return [w for w in words if not w in self._stopwords]

    def is_just_stopwords(self, words):
        if type(words) == type(''): words = words.split()
        for word in words:
            if word not in self._stopwords:
                return False
        return True

    def remove_punct(self, sentence):
        return re.sub(r'[^a-zA-Z0-9- ]', '', sentence).strip()

text_processor = TextProcessor()

class Sentence:
    """
    class for holding information about a single sentence
    self.original     original text string
    self.parsed       s-exp representation of a parse tree
    """
    
    def __init__(self, text, order = 0, source = "?", date = "?"):
        self.order = order
        self.date = date
        self.source = source
        self.set_text(text)

    def set_text(self, text):
        self.original = text.strip()
        self.parsed = None
        self.length = len(self.original.split())
        self.tokens = text_processor.tokenize(text_processor.remove_punct(self.original.lower()))
        self.stemmed = map(text_processor.porter_stem, self.tokens)
        self.no_stop = map(text_processor.porter_stem, text_processor.remove_stopwords(self.tokens))
    
        self.no_stop_freq = {}
        for word in self.no_stop:
            if word not in self.no_stop_freq: self.no_stop_freq[word] = 1
            else: self.no_stop_freq[word] += 1
            
    def parse(self, parser=None):
        if self.parsed:
            return
        if parser:
            parser.add_job(self, self.original)
        else:
            #parser = CommandLineParser()
            self.parsed = parser.parse(self.original)

    def sim_basic(self, s):
        """
        basic word overlap similarity between two sentences
        """
        if type(s) != type(''):
            s = s.no_stop
        else:
            s = s.split()

        w1 = set(self.no_stop)
        w2 = set(s)
        return 1.0 * len(w1.intersection(w2)) / max(len(w1), len(w2))

    # compute norm for cosine similarity
    def compute_norm(self, words_idf = None):
        self.norm = 0
        for word in self.no_stop_freq:
            score = self.no_stop_freq[word]
            if words_idf != None and word in words_idf:
                score *= words_idf[word]
            self.norm += score * score
        self.norm = math.sqrt(self.norm)

    # simple cosine similarity with ignored
    def sim_cosine(self, s, words_idf = None):
        norm = self.norm * s.norm
        if math.fabs(norm) < 0.00001:
            return 0
        score = 0
        for word in self.no_stop_freq:
            if word in s.no_stop_freq:
                factor = self.no_stop_freq[word]
                if words_idf != None and word in words_idf:
                    factor *= words_idf[word] * words_idf[word]
                factor *= s.no_stop_freq[word]
                score += factor
        return score / norm

    def __str__(self):
        return self.original

def glue_quotes(sentences):
    starts = []
    ends = []
    id = 0
    offset = 0
    for sentence in sentences:
        for match in re.finditer(r'(^|\s)[\(]*"', sentence):
            starts.append((id, offset + match.end(), match.end()))
        for match in re.finditer(r'"[,.\'\)]*(\s|$)', sentence):
            ends.append((id, offset + match.start(), match.start()))
        for match in re.finditer(r'([^\(\s]"[^\s.,\'])', sentence):
            starts.append((id, offset + match.end(), match.end()))
            ends.append((id, offset + match.start(), match.start()))
        offset += len(sentence)
        id += 1
    gluelist = []
    bounds = {}
    for i in xrange(len(starts)):
        min = offset
        argmin = None
        for j in xrange(len(ends)):
            if ends[j] == None: continue
            dist = ends[j][1] - starts[i][1]
            if dist < 0: continue
            if dist < min or argmin == None:
                min = dist
                argmin = j
        if argmin != None:
            if argmin not in bounds:
                bounds[argmin] = (i, min)
            else:
                if bounds[argmin][1] > min:
                    bounds[argmin] = (i, min)
                
    for end, start in bounds.items():
        if starts[start[0]][0] != ends[end][0]:
            gluelist.append((starts[start[0]][0], ends[end][0]))
        starts[start[0]] = None
        ends[end] = None
    for start in starts:
        if start != None:
            sentence = sentences[start[0]][:start[2]] + "<start>" + sentences[start[0]][start[2]:]
            #print ('WARNING: unused quote [%s]\n' % sentence)
    for end in ends:
        if end != None:
            sentence = sentences[end[0]][:end[2]] + "<end>" + sentences[end[0]][end[2]:]
            #print ('WARNING: unused quote [%s]\n' % sentence)
    output = []
    for i in xrange(len(sentences)):
        glued = False
        for item in gluelist:
            if i > item[0] and i <= item[1]:
                output[-1] += " " + sentences[i]
                glued = True
                break
        if not glued:
            output.append(sentences[i])
    return output

def glue_pars(pars):
    glued = []
    for i in range(len(pars)-1):
        ## next par starts with lowercase and this par doesn't end with a period
        if par[i+1][0:2].islower() and not re.search('\.[")]?$', par[i]):
            glued.append(par[i] + par[i+1])
        else:
            glued.append(par[i])
    return glued

class Document:
    """
    Class for storing documents.
    doc = Document(<document_path>) will load the document and parse it
    for desired information.

    Public Member Variables:
    self.id             'XIE19980304.0061'
    self.source         'XIE'
    self.date           '19980304.0061'
    self.paragraphs     ['Par 1 text', 'Par 2 text', ... ]
    self.sentences      ['sent 1 text', 'sent 2 text', ... ]
    """

    def _parse_clean(self, path):
        return open(path).read().splitlines()

    def _parse_newswire(self, data):
        data = data.replace('``', '\"').replace('\'\'', '\"').replace('`', '\'')
        data = data.replace('\n', '\t')
        pattern = re.compile(r'<\/?(p|text|doc)>', re.I | re.M) # convert <p> and <text> to paragraph breaks
        data = re.sub(pattern, '\t', data)
        pattern = re.compile(r'<[^>]*>.*?<\/[^>]*>', re.M) # remove tagged content
        data = re.sub(pattern, '\t', data)
        pattern = re.compile(r'<[^>]*>', re.M) # remove remaining tags
        data = re.sub(pattern, ' ', data)
        pattern = re.compile(r'\s+', re.M)
        text = map(lambda x: re.sub(pattern, ' ', x.strip()), filter(lambda x: x != '', re.split(r' *\t *\t *', data)))
        return text

    def _fix_newswire(self, par):
        """
        clean up newswire paragraphs
        """        
        fixed = par
        
        ## get rid of leaders in newswire text        
        fixed = re.sub('^(.{0,35} )?\(\w{2,10}?\) ?(--?|_) ?', '', fixed)
        fixed = re.sub('^([A-Z]{2,}.{0,30}? (--?|_) ){,2}', '', fixed)
        
        ## replace underscore, dash, double-dash with comma
        fixed = fixed.replace(' _ ', ', ')
        fixed = fixed.replace(' - ', ', ')
        fixed = fixed.replace(' -- ', ', ')
        fixed = re.sub('([\w\d])--([\w\d])', '\\1, \\2', fixed)
        
        ## other fixes
        fixed = re.sub('^(_|--?)', '', fixed)
        fixed = re.sub(re.compile(r' ?&AMP; ?', re.I), '&', fixed)
        fixed = re.sub(' ?&\w{2}; ?', ' ', fixed)
        fixed = fixed.replace(' ,', ',')
        fixed = re.sub('^, ', '', fixed)
        fixed = re.sub('\s+', ' ', fixed)
        fixed = re.sub('(\w)\.("?[A-Z])', '\\1. \\2', fixed)
        fixed = fixed.strip()

        if util.is_punct(fixed): fixed = ''        
        return fixed
    
    def get_sentences(self):
        self.sentences = []
        order = 0
        for par in self.paragraphs:
            #sents_text = text_processor.split_sents(par)
            sents_text = text_processor.splitta(par)
            sents_text_glued = glue_quotes(sents_text)
            par_sent_count = 0
            for sent_text in sents_text_glued:
                #print order, sent_text
                if order == 0 and re.search('By [A-Z]', sent_text): continue
                if order == 0 and sent_text.startswith('('): continue
                if order == 0 and re.search('c\.\d', sent_text): continue
                if order == 0 and sent_text.startswith('"') and sent_text.endswith('"'): continue
                if sent_text.isupper(): continue
                if 1.0*len([1 for c in sent_text if c.isupper()]) / len(sent_text) > 0.2: continue
                if len(sent_text.split()) < 20 and not re.search('\.[")]?$', sent_text): continue
                if re.search(re.compile('eds:', re.I), sent_text): continue
                if re.search('[ \-]\d\d\d-\d\d\d\d', sent_text): continue
                if '(k)' in sent_text: continue
                sentence = Sentence(sent_text, order, self.source, self.date)
                if par_sent_count == 0: sentence.paragraph_starter = True
                else: sentence.paragraph_starter = False
                self.sentences.append(sentence)
                order += 1
                par_sent_count += 1
        print self.id, len(self.sentences)

    def parse_sentences(self, parser=None):
        if parser:
            for sentence in self.sentences:
                sentence.parse(parser)
        else:
            #parser = CommandLineParser(BERKELEY_PARSER_CMD)
            for sentence in self.sentences:
                sentence.parse(parser)
            parser.run()
            for sentence in parser.parsed:
                sentence.parsed = parser.parsed[sentence]
            

    def __init__(self, path, is_clean=False):
        """
        path is the location of the file to process
        is_clean=True means that file has no XML or other markup: just text
        """
        self.id = 'NONE'
        self.date = 'NONE'
        self.source = 'NONE'
        self.paragraphs = []
        self._isempty = True

        ## get generic info
        if os.path.isfile(path): rawdata = open(path).read()
        elif path.strip().startswith('<DOC>'): rawdata = path
        else:
            sys.stderr.write('ERROR: could not read: %s\n' %path)
            return

        try: 
            self.id = util.remove_tags(re.findall('<DOCNO>[^>]+</DOCNO>', rawdata[:100])[0])
        except:
            match = re.search('<DOC id=\"([^"]+)\"', rawdata[:100])
            if match:
                self.id = str(match.groups(1)[0])
            else:
                sys.stderr.write('ERROR: no <DOCNO>/<DOC id=...> tag: %s\n' %path)

        ## source and date from id (assumes newswire style)
        if self.id != 'NONE':
            self.source = re.findall('^[^_\d]*', self.id)[0]
            self.date = self.id.replace(self.source, '')

        ## parse various types of newswire xml
        if is_clean: text = self._parse_clean(rawdata)
        else: text = self._parse_newswire(rawdata)

        if len(text)==0:
            #sys.stderr.write('WARNING: no text read for: %s\n' %path)
            return

        self.paragraphs = []
        for paragraph in text:
            fixed_par = self._fix_newswire(paragraph)
            if fixed_par == '': continue
            self.paragraphs.append(fixed_par)
        
        self._isempty = False
    
    def __str__(self):
        s = []
        s.append('%s DOCUMENT' %'#START')
        s.append('ID %s' %self.id)
        s.append('SOURCE %s' %self.source)
        s.append('DATE %s' %self.date)
        s.append('TEXT')
        s.extend(self.paragraphs)
        return '\n'.join(s)
    
