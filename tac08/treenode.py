
class TreeNode:
    # this class handles a parse tree in bracketted format "(S (NP (NNP Python)))"
    # this basic implementation assumes that the parse tree is well formed
    #
    # available members for crossing the tree:
    # - root = the root of the tree
    # - parent = the parent of the node
    # - children = the children of the node
    # - nextSibling = the next child of this node's parent
    # - previousSibling = the next child of this node's parent
    # - leaves = the deepest children of that node
    # - nextLeaf = the first leaf of the next slibling
    # - previousLeaf = the last leaf of the previous slibling
    #
    # available members specific to parse trees:
    # - label = the node label (NP, VP, S, NNP, VB, JJ, ...)
    # - text = the text attached to the node, if it's a leaf
    def __init__(self, text, start = 0, parent = None, root = None):
        self.parent = parent
        if root != None:
            self.root = root
        else:
            self.root = self
        self.start = start
        self.end = start
        self.text = ""
        self.label = ""
        self.index = 0
        self.children = []
        self.previousSlibling = None
        self.nextSlibling = None
        self.previousLeaf = None
        self.nextLeaf = None
        self.leaves = []
        # BUG: this is unable to handle "( () )"
        while start < len(text) and text[start] != ' ': start+=1
        self.label = text[self.start + 1:start]
        while start < len(text) and text[start] != ')':
            while text[start] == ' ': start+=1
            if text[start] == '(':
                child = self.__class__(text, start, self, self.root)
                child.index = len(self.children)
                start = child.end
                self.children.append(child)
                self.leaves.extend(child.leaves)
            else:
                closing = text.find(")", start)
                if closing > start:
                    self.text = text[start:closing]
                    self.leaves.append(self)
                    start = closing 
                else:
                    start = start + 1
        self.end = start + 1
        for index in range(len(self.children) - 1):
            self.children[index].nextSlibling = self.children[index + 1]
            self.children[index + 1].previousSlibling = self.children[index]
            self.children[index].setNextLeaf(self.children[index + 1].leaves[0])
            self.children[index + 1].setPreviousLeaf(self.children[index].leaves[-1])

    def setPreviousLeaf(self, leaf):
        self.previousLeaf = leaf
        if len(self.children) > 0:
            self.children[0].setPreviousLeaf(leaf)

    def setNextLeaf(self, leaf):
        self.nextLeaf = leaf
        if len(self.children) > 0:
            self.children[-1].setNextLeaf(leaf)

    # basic utility functions
    def isRoot(self):
        return self.root == self

    def isLeaf(self):
        return len(self.children) == 0

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

    def getParentsByLabel(self, label):
        return self.getParentsByFilter(lambda x: x.label == label)

    def getParentsByFilter(self, filter):
        output = []
        if self.hasParent():
            if filter(self.parent):
                output.append(self.parent)
            output.extend(self.parent.getParentsByFilter(filter))
        return output

    def __iter__(self):
        output = [self]
        for child in self.children:
            output.extend(child.__iter__())
        return output.__iter__()

if __name__ == "__main__":
    import sys
    for line in sys.stdin.readlines():
        root = TreeNode(line)
        print root.hasLeaf("DT")
        print root.hasLeaf(lambda x: x.text == "the")
        print root.getTabbedRepresentation()
        leaf = root.leaves[0]
        while leaf != None:
            print leaf.text
            leaf = leaf.nextLeaf
