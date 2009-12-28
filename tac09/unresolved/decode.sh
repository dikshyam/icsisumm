mkdir -p tac09_v4
#for i in /u/dgillick/workspace/summ/bourbon/tac08_v4/*.sent.tok.parsed; do echo $i; cat $i | python2.6 ./unresolved_score.py icsiboost 0.449557 > tac08_v4/`basename $i .parsed`.unresolved; done
for i in /u/dgillick/workspace/summ/bourbon/tac09_v4/*.sent.tok.parsed; do echo $i; cat $i | python2.6 ./unresolved_score.py icsiboost 0.449557 > tac09_v4/`basename $i .parsed`.unresolved; done
