"""
    Summ-Thing: A basic (multi-document) summarization package for computing
      (1) ROUGE-based oracle summaries
      (2) high ROUGE-scoring summaries based on frequency statistics
      
    Copyright (C)2008 Dan Gillick

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys, os, os.path, tempfile, re, collections

def create_config(model_dir, peer_dir):
    models = filter(lambda x: x not in ('.', '..'), os.listdir(model_dir))
    peers = filter(lambda x: x not in ('.', '..'), os.listdir(peer_dir))
    unused, config_file = tempfile.mkstemp()
    config = open(config_file, 'w')
    config.write('<ROUGE_EVAL version=\"1.5.5\">\n')
    for peer in peers:
        topic = peer.upper()
        topic_models = filter(lambda x: x.upper().startswith(topic), models)
        for skipped_model in topic_models:
            config.write('<EVAL ID=\"%s\">\n' %skipped_model)
            config.write('<PEER-ROOT>\n')
            config.write(peer_dir + '/\n')
            config.write('</PEER-ROOT>\n')
            config.write('<MODEL-ROOT>\n')
            config.write(model_dir + '/\n')
            config.write('</MODEL-ROOT>\n')
            config.write('<INPUT-FORMAT TYPE=\"SPL\">\n')
            config.write('</INPUT-FORMAT>\n')
            config.write('<PEERS>\n')
            config.write('<P ID=\"1\">%s</P>\n' %peer)
            config.write('</PEERS>\n')
            config.write('<MODELS>\n')
            for model in topic_models:
                if model == skipped_model: continue
                config.write('<M ID=\"%s\">%s</M>\n' %(model[-1], model))
            config.write('</MODELS>\n')
            config.write('</EVAL>\n')
    config.write('</ROUGE_EVAL>\n')
    config.close()
    return config_file

def run_rouge(executable, config_file, length, verbose=False):
    rouge_data = os.path.dirname(executable) + '/data/'
    command = '%s -e %s -l %d -n 4 -x -m -2 4 -u -c 95 -r 1000 -f A -p 0.5 -t 0 -d %s 1' %(executable, rouge_data, length, config_file)
    scores = collections.defaultdict(dict)
    metrics = set()
    topics = set()
    for line in os.popen(command).readlines():
        if 'Eval' in line:
            [peer, metric, junk, topic_file, R, P, F] = line.split()
            topic = topic_file.split('.')[0]
            recall = float(R.split(':')[1])
            precision = float(P.split(':')[1])
            fm = float(F.split(':')[1])
            scores[metric][topic] = recall  # use recall
            metrics.add(metric)
            topics.add(topic)
            
        ## report averages
        if re.search(r'[1234] Average_R', line):
            sys.stdout.write(line)

    ## report all
    topics, metrics = list(topics), list(metrics)
    topics.sort()
    metrics.sort()
    print '\n         %s' %' '.join(['%s ' %m for m in metrics])
    if verbose:
        for topic in topics:
            print '%s  %s' %(topic, ' '.join(['%1.4f  ' %(scores[metric][topic]) for metric in metrics]))

    ## mean scores
    means = {}
    for metric in metrics:
        vals = scores[metric].values()
        means[metric] = sum(vals) / len(vals)
    print '\nAVG      %s' %' '.join(['%1.4f  ' %means[metric] for metric in metrics])


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.stderr.write('USAGE: %s <path_to_rouge_script> <model_dir> <peer_dir>\n' %sys.argv[0])
        sys.exit(1)
    config_file = create_config(sys.argv[2], sys.argv[3])
    run_rouge(sys.argv[1], config_file)
    os.remove(config_file)
