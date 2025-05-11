from src.executor.executor import Executor
from example.my_workflow import my_workflow

executor = Executor(orchestrator_server='http://localhost:8008', executor_url='http://localhost:8009')
executor.register_workflow('my_workflow', my_workflow)

app = executor.server.app
