Run the eval:
```
python2.5 ../icsisumm/src/main.py -t u08 -d data/ --output out-u08-compress/ --compress
python2.5 ../icsisumm/src/main.py -t u08 -d data/ --output out-u08/
```
Note that if you reload without compression, the parser will not be run!

Test sentence compression:
```
cd /n/scotch/xc/drspeech/GALE/favre/summarization/systems/icsi_tac08/runs/
~favre/random_sequence.pl -r -i m07.parsed | python2.5 ../icsisumm/src/compression.py | more
```

A nice utility to highlight things instead of grepping:
```
cat whatever | /u/favre/install/bin/highlight [regexp] | more
```