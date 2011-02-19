import sys, os
import ilp, ilp_to_localsolver

def decode(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
    solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command)
    #solver = ilp_to_localsolver.IntegerLinearProgram(debug=1, tmp = concept_weight_file, time_limit=1)
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
        objective.append("%+g c%d" % (weight, concept))
        solver.binary["c%d" % concept] = concept
    solver.objective["score"] = " ".join(objective)

    # sentence => concepts
    for sentence, concepts in sentence_concepts.items():
        solver.binary["s%d" % sentence] = sentence
    #    for concept in concepts:
    #        solver.constraints["sent_%d" % len(solver.constraints)] = "s%d - c%d <= 0" % (sentence, concept)

    # concept => sentence
    for concept in index:
        solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept

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
            solver.constraints["group_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in groups[group]]) + " <= 1"

    if dependency_file != None:
        groups = {}
        sentence = 0
        for line in open(dependency_file):
            if sentence in sentence_concepts:
                if line != '\n':
                    for id in line.strip().split():
                        id = int(id)
                        if "s%d" % id not in solver.binary:
                            solver.constraints["depend_%d" % len(solver.constraints)] = "s%d = 0" % (sentence)
                        else:
                            solver.constraints["depend_%d" % len(solver.constraints)] = "s%d - s%d >= 0" % (id, sentence)
            sentence += 1

    length_constraint = []
    sentence = 0
    for line in open(sentence_length_file):
        if sentence in sentence_concepts:
            length = line.strip()
            length_constraint.append("%s s%d" % (length, sentence))
            solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
        sentence += 1

    solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

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
            solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

    sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts), len(index)))

    if len(sentence_concepts) > 0 and len(index) > 0:
        solver.run()
    output = []
    for variable in solver.output:
        if variable.startswith("s") and solver.output[variable] == 1:
            output.append(int(variable[1:]))
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
    

