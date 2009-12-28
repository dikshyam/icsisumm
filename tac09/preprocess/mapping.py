"""
"""

import os, sys, re, math, util, ilp, text, treenode, prob_util
from operator import itemgetter  # for sorting dictionaries by value
from globals import *

class LocationMapper:
    
    def __init__(self, problem):
        self.problem = problem
        
    def setup(self):
        
        ## parameters
        min_sent_len = 5
        
        ## weight sentences
        sent_weights = {}
        all_sents = self.problem.get_new_sentences()
        for sent in all_sents:
            if sent.length < min_sent_len: continue
            if sent.original in sent_weights: continue
            sent_weights[sent] = 1.0 / (sent.order+1)
            print 1.0/(sent.order+1), sent
        
        