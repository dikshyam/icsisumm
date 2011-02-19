import os, sys, popen2

class Batch:
    def __init__(self):
        self.jobs = {}
        self.outputs = {}

    def add_job(self, id, input):
        self.jobs[id] = input

    def get_job(self, id):
        return self.jobs[id]

    def run(self):
        abstract


class BatchCmd(Batch):
    def __init__(self, command):
        Batch.__init__(self)
        self.command = command
        
    def run(self):
        if not self.jobs: return
        output, input = popen2.popen2(self.command)
        for id in self.jobs:
            input.write(self.jobs[id] + '\n')
        input.close()
        for id in self.jobs:
            self.outputs[id] = output.readline().rstrip()
        output.close()

class BatchSBD(Batch):

    def run(self):
        if not self.jobs: return

        ## create a model
        
