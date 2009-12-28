#!/bin/bash

if [ $# != 2 ]
then
    echo "USAGE: $0 <input> <output>" >&2
    exit 1
fi

INPUT=$1
OUTPUT=$2
PRED=~favre/work/ontonotes/srl/guess_predicate_2009-05-26/
BERND=~favre/work/ontonotes/bernds_system/srl/
TAGGER=~favre/gale/sbd/systems/pos/PoST_v0.4/perl_scripts/tagging.pl
JAVA=/usr/local/lang/jdk1.6.0-64bit/bin/java
JAR=$BERND/lib/mate-090616.jar
DIR=`dirname $0`

if [ ! -f "$INPUT" ]
then
    echo "ERROR: input '$INPUT' not found" >&2
    exit 1
fi

$DIR/text_to_conll09_words.pl $INPUT > $OUTPUT.words
$JAVA -Xmx3G -cp $BERND/lib/mate-090710.jar is2.lemmatizer.Main -test $OUTPUT.words -out $OUTPUT.lemmas -model $BERND/models/lemma.model
$JAVA -Xmx3G -cp $BERND/lib/mate-090710.jar is2.tag.Main -test $OUTPUT.lemmas -out $OUTPUT.tagged -model $BERND/models/tag-conll.model
#python2.6 ~favre/work/ontonotes/srl/lemma/lemmatize.py ~favre/work/ontonotes/srl/lemma/lemma.CoNLL2009-ST-English.model < $OUTPUT.tagged > $OUTPUT.lemmas
$JAVA -Xmx3G -cp $BERND/lib/mate-090710.jar is2.sp09k1.Parser -test $OUTPUT.tagged -out $OUTPUT.parsed -model $BERND/models/eng-090703k1.model
#python2.6 ~favre/work/ontonotes/srl/predicate/predicate.py ~favre/work/ontonotes/srl/predicate/predicate.CoNLL2009-ST-English.model < $OUTPUT.parsed > $OUTPUT.predicates
#python2.6 ~favre/work/ontonotes/srl/predicate/all_predicate.py < $OUTPUT.parsed > $OUTPUT.predicates
awk '/./{if(NF<14){$13="_";$14="_"}}{print}' < $OUTPUT.parsed | $PRED/add_predicate_conll.py --model $PRED/conll_english > $OUTPUT.predicates
awk '/./{if(NF<14){$13="_";$14="_"}}{print}' < $OUTPUT.parsed | $PRED/add_predicate_conll_scores.py --model $PRED/conll_english > $OUTPUT.predicates+scores
#python2.5 $PRED/simple_predicate_finder.py < $OUTPUT.parsed > $OUTPUT.predicates
$JAVA -Xmx3G -cp $JAR is2.sp09i.AI -test $OUTPUT.predicates -out $OUTPUT.arguments -model $BERND/models/ai.CoNLL2009-ST-English.model -nopred
$JAVA -Xmx3G -cp $JAR is2.sp09i.SRL -test $OUTPUT.arguments -out $OUTPUT.srl_nosense -model $BERND/models/srl.CoNLL2009-ST-English.model -nopred
$JAVA -Xmx3G -cp $BERND/lib/mate-090629.jar is2.sp09m.SRL -test $OUTPUT.arguments -out $OUTPUT.arguments+scores -model $BERND/models/srl.CoNLL2009-ST-English.model -nopred
cut -f 13 $OUTPUT.predicates+scores | paste - $OUTPUT.arguments+scores | awk 'BEGIN{OFS="\t"}/./{$14=$1}{print}'|cut -f 2- > $OUTPUT.srl+scores
$JAVA -Xmx3G -cp $JAR is2.sp09i.WSD -test $OUTPUT.srl_nosense -out $OUTPUT.srl -model $BERND/models/wsd.CoNLL2009-ST-English.model -nopred
#python2.6-64bit ~/work/ontonotes/srl/mira-srl.py ~/work/ontonotes/srl/mira.argument_2009-05-26_noauto.model < $OUTPUT.predicates > $OUTPUT.srl_nosense
#awk 'BEGIN{OFS="\t"}/../{if($14!="_"){$14=$14 ".01"}}{print}' < $OUTPUT.srl_nosense > $OUTPUT
