#!/bin/bash
DOCS=data/09/tac09_data/UpdateSumm09_test_docs_files/
REF=data/09/UpdateSumm09_eval/ROUGE/models/
OUTPUT=output/u09/
export PYTHONPATH=nltk/nltk-0.9.2:preprocess/splitta:$PYTHONPATH
export PATH=solver/glpk-4.43/examples/:$PATH
mkdir -p $OUTPUT

#python2 preprocess/main.py --output $OUTPUT --docpath $DOCS --manpath $REF --task u09 --reload --splitta-model preprocess/splitta/model_nb/

#for i in $OUTPUT/*.sent ; do preprocess/penn_treebank_tokenizer.sed $i > $i.tok;done

export HOSTNAME=localhost
python2 summarizer/inference.py -i $OUTPUT -o $OUTPUT -t u09 --manpath $REF --decoder nbest --nbest 2
rm -f tmp_decoder.*
