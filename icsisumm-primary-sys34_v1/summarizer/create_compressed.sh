#!/bin/bash

if [ $# != 2 ]
then
    echo "USAGE: $0 <input> <output>" >&2
    exit 1
fi

INPUT=$1
OUTPUT=$2
DIR=`dirname $0`

mkdir -p $OUTPUT
for i in $INPUT/*.srl+scores; do echo $i; python2 $DIR/compression.py $i $OUTPUT/`basename $i .srl+scores`.compressed $OUTPUT/`basename $i .srl+scores`.groups;done
for i in $OUTPUT/*.compressed; do echo "$DIR/../constituency/berkeleyParser.sh $i > $i.parsed"; done > $$.parse.run-command
#run-command -attr 2048meg -J 40 -f parse.run-command
sh $$.parse.run-command
for i in $OUTPUT/*.compressed.parsed; do echo $i; cat $i|python2 $DIR/../unresolved/unresolved_score.py $DIR/../unresolved/icsiboost 0.449557 > `echo $i|sed s'/.parsed$/.unresolved/'`; done
rm $$.parse.run-command
