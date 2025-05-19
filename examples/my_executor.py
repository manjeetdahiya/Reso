from src.executor.executor import Executor
from examples.my_workflow import my_workflow
from examples.my_workflow_2 import my_workflow_2

executor = Executor(orchestrator_server='http://localhost:8008', executor_server='http://localhost:8009')
executor.register_workflow('my_workflow', my_workflow)
executor.register_workflow('my_workflow_2', my_workflow_2)
