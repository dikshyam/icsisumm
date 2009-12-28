import os, sys, re, tempfile

def get_topic_ids(path):
    ids = map(str.strip, os.popen('ls %s*.doc' %path).readlines())
    ids = [f.split('.')[0] for f in map(os.path.basename, ids)]
    return ids

def tokenize(path, input_ext, output_ext):
    split_script = '~/tools/tokenize.sed'
    files = [f.strip() for f in os.popen('ls %s/*%s' %(path, input_ext)).readlines()]
    for file in files:
        output = file.replace(input_ext, output_ext)
        os.popen('sed -f %s %s > %s' %(split_script, file, output))

def run_parallel(path, tool, new_ext, jobs=20):
    ext = '.tok'
    inputs = map(str.strip, os.popen('ls %s/*%s' %(path, ext)).readlines())
    outputs = ['%s%s' %(f, new_ext) for f in inputs]

    rc_fh = open('rc', 'w')
    for input, output in zip(inputs, outputs):
        cmd = '%s <%s >%s' %(tool, input, output)
        rc_fh.write(cmd + '\n')
    rc_fh.close()
    cmd = 'run-command -attr x86_64 -J %d -f rc' %jobs
    os.popen(cmd)
    os.popen('rm -f rc')

import firstsent
def first_sent(path, new_ext='.firstsent'):
    """
    apply first sentence classifier
    """    
    
    ids = get_topic_ids(path)
    model = firstsent.load_model('../bourbon/nyt/svm/')
    for id in ids:
        sent_file = path + id + '.sent.tok'
        tag_file = path + id + '.sent.tok.tagged'
        data = firstsent.featurize(sent_file, tag_file)
        data = model.classify(data)
        
        fs_fh = open(path + id + new_ext, 'w')
        for sent in data:
            fs_fh.write('%1.4f\n' %sent.pred)
        fs_fh.close()

if __name__ == '__main__':

    ## general stuff
    parser_tool = '/u/dgillick/tools/parser_bin/berkeleyParser+Postagger.sh'
    tagger_tool = '/u/dgillick/tools/parser_bin/postagger-1.0/run_tagger.sh'

    ## where the data is
    path = '/u/dgillick/workspace/summ/bourbon/tac08_v4/'
    #path = '/u/dgillick/workspace/summ/bourbon/duc07_v3/'
    #path = '/u/dgillick/workspace/summ/bourbon/duc06m_v2/'
    #path = '/u/dgillick/workspace/summ/bourbon/tac09_v3/'

    ## run stuff
    jobs = 20
    print 'tokenizing...'
    tokenize(path, '.sent', '.sent.tok')
    tokenize(path, '.gold_sent', '.gold_sent.tok')
    tokenize(path, '.query', '.query.tok')
    print 'tagging...'
    run_parallel(path, tagger_tool, '.tagged', jobs)
    print 'parsing...'
    run_parallel(path, parser_tool, '.parsed', jobs)
    print 'first sentence classifier...'
    first_sent(path)
    print 'done'
