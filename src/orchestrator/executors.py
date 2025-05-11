class Executors:
    def __init__(self):
        self.executors = {}

    def register_executor(self, executor_url):
        self.executors[executor_url] = []

    def register_workflow(self, executor_url, workflow_name):
        self.executors[executor_url].append(workflow_name)