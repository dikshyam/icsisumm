import os, sys, re
import util, prob_util, berkeleyparser, sentence_compression, treenode, ilp, concept_mapper
from globals import *    
import nltk

class TextProcessor:
    
    def __init__(self):
        self._no_punct_pattern = re.compile('[a-zA-Z0-9- ]')
        self._stopwords = set(open(STOPWORDS).read().splitlines())
        self._porter_stemmer = nltk.stem.porter.PorterStemmer()
        self._sent_tokenizer = util.load_pickle('%s%s' %(STATIC_DATA_ROOT, 'punkt/english.pickle'))
        self._sent_split_ABBR_LIST = set(['Mr.', 'Mrs.', 'Sen.', 'No.', 'Dr.'])
        self._sent_split_PUNCT_LIST = set(['\" ', '\")', ') ', '\' ', '\"\''])

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
    
    def tokenize(self, text):
        return nltk.tokenize.punkt_word_tokenize(text)

    def porter_stem(self, word):
        return self._porter_stemmer.stem(word)
    
    def remove_stopwords(self, words):
        return [w for w in words if not w in self._stopwords]

    def is_just_stopwords(self, words):
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
        self.original = text
        self.parsed = None
        #self.length = len(re.split(r'[^A-Za-z0-9]+', text))
        self.length = len(text.strip().split())
        self.order = order
        self.date = date
        self.source = source
        self.tokens = text_processor.tokenize(text_processor.remove_punct(self.original.lower()))
        self.stemmed = map(text_processor.porter_stem, self.tokens)
        self.no_stop = map(text_processor.porter_stem, text_processor.remove_stopwords(self.tokens))
        
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
        w1 = set(self.no_stop)
        w2 = set(s.no_stop)
        return 1.0 * len(w1.intersection(w2)) / max(len(w1), len(w2))

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

    def _parse_newswire(self, path):
        data = open(path).read()
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
        fixed = re.sub('^(.{0,35} )?\(\w{2,10}?\) (--?|_) ?', '', fixed)
        fixed = re.sub('^([A-Z]{2,}.{0,30}? (--?|_) ){,2}', '', fixed)
        
        ## replace underscore, dash, double-dash with comma
        fixed = fixed.replace(' _ ', ', ')
        fixed = fixed.replace(' - ', ', ')
        fixed = fixed.replace(' -- ', ', ')
        
        ## other fixes
        fixed = re.sub('^(_|--?)', '', fixed)
        fixed = re.sub(' ?&AMP; ?', '&', fixed)
        fixed = re.sub(' ?&\w{2}; ?', ' ', fixed)
        fixed = fixed.replace(' ,', ',')
        fixed = re.sub('^, ', '', fixed)
        fixed = re.sub('\s+', ' ', fixed)
        fixed = fixed.strip()

        if util.is_punct(fixed): fixed = ''        
        return fixed
    
    def get_sentences(self):
        self.sentences = []
        order = 0
        for par in self.paragraphs:
            sents_text = text_processor.split_sents(par)
            for sent_text in sents_text:
                sentence = Sentence(sent_text, order, self.source, self.date)
                self.sentences.append(sentence)
                order += 1
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
        try: rawdata = open(path).read()
        except:
            sys.stderr.write('ERROR: could not read: %s\n' %path)
            return
        try: self.id = util.remove_tags(re.findall('<DOCNO>[^>]+</DOCNO>', rawdata[:100])[0])
        except:
            #<DOC id="AFP_ENG_20050125.0151" type="story" >
            match = re.search('<DOC id=\"([^"]+)\"', rawdata[:100])
            if match:
                self.id = str(match.groups(1))
            else:
                sys.stderr.write('ERROR: no <DOCNO>/<DOC id=...> tag: %s\n' %path)
                print rawdata[:100]

        ## source and date from id (assumes newswire style)
        if self.id != 'NONE':
            self.source = re.findall('^[^_\d]*', self.id)[0]
            self.date = self.id.replace(self.source, '')

        ## parse various types of newswire xml
        if is_clean:        text = self._parse_clean(path)
        else: text = self._parse_newswire(path)

        if len(text)==0:
            sys.stderr.write('WARNING: no text read for: %s\n' %path)
            return

        self.paragraphs = []
        for paragraph in text:
            fixed_par = self._fix_newswire(paragraph)
            if fixed_par == '': continue
            self.paragraphs.append(fixed_par)
        
        self._isempty = False
    
    def __str__(self):
        s = []
        s.append('%s DOCUMENT' %FORMAT_START)
        s.append('ID %s' %self.id)
        s.append('SOURCE %s' %self.source)
        s.append('DATE %s' %self.date)
        s.append('TEXT')
        s.extend(self.paragraphs)
        return '\n'.join(s)
    
