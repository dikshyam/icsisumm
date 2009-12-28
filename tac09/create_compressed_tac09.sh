mkdir -p tac09_compressed_v4
for i in ~/work/ontonotes/bernds_system/srl/tac09_v4/*.srl+scores; do echo $i; python2.6 compression.py $i tac09_compressed_v4/`basename $i .srl+scores`.compressed tac09_compressed_v4/`basename $i .srl+scores`.groups;done
for i in tac09_compressed_v4/*.compressed; do echo "~/install/bin/berkeleyParser.sh $i > $i.parsed"; done > parse.run-command
run-command -attr 2048meg -J 40 -f parse.run-command
for i in tac09_compressed_v4/*.parsed; do echo $i; cat $i|python2.6 ../unresolved/unresolved_score.py ../unresolved/icsiboost 0.449557 > `echo $i|sed s'/.parsed$/.unresolved/'`; done
