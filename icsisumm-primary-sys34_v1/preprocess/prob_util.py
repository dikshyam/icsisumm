from __future__ import division
import math, random

LOGPROBMIN = -9999.9

class Counter(dict):

   def __getitem__(self, entry):
       try:
           return dict.__getitem__(self, entry)
       except KeyError:
           return 0.0

   def copy(self):
       return Counter(dict.copy(self))

   def makeProbDist(self):
       """
       Normalize the counts to return a ProbDist object.
       """
       total = sum(self.values())
       return ProbDist(dict([(entry, self[entry]/total) for entry in self]))

   def __add__(self, counter):
       """
       Add two counters together in obvious manner.
       """
       newCounter = Counter()
       for entry in set(self).union(counter):
           newCounter[entry] = self[entry] + counter[entry]
       return newCounter

   def sortedKeys(self):
       """
       returns a list of keys sorted by their values
       keys with the highest values will appear first
       """
       sortedItems = self.items()
       compare = lambda x,y: sign(y[1] - x[1])
       sortedItems.sort(cmp=compare)
       return [x[0] for x in sortedItems]

   def totalCount(self):
       """
       returns the sum of counts for all keys
       """
       return sum(self.values())

   def incrementAll(self, value=1):
       """
       increment all counts by value
       helpful for removing 0 probs
       """
       for key in self.keys():
           self[key] += value

   def display(self):
       """
       a nicer display than the built-in dict.__repr__
       """
       for key, value in self.items():
           s = str(key) + ': ' + str(value)
           print s

   def displaySorted(self, N=10):
       """
       display sorted by decreasing value
       """
       sortedKeys = self.sortedKeys()
       for key in sortedKeys[:N]:
           s = str(key) + ': ' + str(self[key])
           print s

class ProbDist(dict):
   """
   A distribution over finitely many entries.  Can be 'logified' to hold
   logarithms of probabilities. Any unseen entry has zero probability.
   """
   def __init__(self, *arg, **kwargs):
       self.logified = False
       if 'logified' in kwargs:
           self.logified = kwargs['logified']
           kwargs.pop('logified')
       dict.__init__(self, *arg, **kwargs)

   def __getitem__(self, entry):
       try:
           return dict.__getitem__(self, entry)
       except KeyError:
           if self.logified:
               return LOGPROBMIN # a pretty small log-prob
           else:
               return 0.0 # a very small prob

   def sample(self):
       """
       Sample a value from a U(0,1) distribution, and use this to generate
       a random sample from this particular distribution.
       """
       cumulative, uniform_sample = 0.0, random.random()
       probDist = self.delogify()
       for entry, prob in probDist.items():
           cumulative += prob
           if cumulative >= uniform_sample:
               return entry
       # Uh-oh: probabilities sum to < 1, so pick uniformly at random
       return self.keys()[random.randrange(len(self))]

   def copy(self):
       """
       Hopefully, this is not bugged...
       """
       return ProbDist(dict.copy(self), logified=self.logified)

   def logify(self):
       """
       Convert probabilities to the logarithmic domain
       """
       if not self.logified:
           entries = self.copy()  # a shallow copy
           for entry, value in entries.items():
               if value == 0.0:
                   entries[entry] = LOGPROBMIN
               else:
                   entries[entry] = math.log(value)
           return ProbDist(entries, logified=True)
       else:
           return self.copy()

   def delogify(self):
       """
       Convert to the non-logarithmic domain
       """
       if self.logified:
           entries = self.copy()
           for entry, value in entries.items():
               entries[entry] = math.exp(value)
           return ProbDist(entries, logified=False)
       else:
           return self.copy()

   def hasZeroProb(self, entry):
       if self.logified:
           return self[entry] == LOGPROBMIN
       else:
           return self[entry] == 0.0

   def hasNonZeroProb(self):
       for entry in self:
           if not self.hasZeroProb(entry):
               return True
       return False

class CondCounter(dict):
   """
   A dict of Counters.  Can be normalized to create a CondProbDist
   """
   def __init__(self, *arg, **kwargs):
       dict.__init__(self, *arg, **kwargs)
       for entry in self:
           self[entry] = Counter(self[entry])

   def __getitem__(self, entry):
       try:
           return dict.__getitem__(self, entry)
       except KeyError:
           self[entry] = Counter()
           return self[entry]

   def copy(self):
       """
       Hopefully, this is not bugged...
       """
       entries = dict.copy(self)
       for entry, counter in entries.items():
           entries[entry] = counter.copy()
       return CondCounter(entries)

   def makeCondProbDist(self):
       """
       For each entry, normalize the counts to return a ProbDist object.
       """
       return CondProbDist(dict([(entry, self[entry].makeProbDist()) for entry in self]))

   def __add__(self, condCounter):
       """
       Add two CondCounters together in obvious manner.
       """
       newCondCounter = CondCounter()
       for entry in set(self).union(condCounter):
           newCondCounter[entry] = self[entry] + condCounter[entry]
       return newCondCounter



class CondProbDist(dict):
   """
   A dict of ProbDists.  Can be 'logified' for log-domain probabilities.
   """
   def __init__(self,  *arg, **kwargs):
       self.logified = False
       if 'logified' in kwargs:
           self.logified = kwargs['logified']
           kwargs.pop('logified')
       dict.__init__(self, *arg, **kwargs)
       for entry, value in self.items():
           # There's got to be a better way to write this line:
           if str(type(value)) == "<class 'util.ProbDist'>":
               if self.logified:
                   self[entry] = value.logify()
               else:
                   self[entry] = value.delogify()
           else:
               # Assume entries are in correct logified state
               self[entry] = ProbDist(value, logified=self.logified)

   def __getitem__(self, entry):
       try:
           return dict.__getitem__(self, entry)
       except KeyError:
           self[entry] = ProbDist(logified=self.logified)
           return self[entry]

   def copy(self):
       """
       Hopefully, this is not bugged...
       """
       entries = dict.copy(self)
       for entry, probDist in entries.items():
           entries[entry] = probDist.copy()
       return CondProbDist(entries, logified=self.logified)

   def logify(self):
       entries = dict.copy(self)
       for entry, probDist in entries.items():
           entries[entry] = probDist.logify()
       return CondProbDist(entries, logified=True)

   def delogify(self):
       entries = dict.copy(self)
       for entry, probDist in entries.items():
           entries[entry] = probDist.delogify()
       return CondProbDist(entries, logified=False)

def normalize(counter):
   """
   normalize a counter by dividing each value by the sum of all values
   """
   counter = Counter(counter)
   normalizedCounter = Counter()
   total = float(counter.totalCount())
   for key in counter.keys():
       value = counter[key]
       normalizedCounter[key] = value / total
   return normalizedCounter

def multiplyAll(counter, m):
   """
   multiply each element of a counter by m and return a new counter
   """
   m = float(m)
   #if m == 0.0: return counter
   newCounter = Counter(counter)
   for key in counter.keys():
       newCounter[key] = counter[key] * m
   return newCounter

def maxes(counter):
   """
   returns the max and a list of equivalent argmaxes
   """
   max, argmaxes = None, []
   for key in counter.keys():
       c = counter[key]
       if max == None or c > max:
           max = c
   for key in counter.keys():
       c = counter[key]
       if c == max:
           argmaxes.append(key)
   return max, argmaxes

def mins(counter):
   """
   returns the max and a list of equivalent argmaxes
   """
   min, argmins = None, []
   for key in counter.keys():
       c = counter[key]
       if min == None or c < min:
           min = c
   for key in counter.keys():
       c = counter[key]
       if c == min:
           argmins.append(key)
   return min, argmins

def entropy(probDist):
   """
   calculate the entropy of a distribution
   """
   M = 0.0000000000001
   if probDist.logified: probDist = probDist.delogify()
   entropy = 0
   for key, value in probDist.items():
       if value == 0: value = M
       entropy += (value * math.log(value,2))
   return entropy

def klDivergence(probDist1, probDist2):
   """
   calculate the KL distance between two distributions
   """
   M = 0.0000000000001

   if probDist1.logified: probDist1 = probDist1.delogify()
   if probDist1.logified: probDist1 = probDist1.delogify()

   kl = 0
   for key, value in probDist1.items():
       try: q = value / probDist2[key]
       except: q = value / M
       if q == 0: q = M
       kl += value * math.log(q, 2)

   return kl

def klDistance(probDist1, probDist2):
   return klDivergence(probDist1, probDist2) + klDivergence(probDist2, probDist1)

def euclidianDistance(f1, f2):
   """
   return euclidian distance between two dictionaries
   """
   if set(f1.keys()) != set(f2.keys()):
       pass
       #raise 'non-matching keys', set(f1.keys()).symmetric_difference(set(f2.keys()))

   s = 0.0
   for key, val1 in f1.items():
       val2 = f2[key]
       val1, val2 = float(val1), float(val2)
       s += ((val1 - val2) ** 2)
   return math.sqrt(s)

def flatten(counter):
   """
   takes a dictionary of dictionaries and flattens it into a new
   counter with keys of the form <key1.key2>
   """
   flatCounter = Counter()
   for key1 in counter.keys():
       for key2 in counter[key1].keys():
           newKey = key1 + '.' + key2
           flatCounter[newKey] = counter[key1][key2]
   return flatCounter

def sign(x):
   """
   returns 1 or -1 depending on the sign of x
   """
   if x >= 0: return 1
   else: return -1
