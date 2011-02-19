import sys

class DependencyNode:
    def __init__(self, lines=None):
        if lines:
            nodes = []
            predicate_nodes = []
            root = None
            for line in lines:
                tokens = line.strip().split("\t")
                parent = int(tokens[8]) - 1
                if parent == -1 and root == None:
                    root = self
                    self.parent = parent
                    self.id = int(tokens[0])
                    self.text = tokens[1]
                    if tokens[2] == "_":
                        self.lemma = tokens[3]
                    else:
                        self.lemma = tokens[2]
                    self.tag = tokens[4]
                    self.label = tokens[10]
                    self.children = []
                    self.predicate = tokens[13]
                    if self.isPredicate():
                        predicate_nodes.append(self)
                    self.argument_tokens = tokens[14:]
                    self.line = line
                    nodes.append(self)
                else:
                    node = DependencyNode()
                    if parent == -1:
                        parent = 0
                        sys.stderr.write('WARNING: multiple roots in sentence\n' + ''.join(lines))
                    node.parent = parent
                    node.id = int(tokens[0])
                    node.text = tokens[1]
                    if tokens[2] == "_":
                        node.lemma = tokens[3]
                    else:
                        node.lemma = tokens[2]
                    node.tag = tokens[4]
                    node.label = tokens[10]
                    node.predicate = tokens[13]
                    if node.isPredicate():
                        predicate_nodes.append(node)
                    node.argument_tokens = tokens[14:]
                    node.children = []
                    node.line = line
                    nodes.append(node)
            for node in nodes:
                node.arguments = []
                node.predicates = []
                if node.parent >= 0:
                    if node.parent >= len(nodes):
                        sys.stderr.write('ERROR: parent for %d not found \n%s\n' % (node.id, "\n".join(lines)))
                        sys.exit(2)
                    node.parent = nodes[node.parent]
                    node.parent.children.append(node)
                else:
                    node.parent = None
                if node.id > 1:
                    node.previous = nodes[node.id - 2]
                if node.id < len(nodes):
                    node.next = nodes[node.id]
                node.root = self
            try:
                for i in range(len(predicate_nodes)):
                    for node in nodes:
                        if node.argument_tokens[i] != "_":
                            predicate_nodes[i].arguments.append((node, node.argument_tokens[i]))
                            node.predicates.append(predicate_nodes[i])
            except:
                sys.stderr.write('ERROR: not enough fields for %s\n' % str(predicate_nodes[i].predicate))
                for line in lines:
                    sys.stderr.write(" ".join(line.split("\t")[13:]) + "\n")
                sys.exit(1)

    def getCommonParent(self, peer):
        parent = self
        while parent:
            if peer == parent:
                return peer
            for node in parent:
                if node == peer:
                    return parent
            parent = parent.parent
        return None
        
    def getPath(self, peer):
        common = self.getCommonParent(peer)
        output = []
        node = self
        while node != common:
            output.append(node)
            node = node.parent
        output.append(common)
        base = len(output)
        node = peer
        while node != common:
            output.insert(base, node)
            node = node.parent
        return output

    def getPredicates(self):
        output = []
        for node in self:
            if node.isPredicate():
                output.append(node)
        return output

    def isPredicate(self):
        return self.predicate != "_"

    def isArgument(self, predicate):
        return predicate in self.predicates

    def __iter__(self):
        output = [self]
        for node in self.children:
            output.extend(node.__iter__())
        output = sorted(output, lambda x, y: cmp(x.id, y.id))
        return output.__iter__()

    def __str__(self):
        output = []
        for node in self:
            if node.parent:
                output.append(" ".join((str(node.id), node.text, node.tag, str(node.parent.id), node.label)) + "\n")
            else:
                output.append(" ".join((str(node.id), node.text, node.tag, "0", node.label)) + "\n")
        return "".join(output)
    def __repr__(self):
        return self.text

    def getParents(self):
        output = []
        node = self.parent
        while node:
            output.append(node)
            node = node.parent
        return output

    @classmethod
    def readAllTrees(cls, input):        
        lines = []
        for line in input:
            if line.strip() == "" and len(lines) > 0:
                yield DependencyNode(lines)
                lines = []
                continue
            lines.append(line)
        if len(lines) > 0:
            yield DependencyNode(lines)

if __name__ == "__main__":
    for tree in DependencyNode.readAllTrees(sys.stdin):
        print tree
        continue
        for node in tree:
            for peer in tree:
                path = node.getPath(peer)
                print node.text, peer.text, [x.text for x in path]
