# changes:
# 2009-03-26 changed readAllTrees() to be an iterator instead of building a large list in memory
# 2009-03-24 added leaf_index, the word number

class TreeNode:
    # this class handles a parse tree in bracketted format "(S (NP (NNP Python)))"
    # this basic implementation assumes that the parse tree is well formed
    # v1.1 now uses an s-expression parser that reads multiline trees
    #      taken from http://nlp.cs.jhu.edu/~edrabek/utils/s_expr_gen.py
    #
    # available members for crawling the tree:
    # - root = the root of the tree
    # - parent = the parent of the node
    # - children = the children of the node
    # - nextSibling = the next child of this node's parent
    # - previousSibling = the next child of this node's parent
    # - leaves = the deepest children of that node
    # - nextLeaf = the first leaf of the next sibling
    # - previousLeaf = the last leaf of the previous sibling
    # - index = child number of node in parent
    # - leaf_index = word number (only on leaves)
    #
    # available members specific to parse trees:
    # - label = the node label (NP, VP, S, NNP, VB, JJ, ...)
    # - text = the text attached to the node, if it's a leaf
    def __init__(self, input, parent = None):
        self.parent = parent
        if parent != None:
            self.root = parent.root
        else:
            self.root = self
        if type(input) != type([]):
            input = self._read_all_iterator(input).next()
        self.text = None
        self.label = None
        self.index = 0
        self.children = []
        self.previousSibling = None
        self.nextSibling = None
        self.previousLeaf = None
        self.nextLeaf = None
        self.leaves = []
        for node in input:
            if type(node) == type([]):
                child = self.__class__(node, self)
                child.index = len(self.children)
                self.children.append(child)
                self.leaves.extend(child.leaves)
            elif self.label == None:
                self.label = node
            elif self.text == None:
                self.text = node
        if len(self.children) == 0:
            self.leaves.append(self)
        for index in range(len(self.children) - 1):
            self.children[index].nextSibling = self.children[index + 1]
            self.children[index + 1].previousSibling = self.children[index]
            self.children[index]._setNextLeaf(self.children[index + 1].leaves[0])
            self.children[index + 1]._setPreviousLeaf(self.children[index].leaves[-1])
        if self.text == None: self.text = ""
        if self.label == None: self.label = ""
        if not self.parent:
            for i in range(len(self.leaves)):
                self.leaves[i].leaf_index = i

    # read all trees in a file or a string (lightweight iterator version)
    @classmethod
    def readAllTrees(cls, input):
        for tree in cls._read_all_iterator(input):
            yield cls(tree)

    # internal use (tokenize an s-expression)
    @classmethod
    def _gen_tokens_iterator(cls, input):
        if type(input) == type(""):
                input = [input]
        for line in input:
            line_len = len(line)
            left = 0

            while left < line_len:
                c = line[left]

                if c.isspace():
                    left += 1
                elif c in '()':
                    yield c
                    left += 1

                else:
                    right = left + 1
                    while right < line_len:
                        c = line[right]
                        if c.isspace() or c in '()':
                            break

                        right += 1

                    token = line[left:right]
                    #if token.isdigit():
                    #    token = int(token)
                    yield token

                    left = right

    # internal use (get a list representation of an s-expression)
    @classmethod
    def _read_all_iterator(cls, input):
        stack = []
        for token in cls._gen_tokens_iterator(input):
            if token == '(':
                stack.append([])

            elif token == ')':
                top = stack.pop()
                if len(stack) == 0:
                    yield top
                else:
                    stack[-1].append(top)

            else:
                stack[-1].append(token)

        assert len(stack) == 0

    # print the s-expression from a list representation (helps debugging)
    @classmethod
    def s_expr_to_str(cls, e):
        if type(e) is type([]):
            return '(%s)' % ' '.join(map(cls.s_expr_to_str, e))
        else:
            return str(e)

    # internal (used in constructor)
    def _setPreviousLeaf(self, leaf):
        self.previousLeaf = leaf
        if len(self.children) > 0:
            self.children[0]._setPreviousLeaf(leaf)

    # internal (used in constructor)
    def _setNextLeaf(self, leaf):
        self.nextLeaf = leaf
        if len(self.children) > 0:
            self.children[-1]._setNextLeaf(leaf)

    # basic utility functions
    def isRoot(self):
        return self.root == self

    def isLeaf(self):
        return len(self.children) == 0

    # condition can be a:
    #    string (matched against label)
    #    a node (matched with ==)
    #    nothing (just check if it has a parent)
    #    a function (run against the node)
    def hasParent(self, condition = None):
        if type(condition) == type(""):
            filter = lambda x: x.label == condition
        elif type(condition) == type(self):
            filter = lambda x: x == condition
        elif condition == None:
            return self.parent != None
        else:
            filter = condition
        if self.parent == None:
            return False
        if filter(self.parent):
                return True
        return self.parent.hasParent(filter)

    # see hasParent()
    def hasChild(self, condition = None):
        if type(condition) == type(""):
            filter = lambda x: x.label == condition
        elif type(condition) == type(self):
            filter = lambda x: x == condition
        elif condition == None:
            return len(self.children) > 0
        else:
            filter = condition
        for node in self.children:
            if filter(node):
                return True
        return False

    # see hasParent()
    def hasLeaf(self, condition = None):
        if type(condition) == type(""):
            filter = lambda x: x.label == condition
        elif type(condition) == type(self):
            filter = lambda x: x == condition
        elif condition == None:
            return len(self.leaves) > 0
        else:
            filter = condition
        for node in self.leaves:
            if filter(node):
                return True
        return False

    # get the subtree as text or as a bracketted representation
    def getText(self):
        return " ".join(leaf.text for leaf in self.leaves)

    def __str__(self):
        output = "(" + self.label
        for child in self.children:
            output += " " + str(child)
        if len(self.children) == 0 or self.parent == None:
            output = output + " " + self.text
        output = output + ")"
        return output

    # nice multi-line representation
    def getTabbedRepresentation(self, tabs = "", firstChild = True):
        if firstChild:
            output = "(" + self.label + " "
        else:
            output = "\n" + tabs + "(" + self.label + " "
        tabs = tabs + (" " * (len(self.label) + 2))
        firstChild = True
        for child in self.children:
            output +=  child.getTabbedRepresentation(tabs, firstChild)
            firstChild = False
        if len(self.children) == 0 or self.parent == None:
            output += self.text
        output = output + ")"
        return output

    # getters for leaves, children and sub nodes according to a filter on the node
    # a label based filter is provided
    def getLeavesByLabel(self, label):
        return self.getLeavesByFilter(lambda x: x.label == label)

    def getLeavesByFilter(self, filter):
        output = []
        for leaf in self.leaves:
            if filter(leaf):
                output.append(leaf)
        return output

    def getChildrenByLabel(self, label):
        return self.getChildrenByFilter(lambda x: x.label == label)

    def getChildrenByFilter(self, filter):
        output = []
        for child in self.children:
            if filter(child):
                output.append(child)
        return output

    def getNodesByLabel(self, label):
        return self.getNodesByFilter(lambda x: x.label == label)

    def getNodesByFilter(self, filter):
        output = []
        if filter(self):
            output.append(self)
        for child in self.children:
            output.extend(child.getNodesByFilter(filter))
        return output

    def getParents(self):
        output = []
        parent = self.parent
        while parent:
            output.append(parent)
            parent = parent.parent
        return output

    def getParentsByLabel(self, label):
        return self.getParentsByFilter(lambda x: x.label == label)

    def getParentsByFilter(self, filter):
        output = []
        if self.hasParent():
            if filter(self.parent):
                output.append(self.parent)
            output.extend(self.parent.getParentsByFilter(filter))
        return output

    # removes the node from the tree and leaves the tree in a usable state
    # also removes empty parents
    def cut(self):
        parent = self.parent
        if self.hasParent():
            self.parent.children.remove(self)
        if self.nextSibling != None:
            self.nextSibling.previousSibling = self.previousSibling
        if self.previousSibling != None:
            self.previousSibling.nextSibling = self.nextSibling
        for leaf in self.leaves:
            for node in self.getParentsByFilter(lambda x: True):
                node.leaves.remove(leaf)
        if self.nextSibling != None:
            self.nextSibling._setPreviousLeaf(self.previousLeaf)
        if self.previousSibling != None:
            self.previousSibling._setNextLeaf(self.nextLeaf)
        self.previousSibling = None
        self.nextSibling = None
        self.previousLeaf = None
        self.nextLeaf = None
        self.parent = None
        for node in self:
            node.root = self
        self.root = self
        if parent != None and len(parent.children) == 0:
            parent.cut()

    def _updateLeaves(self):
        self.leaves = []
        for node in self.children:
            self.leaves.extend(node.leaves)
        if self.parent:
            self.parent._updateLeaves()
        else:
            for i in range(len(self.leaves)):
                self.leaves[i].leaf_index = i

    def grow(self, node, index):
        if index > len(self.children): index = len(self.children)
        if type(node) is not type(self):
            node = self.__class__(node, self)
        node.parent = self
        self.children.insert(index, node)
        # set parent leaves
        self._updateLeaves()
        # set nextSibling and previousSibling
        if index > 0:
            node.previousSibling = self.children[index - 1]
            self.children[index - 1].nextSibling = node
        if index < len(self.children) - 1:
            node.nextSibling = self.children[index + 1]
            self.children[index + 1].previousSibling = node
        # set nextLeaf and previousLeaf
        if node.previousSibling:
            node.previousSibling._setNextLeaf(node.leaves[0])
            node._setPreviousLeaf(node.previousSibling.leaves[-1])
        if node.nextSibling:
            node.nextSibling._setPreviousLeaf(node.leaves[-1])
            node._setNextLeaf(node.nextSibling.leaves[0])

    # iterate over all child nodes
    def __iter__(self):
        output = [self]
        for child in self.children:
            output.extend(child.__iter__())
        return output.__iter__()

    def getCommonParent(self, node):
        parent = self.parent
        while parent:
            if parent.getNodesByFilter(lambda x: x == node):
                break
            parent = parent.parent
        return parent

# tests a few functions
if __name__ == "__main__":
    import sys
    for root in TreeNode.readAllTrees(sys.stdin):
        print root
        print root.hasLeaf()
        print root.hasLeaf("DT")
        print root.hasLeaf(lambda x: x.text == "the")
        print root.getTabbedRepresentation()
        leaf = root.leaves[0]
        while leaf != None:
            print leaf.text
            leaf = leaf.nextLeaf
