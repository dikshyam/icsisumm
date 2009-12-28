import re 
def extract_features(node):
    features = []
    features.append("text:" + node.text.lower())
    features.append("tag:" + node.label)
    if node.previousLeaf:
        features.append("text_p:" + node.previousLeaf.text.lower())
        features.append("text_cp:" + node.text.lower() + "_" + node.previousLeaf.text.lower())
        features.append("tag_p:" + node.previousLeaf.label)
        features.append("tag_cp:" + node.previousLeaf.label + "_" + node.label)
    if node.nextLeaf:
        features.append("text_n:" + node.nextLeaf.text.lower())
        features.append("text_cn:" + node.text.lower() + "_" + node.nextLeaf.text.lower())
        features.append("tag_n:" + node.nextLeaf.label)
        features.append("tag_cn:" + node.label + "_" + node.nextLeaf.label)
    features.append("index:%d" % (10.0 * node.leaf_index / len(node.root.leaves)))
    features.append("parent:" + node.parent.label)
    if node.parent.previousSibling:
        features.append("parent_p:" + node.parent.previousSibling.label)
    else:
        features.append("parent_p:none")
    if node.parent.nextSibling:
        features.append("parent_p:" + node.parent.nextSibling.label)
    else:
        features.append("parent_n:none")
    features.append("parent_index:%d" % node.parent.index)
    if node.leaf_index < len(node.root.leaves) / 2:
        features.append("first_half:1")
    count = 0
    for peer in node.root:
        if peer.label.startswith("NP") and peer.leaves[-1].leaf_index < node.leaf_index:
            common = peer.getCommonParent(node)
            features.append("np_common:%s" % common.label)
            features.append("np_before_common:%s" % common.label)
            features.append("np_before_leaf_first:%s" % peer.leaves[0].label)
            features.append("np_before_leaf_last:%s" % peer.leaves[-1].label)
            count += 1
    features.append("np_before:%d" % count)
    count = 0
    for peer in node.root:
        if peer.label.startswith("NP") and peer.leaves[0].leaf_index > node.leaf_index:
            common = peer.getCommonParent(node)
            features.append("np_common:%s" % common.label)
            features.append("np_after_common:%s" % common.label)
            features.append("np_after_leaf_first:%s" % peer.leaves[0].label)
            features.append("np_after_leaf_last:%s" % peer.leaves[-1].label)
            count += 1
    features.append("np_after:%d" % count)
    count = 0
    for peer in node.root.leaves:
        if re.match(r'(\'\'|``|")', peer.text) and peer.leaf_index > node.leaf_index:
            count += 1
    count = 0
    for peer in node.root.leaves:
        if re.match(r'(\'\'|``|")', peer.text) and peer.leaf_index > node.leaf_index:
            count += 1
    features.append("quotes_after:%d" % count)
    count = 0
    for peer in node.root.leaves:
        if re.match(r'(\'\'|``|")', peer.text) and peer.leaf_index < node.leaf_index:
            count += 1
    features.append("quotes_before:%d" % count)
    prp_before = 0
    for peer in node.root.leaves:
        if peer.label.startswith("PRP") and peer.leaf_index < node.leaf_index:
            prp_before += 1
    features.append("prp_before:%d" % count)
    repeats = 0
    for peer in node.root.leaves:
        if peer.label.startswith("PRP") and peer.text.lower() == node.text.lower() and peer.leaf_index < node.leaf_index:
            repeats += 1
    features.append("repeats:%d" % repeats)
    if repeats == 0 and prp_before > 0:
        features.append("other_prp_before:1")
    features.append("length:%d" % (len(node.root.leaves) / 5))
    features = [x.replace(",", "<COMMA>") for x in features]
    return features

if __name__ == "__main__":
    import icsiboost, sys, treenode
    if len(sys.argv) != 3:
        sys.stderr.write('USAGE: %s <model> <threshold>\n')
        sys.exit(1)
    classifier = icsiboost.Classifier(sys.argv[1])
    threshold = float(sys.argv[2])
    for tree in  treenode.TreeNode.readAllTrees(sys.stdin):
        pronoun = None
        for node in tree.leaves:
            if node.label.startswith('PRP'):
                features = extract_features(node)
                posteriors = classifier.compute_posteriors([features])
                if posteriors[0] > threshold:
                    pronoun = "%s %d" % (node.text, node.leaf_index)
                    #pronoun = node.root.getText()
                    break
        if pronoun:
            print "1", pronoun
        else:
            print "0"
