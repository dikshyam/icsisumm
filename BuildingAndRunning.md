# Introduction #

If you need a technical overview of what the system actually does, please check the [TAC'09 system description paper](http://icsisumm.googlecode.com/svn/trunk/icsisumm-primary-sys34_v1/papers/favre_tac2009.pdf).

Here are the steps you'll have to go through to run the system:
  1. Check basic requirements
  1. Grab the source code
  1. Download and setup the data from NIST
  1. Download and setup ROUGE-1.5.5
  1. Rebuild GLPK
  1. Run the system
  1. Get the output

# Requirements #

You need a 2 series python, at least 2.6 (it does not work with python 3).

You also need subversion and usual build tools (build-essential in ubuntu).

For performing ROUGE scoring, you need the XML::DOM perl extension.

The system has been shown to work on linux. It should be possible to get it to work on MacOSX and Windows (under Cygwin).

# Grabbing the code #

```
svn checkout http://icsisumm.googlecode.com/svn/tags/tac09-sys34 icsisumm
cd icsisumm/icsisumm-primary-sys34_v1
```

# Setup TAC'09 data #

If you don't already have the TAC data, see http://www.nist.gov/tac/data/index.html for more info on how to get it from NIST.

Put the files in the `data` subdirectory in a directory named after the year of the evaluation (09).

The resulting layout should be as listed in data/09.files.gz.

# Setup the ROUGE evaluation toolkit #

Go in the `scoring` subdirectory.

Rebuild those dependences (archives are provided):
  * libxml can be downloaded at http://xmlsoft.org/
  * XML::Parser http://search.cpan.org/dist/XML-Parser/

```
tar zxf libxml-enno-1.02.tar.gz 
cd libxml-enno-1.02
perl Makefile.PL 
cd ..
tar zxf XML-Parser-2.36.tar.gz 
cd XML-Parser-2.36
perl Makefile.PL 
cd ..
```

Get ROUGE 1.5.5 at http://berouge.com/contactus.aspx, then extract and patch it:

```
tar xf ROUGE-1.5.5.tar.gz
cd RELEASE-1.5.5
patch -p1 < ../ROUGE-1.5.5.patch
chmod +x ROUGE-1.5.5_faster.pl
cd ..
mv RELEASE-1.5.5 ROUGE-1.5.5
```

The patch adds caching of scoring units for faster results.
Check that you get more or less the same files as listed in ROUGE-1.5.5.files.gz.

You can find a ROUGE tutorial here http://kavita-ganesan.com/rouge-howto

# Rebuild the ILP solver #

Go to the `solver` subdirectory.

The GNU Linear Programming Kit (GLPK) can be downloaded at http://www.gnu.org/software/glpk/.

```
tar xf glpk-4.43.tar.gz
cd glpk-4.43
./configure
make
cd ..
```

# Run the system #

Go in the main directory and run:

```
./run-icsi-primary-sys-34.sh
```

It performs the following operations:
  1. Run sentence segmentation on the original documents using [Splitta](http://code.google.com/p/splitta/)
  1. Tokenize sentences with the penn tokenizer
  1. Run the summarizer on resulting sentences

# Grab the output #

The output is located in ./output/u09/summary.