import os, sys, popen2

class Parser:
    def __init__(self):
        self.jobs = {}
        self.parsed = {}

    def clear(self):
        self.jobs = {}
        self.parsed = {}

    def add_job(self, id, sentence):
        self.jobs[id] = sentence

    def run(self):
        abstract()
        
    def get_job(self, id):
        return self.jobs[id]

    def parse(self, sentence):
        self.clear()
        self.add_job(0, sentence)
        self.run()
        return self.get_job(0)

class CommandLineParser(Parser):
    def __init__(self, command):
        Parser.__init__(self)
        self.command = command

    def run(self):
        if not self.jobs:
            return
        output, input = popen2.popen2(self.command)
        for id in self.jobs:
            input.write(self.jobs[id] + "\n")
        input.close()
        for id in self.jobs:
            self.parsed[id] = output.readline().rstrip()
        output.close()

if __name__ == "__main__":
    #parser = CommandLineParser("parser_bin/berkeleyParser+Postagger.sh")
    parser = CommandLineParser("parser_bin/distribute.sh parser_bin/berkeleyParser+Postagger.sh")
    id = 0
    for line in sys.stdin.readlines():
        line = line.rstrip()
        parser.add_job(id, line)
        id += 1
    parser.run()
    for id in parser.parsed:
        print id, parser.parsed[id]
