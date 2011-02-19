import sys, os

def decode(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
    program_file = open(concept_weight_file + ".lsp", "w")
    concept_id = {}
    concept = 0
    concept_weights = {}
    for line in open(concept_weight_file):
        tokens = line.strip().split()
        weight = float(tokens[1])
        if tokens[0] in concept_id:
            sys.stderr.write('ERROR: duplicate concept \"%s\", line %d in %s\n' % (tokens[0], concept + 1, concept_weight_file))
            sys.exit(1)
        concept_id[tokens[0]] = concept
        concept_weights[concept] = weight
        concept += 1

    index = {}
    sentence_concepts = {}
    sentence = 0
    for line in open(concepts_in_sentence_file):
        tokens = line.strip().split()
        concepts = {}
        for token in tokens:
            concepts[token] = True
        mapped_concepts = {}
        for concept in concepts:
            if concept not in concept_id:
                sys.stderr.write('ERROR: not weight for concept \"%s\", line %d in %s\n' % (concept, sentence + 1, concepts_in_sentence_file))
                sys.exit(1)
            id = concept_id[concept]
            if id not in index: index[id] = []
            index[id].append(sentence)
            mapped_concepts[id] = True
        if len(mapped_concepts) > 0:
            sentence_concepts[sentence] = mapped_concepts
        sentence += 1

    # build objective
    objective = []
    for concept, weight in concept_weights.items():
        if concept not in index: continue # skip unused concepts
        objective.append("%d c%d" % (int(weight * 1000), concept))
    program_file.write("maximize sum(" + ", ".join(objective) + ");\n")

    # sentence => concepts
    for sentence, concepts in sentence_concepts.items():
        program_file.write("s%d <- bool();\n" % sentence);

    # concept => sentence
    for concept in index:
        program_file.write(("c%d <- or(" % concept) + ", ".join(["s%d" % x for x in index[concept]]) + ");\n")

    if sentence_group_file != None:
        groups = {}
        sentence = 0
        for line in open(sentence_group_file):
            if sentence in sentence_concepts:
                if line != '\n':
                    if line not in groups:
                        groups[line] = []
                    groups[line].append(sentence)
            sentence += 1
        for group in groups:
            program_file.write("constraint sum(" + ", ".join(["s%d" % x for x in groups[group]]) + ") <= 1;\n")

    if dependency_file != None:
        groups = {}
        sentence = 0
        for line in open(dependency_file):
            if sentence in sentence_concepts:
                if line != '\n':
                    for id in line.strip().split():
                        id = int(id)
                        if "s%d" % id not in solver.binary:
                            pass
                            #solver.constraints["depend_%d" % len(solver.constraints)] = "s%d = 0" % (sentence)
                        else:
                            pass
                            #solver.constraints["depend_%d" % len(solver.constraints)] = "s%d - s%d >= 0" % (id, sentence)
            sentence += 1

    length_constraint = []
    sentence = 0
    objective = []
    for line in open(sentence_length_file):
        if sentence in sentence_concepts:
            length = line.strip()
            length_constraint.append("%s s%d" % (length, sentence))
            objective.append("-%d s%d" % (int(length), sentence))
        sentence += 1
    program_file.write("maximize sum(" + ", ".join(objective) + ");\n")

    program_file.write("constraint sum(" + ", ".join(length_constraint) + ") <= %d;\n" % max_length)

    if atleast != None:
        at_least = []
        sentence = 0
        for line in open(atleast):
            line = line.strip()
            if sentence in sentence_concepts:
                if line == "1":
                    at_least.append("s%d" % sentence)
            sentence += 1
        if len(at_least) > 0:
            pass
            #solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

    sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts), len(index)))

    program_file.close()
    if len(sentence_concepts) > 0 and len(index) > 0:
        os.system("./solver/localsolver io_lsp=%s.lsp io_solution=%s.sol hr_timelimit=1 >&2" % (concept_weight_file, concept_weight_file))
    output_file = open("%s.sol" % concept_weight_file)
    output = []
    for line in output_file.xreadlines():
        tokens = line.strip().split("=")
        if tokens[0].startswith("s") and tokens[1] == "1;":
            output.append(int(tokens[0][1:]))
    output_file.close()
    return output

if __name__ == '__main__':
    if len(sys.argv) < 5 or len(sys.argv) > 8:
        sys.stderr.write('USAGE: %s <length_constraint> <sentence_lengths> <concepts_in_sentences> <concept_weights> [sentence_groups] [dependencies] [atleast]\n')
        sys.exit(1)
    sentence_groups = None
    dependencies = None
    atleast = None
    if len(sys.argv) > 5:
        sentence_groups = sys.argv[5]
    if len(sys.argv) > 6:
        dependencies = sys.argv[6]
    if len(sys.argv) > 7:
        atleast = sys.argv[7]
    output = decode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sentence_groups, dependencies, atleast)
    for value in output:
        print value
    

