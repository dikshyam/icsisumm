import treenode, utils, unresolved
import os, sys, re, traceback
from lxml import etree

def _add_coref_annot(element, parse_tree, word_id):
    text_start = word_id
    if element.text:
        word_id += len(element.text.strip().split())
    for child in element:
        word_id += _add_coref_annot(child, parse_tree, word_id)
    text_end = word_id
    if element.tag == 'COREF':
        found = 0
        node = parse_tree.leaves[text_start]
        while node.parent:
            if node.leaves[0].leaf_index < text_start or node.leaves[-1].leaf_index >= text_end - 1:
                found = 1
                node.coref = element.attrib['ID']
                break
            node = node.parent
        if found == 0:
            sys.stderr.write('WARNING: not found [%s] in %s\n' % (" ".join([x.text for x in parse_tree.leaves[text_start:text_end]]), parse_tree) )
            raise Exception()
    if element.tail:
        word_id += len(element.tail.strip().split())
    return word_id - text_start

def annotate_tree_with_coref(tree, line):
    for node in tree:
        node.coref = ""
    line = line.replace("&", "&amp;")
    try:
        root = etree.XML("<ROOT>%s</ROOT>" % line)
        word_id = 0
        if root.text:
            word_id += len(root.text.strip().split())
        for element in root:
            word_id += _add_coref_annot(element, tree, word_id)
    except:
        traceback.print_exc()
        return False
    return True

for file in sys.argv[1:]:
    file = re.sub(r'.parse$', r'', file)
    coref_file = file + ".coref"
    try:
        coref_lines = open(coref_file).readlines()
    except:
        sys.stderr.write("WARNING: %s not found\n" % coref_file)
        continue
    name_file = file + ".name"
    try:
        name_lines = open(name_file).readlines()
    except:
        sys.stderr.write("WARNING: %s not found\n" % name_file)
        continue
    parse_file = file + ".parse"
    trees = [x for x in treenode.TreeNode.readAllTrees(open(parse_file))]

    current_tree = 0
    for line in coref_lines:
        line = line.strip()
        if re.match(r'^</?(DOC|TEXT|DOCNO)[ >]', line): continue
        if line == "<TURN>":
            current_tree += 1
            continue
        if not annotate_tree_with_coref(trees[current_tree], line):
            sys.stderr.write("WARNING: %s could not process line [%s] %d/%d\n" % (coref_file, line, current_tree, len(trees)))
        current_tree += 1
    for tree in trees:
        for node in tree:
            if node.label == '-NONE-':
                node.cut()
            node.label = re.sub(r'-.*', '', node.label)
        for node in tree:
            if node.coref != "" and node.getNodesByFilter(lambda x: x.label.startswith("PRP")) and not node.getNodesByFilter(lambda x: x != node and x.coref != ""):
                found = False
                for peer in tree:
                    if peer == node: continue
                    if node.hasParent(peer): continue
                    if peer.leaves[0].label.startswith("PRP"): continue
                    if peer.coref == node.coref and peer.leaves[-1].leaf_index < node.leaves[0].leaf_index:
                        found = True
                        break
                node.resolved = found
    tree_num = 0
    for tree in trees:
        for node in tree.leaves:
            if node.label.startswith("PRP") and hasattr(node, "resolved"):
                label = node.resolved
                features = unresolved.extract_features(node)
                saved = node.text
                node.text = "<%s>" % node.text
                print " ".join(features) + (",%s" % tree.getText().replace(",","<comma>")) + ",%s." % label
                node.text = saved
