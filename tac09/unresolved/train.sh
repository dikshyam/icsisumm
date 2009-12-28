run-command "find /u/drspeech/data/ontonotes_r2.9/data/english/annotations/nw/wsj -name '*.parse' | xargs python2.6 training_data.py > icsiboost.all; ./run.sh | tee icsiboost.iter"
