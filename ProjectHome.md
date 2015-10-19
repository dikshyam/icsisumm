This summarization system, crafted for the [Text Analysis Conference](http://www.nist.gov/tac/) (TAC) evaluation campaign, generates summaries by extracting sentences that contain the most frequent word bigrams (called concepts) from the input documents. It uses Integer Linear Programming (ILP) for determining, under a length constraint that set of sentences. With this system, we obtained very good scores for the update task at the TAC'08 evals and among the best scores at TAC'09.

So far, we only released the raw code which contains a lot of dependencies to internal stuff at ICSI, but we plan to add a cleaned-up, standalone version for public use.

NEWS:
  * <font color='red'>2010-11-16 Added a download with a version of the TAC'09 system that you can run at home!!!</font>
  * 2010-10-13 The _mate_ dependency parser is now available for download
  * 2009-12-28 Added TAC'09 code

DEPENDENCIES:
  * [glpsol ](http://www.gnu.org/software/glpk/), ILP solver
  * [splitta](http://code.google.com/p/splitta), sentence splitter
  * [icsiboost](http://code.google.com/p/icsiboost), a classifier
  * [nltk](http://www.nltk.org), for tokenization and stemming
  * [Berkeley Parser](http://code.google.com/p/berkeleyparser), a constituency parser
  * [mate](http://code.google.com/p/mate-tools/), a dependency parser and SRL system

_Note that the SRL system is only needed if you want to use sentence compression in TAC'09._

REFERENCES:
  * Dan Gillick, Benoit Favre, Dilek Hakkani-Tür, Bernd Bohnet, Yang Liu, Shasha Xie, "[The ICSI/UTD Summarization System at TAC 2009](http://www-lium.univ-lemans.fr/~favre/papers/favre_tac2009.pdf)", in Text Analysis Conference, Gaithersburg, MD (USA) - 2009
  * Daniel Gillick, Benoit Favre, "[A Scalable Global Model for Summarization](http://www-lium.univ-lemans.fr/~favre/papers/favre_ilpnlp2009.pdf)", NAACL/HLT 2009 Workshop on Integer Linear Programming for Natural Language Processing - 2009
  * Dan Gillick, Benoit Favre, Dilek Hakkani-Tür, "[The ICSI Summarization System at TAC 2008](http://www-lium.univ-lemans.fr/~favre/papers/favre_tac2008.pdf)", Text Analysis Conference, Gaithersburg, MD (USA) - 2008