LEN=`cat icsiboost.all |wc -l`
REM=`expr $LEN - 2000`
head -$REM icsiboost.all > icsiboost.data
tail -2000 icsiboost.all | head -1000 > icsiboost.dev
tail -1000 icsiboost.all > icsiboost.test
icsiboost --optimal-iterations -n 1000 --max-fmeasure False -S icsiboost --posteriors

