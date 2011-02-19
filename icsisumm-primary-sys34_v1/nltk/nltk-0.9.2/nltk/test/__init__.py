# Natural Language Toolkit: Unit Tests
#
# Copyright (C) 2001-2008 University of Pennsylvania
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
# URL: <http://nltk.sf.net>
# For license information, see LICENSE.TXT
#
# $Id: __init__.py 5609 2007-12-31 03:02:41Z stevenbird $

"""
Unit tests for the NLTK modules.  These tests are intented to ensure
that changes that we make to NLTK's code don't accidentally introduce
bugs.

Each module in this package tests a specific aspect of NLTK.  Modules
are typically named for the module or class that they test (e.g.,
L{nltk.test.tree} performs tests on the L{nltk.tree}
module).

Use doctest_driver.py to run the tests:

  doctest_driver.py --help

NB. Popular options for NLTK documentation are:

  --ellipsis --normalize_whitespace

"""
