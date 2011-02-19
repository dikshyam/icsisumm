import sys, re

def convert(lines):
    output = []
    section = "none"
    objective = ""
    direction = "minimize"
    variable_type = "binary"
    for line in lines:
        line = line.strip()
        if line.lower() == "maximize":
            section = "objective"
            direction = "maximize"
        elif line.lower() == "minimize":
            section = "objective"
            direction = "minimize"
        elif line.lower() == "subject to" or line.lower() == "subjectto":
            section = "constraints"
        elif line.lower() == "binary":
            section = "declarations"
            variable_type = "binary"
        elif line.lower() == "end":
            break
        elif line != "":
            if section == "objective":
                line = re.sub(r"\s*(\+\s*)?-\s*", r", -", line)
                line = re.sub(r"\s*(\+\s*)?\+\s*", r", ", line)
                line = re.sub(r".*:\s*,?", direction + " sum(", line)
                line = re.sub(r"(\b[-+]?\d*\.?\d+)", lambda x:str(int(1000 * float(x.group(1)))), line)
                line += ");"
                output.append(line)
            elif section == "declarations":
                if variable_type == "binary":
                    output.append(line + " <- bool();")
            elif section == "constraints":
                line = re.sub(r"\s*(\+\s*)?-\s*", r", -", line)
                line = re.sub(r"\s*(\+\s*)?\+\s*", r", ", line)
                line = re.sub(r".*:\s*,?", "constraint sum(", line)
                line = re.sub(r"(\b[-+]?\d*\.?\d+)", lambda x:str(int(1000 * float(x.group(1)))), line)
                line = re.sub(r"([<>]?=.*)", r") \1;", line);
                output.append(line)
    return output

if __name__ == '__main__':
    output = convert(sys.stdin)
    for line in output:
        print line
