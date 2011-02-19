import sys, os

names = []
scores = {}
for eval_file in sys.argv[1:]:
    name = os.path.basename(eval_file).replace(".eval.txt", "")
    if name == "eval.txt": name = "baseline"
    name = name.replace("ie-concepts+regular-concepts", "ie+b")
    name = name.replace("ie-concepts", "ie")
    names.append(name)
    for line in open(eval_file):
        if line.startswith("D"):
            tokens = line.strip().split()
            topic = tokens[0]
            if topic not in scores: scores[topic] = {}
            scores[topic][name] = tokens[2] # rouge 2

names.sort()
print ";" + ";".join(names)
for topic in scores:
    output = [topic]
    for name in names:
        if name in scores[topic]:
            output.append(scores[topic][name])
        else:
            output.append("")
    print ";".join(output)
