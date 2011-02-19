import os, sys, cpxlp_to_localsolver, re

class IntegerLinearProgram:
    # this class handles a basic ILP for glpsol from the Gnu linear programming toolkit, in cpxlp format
    # note that:
    # - only binary and integer variables are supported
    # - the behavior is not defined if no solution is found
    # - the solver might run for a long time
    def __init__(self, command = "./solver/LocalSolver_1_0_20100222/binaries/linux-i686/localsolver", tmp = "./tmp.glpsol", debug = 1, time_limit = 1):
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

        cpxlp_file = open(self.tmp + ".glpsol", "w")
        cpxlp_file.write(str(self))
        cpxlp_file.close()

        lsolver_file = open(self.tmp + ".lsolver", "w")
        for line in cpxlp_to_localsolver.convert(str(self).split("\n")):
            lsolver_file.write(line + "\n")
        lsolver_file.close()

        if self.debug:
            #os.system("%s --tmlim %d --cpxlp %s.ilp -o %s.sol >&2" % (self.command, self.time_limit, self.tmp, self.tmp))
            os.system("%s hr_timelimit=%d io_lsp=%s.lsolver io_solution=%s.sol >&2" % (self.command, self.time_limit, self.tmp, self.tmp))
        else:
            output = os.popen("%s hr_timelimit=%d io_lsp=%s.lsolver io_solution=%s.sol" % (self.command, self.time_limit, self.tmp, self.tmp))
            text = "".join(output.readlines())
            if output.close():
                sys.stderr.write("ERROR: glpsol failed\n")
                sys.stderr.write(text)
                sys.exit(1)

        self.get_solution()

        if not self.debug:
            os.remove(self.tmp + ".lsolver")
            os.remove(self.tmp + ".sol")

    def get_solution(self):
        for line in open("%s.sol" % self.tmp).readlines():
            fields = re.sub(r";", "", line.strip()).split("=")
            if (fields[0] in self.binary) or (fields[0] in self.integer):
                self.output[fields[0]] = int(fields[1])

