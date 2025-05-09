from src.orchestrator.context import WorkflowContext
from src.storage.storage import Storage

class Executor:
    def __init__(self, workflow_mapping, storage):
        self.workflow_mapping = workflow_mapping
        self.storage = storage

    def register_workflow(self, workflow_name, workflow_func):
        self.workflow_mapping[workflow_name] = workflow_func

    async def execute_workflow(self, workflow_id, workflow_name, input):
        context = WorkflowContext(workflow_id, self.storage)
        try:
            context.set_status("active")
            result = await self.workflow_mapping[workflow_name](context, **input)
            context.set_status("completed")
        except Exception:
            context.set_status("failed")
            raise
        print(f"Workflow {workflow_id} completed with result: {result}")

    async def get_workflow_status(self, workflow_id):
        context = WorkflowContext(workflow_id, self.storage)
        status = context.get_status()
        if status is None:
            raise Exception(f"Workflow {workflow_id} not found")
        return status

    async def get_workflows(self):
        return self.storage.list_workflows()

    def get_active_workflows(self):
        return [w["workflow_id"] for w in self.get_workflows() if w.get("status") == "active"]
