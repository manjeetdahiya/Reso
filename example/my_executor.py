from src.executor.executor import Executor
from example.my_workflow import my_workflow

executor = Executor()
executor.register_workflow('my_workflow', my_workflow)

app = executor.server.app
