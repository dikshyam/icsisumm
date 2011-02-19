import os, sys

class IntegerLinearProgram:
    # this class handles a basic ILP for glpsol from the Gnu linear programming toolkit, in cpxlp format
    # note that:
    # - only binary and integer variables are supported
    # - the behavior is not defined if no solution is found
    # - the solver might run for a long time
    def __init__(self, command = "/u/favre/install/bin/glpsol", tmp = "./tmp.glpsol", debug = 0, time_limit = 100):
        self.command = command
        self.tmp = tmp
        self.debug = debug
        self.time_limit = time_limit
        self.objective = {}
        self.constraints = {}
        self.binary = {}
        self.integer = {}
        self.output = {}

    def __str__(self):
        output = ''
        if len(self.objective) > 0:
            output += "Maximize\n"
            for function in sorted(self.objective.keys()):
                output += function + ": " + self.objective[function] + "\n"

        if self.constraints > 0:
            output += "\nSubject To\n"
            for constraint in sorted(self.constraints.keys()):
                output += constraint + ": " + self.constraints[constraint] + "\n"
        if len(self.binary) > 0:
            output += "\nBinary\n"
            for variable in sorted(self.binary.keys()):
                output += variable + "\n"
        if len(self.integer) > 0:    
            output += "\nInteger\n"
            for variable in sorted(self.integer.keys()):
                output += variable + "\n"
        output += "End\n"        
        return output

    def run(self):
        input = open(self.tmp + ".ilp", "w")
        input.write(str(self))
        input.close()

        if self.debug:
            os.system("%s --tmlim %d --cpxlp %s.ilp -o %s.sol >&2" % (self.command, self.time_limit, self.tmp, self.tmp))
        else:
            output = os.popen("%s --tmlim %d --cpxlp %s.ilp -o %s.sol" % (self.command, self.time_limit, self.tmp, self.tmp))
            text = "".join(output.readlines())
            if output.close():
                sys.stderr.write("ERROR: glpsol failed\n")
                sys.stderr.write(text)
                sys.exit(1)

        self.get_solution()

        if not self.debug:
            os.remove(self.tmp + ".ilp")
            os.remove(self.tmp + ".sol")

    def get_solution(self):
        for line in open("%s.sol" % self.tmp).readlines():
            fields = line.strip().split()
            if len(fields) >= 5 and ((fields[1] in self.binary) or (fields[1] in self.integer)):
                self.output[fields[1]] = int(fields[3])

