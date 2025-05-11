from src.orchestrator.executors import Executors
from src.orchestrator.workflows_manager import WorkflowsManager

class Orchestrator:
    def __init__(self):
        self.executors = Executors()
        self.workflows_manager = WorkflowsManager(workflow_mapping={}, storage=None)
