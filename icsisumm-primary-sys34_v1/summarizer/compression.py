import dependency, sys, re, detokenize

def generateCandidates(node):
    output = [[node]]
    new_output = []
    for child in node.children:
        child_output = generateCandidates(child)
        new_output = []
        for candidate in child_output:
            for peer in output:
                new_output.append(candidate + peer)
        output = new_output
    if node.label == "TMP" and len([x for x in node]) <= 3:
        words = [x.text for x in node]
        found = False
        for word in words:
            if re.match('^(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day$', word):
                found = True
                break
        if found: # don't look at the score if there is a day of the week
            output.append([])
            return output
    for token in node.argument_tokens:
        match = re.search(r'^(AM-(MNR|TMP))_(.*)', token)
        if match:
            score = float(match.groups()[2])
            if score > 0.6:
                output.append([])
                break
    return output
        
if len(sys.argv) != 4:
    sys.stderr.write('USAGE: %s <srl+scores_input> <output_text> <output_groups>\n' % sys.argv[0])
    sys.exit(1)

input = open(sys.argv[1])
output_text = open(sys.argv[2], "w")
output_groups = open(sys.argv[3], "w")
num = 0
say_verbs = set(["said", "says", "tells", "told", "wrote", "writes", "write", "reported"])
for tree in dependency.DependencyNode.readAllTrees(input):
        for node in tree:
            node.text2 = node.text
        for node in tree:
            if node.tag == "POS" and node.previous:
                node.previous.text2 += node.text
                node.text2 = ""
        roots = [tree]
        for node in tree:
            if node.label == "SUB" and node.parent and node.parent.label == "OBJ" and node.parent.parent and node.parent.parent.text.lower() in say_verbs:
                roots.append(node)
            if node.lemma != "that" and node.label == "OBJ" and node.parent and node.parent.text.lower() in say_verbs:
                roots.append(node)
        num_candidates = 0
        for root in roots:
            for candidate in sorted(generateCandidates(root), lambda x, y: cmp(len(y), len(x))):
                if num_candidates == 10: break
                candidate.sort(lambda x, y: cmp(x.id, y.id))
                if len([x for x in candidate]) < len([x for x in tree]) / 2: continue
                if len([x for x in candidate]) < 5: continue
                #text = " ".join([x.text + "/" + x.label for x in candidate])
                text = " ".join([x.text2 for x in candidate])
                detokenized = detokenize.postProcess(text)
                if len(detokenized) < 10:
                    continue
                output_groups.write("%d\n" %num)
                output_text.write("%s\n" % detokenized)
                num_candidates += 1
            if num_candidates == 10: break
        num += 1
input.close()
output_text.close()
output_groups.close()
