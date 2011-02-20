import sys, os
import glpk

def decode(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, nbest=1):
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
    num_concepts = concept

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
    num_sentences = sentence

    lp = glpk.LPX()
    glpk.env.term_on = False
    lp.obj.maximize = True
    lp.cols.add(num_concepts + num_sentences)
    for col in lp.cols:
        col.bounds = 0.0, 1.0
    for concept, weight in concept_weights.items():
        if concept not in index: continue # skip unused concepts
        lp.obj[concept] = weight

    # concept => sentence
    for concept in index:
        lp.rows.add(1)
        row = lp.rows[-1]
        row.bounds = 0, None
        matrix = [(num_concepts + sentence, 1.0) for sentence in index[concept]]
        matrix.append((concept, -1))
        row.matrix = matrix

    length_matrix = []
    sentence = 0
    for line in open(sentence_length_file):
        if sentence in sentence_concepts:
            length = float(line.strip())
            length_matrix.append((num_concepts + sentence, length))
            lp.obj[num_concepts + sentence] = - float(length) / 1000.0
        sentence += 1
    lp.rows.add(1)
    lp.rows[-1].bounds = None, max_length
    lp.rows[-1].matrix = length_matrix

    sys.stderr.write("ilp: %d sentences, %d concepts\n" % (num_sentences, num_concepts))

    result = lp.simplex()
    assert result == None
    if lp.status != 'opt': return None # no relaxed solution
    for col in lp.cols:
        col.kind = int
    result = lp.intopt()
    assert result == None
    if lp.status != 'opt': return None # no exact solution

    output = []
    for n in range(nbest - 1):
        selection = []
        for i in range(num_sentences):
            if lp.cols[num_concepts + i].value > 0.99:
                selection.append(i)

        output.append(selection)
        print lp.obj.value, selection
        lp.rows.add(1)
        lp.rows[-1].matrix = [(num_concepts + sentence, 1.0) for sentence in selection]
        lp.rows[-1].bounds = None, len(selection) - 1
        lp.simplex()
        lp.intopt()
    selection = []
    for i in range(num_sentences):
        if lp.cols[num_concepts + i].value > 0.99:
            selection.append(i)
    output.append(selection)
    print lp.obj.value, selection
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


