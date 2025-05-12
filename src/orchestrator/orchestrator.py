from src.storage.storage import Storage
from src.executor.context import WorkflowContext
import httpx

class Orchestrator:
    def __init__(self):
        self.storage = Storage()
        self.executors_map = {}
        self.workflow_execution_mapping = {}

    def register_executor(self, executor_url):
        if executor_url not in self.executors_map:
            self.executors_map[executor_url] = {"workflows": []}

    def register_workflow(self, executor_url, workflow_name):
        if executor_url not in self.executors_map:
            self.executors_map[executor_url] = {"workflows": []}
        self.executors_map[executor_url]["workflows"].append(workflow_name)

    def start_workflow(self, workflow_id, workflow_name, input):
        self._submit_workflow(workflow_id, workflow_name, input)

        executor_url = self.get_executor_for_workflow(workflow_name)
        if executor_url:
            payload = {"workflow_id": workflow_id}
            httpx.post(f"{executor_url}/workflow", json=payload)
            self.workflow_execution_mapping[workflow_id] = executor_url
        else:
            raise Exception(f"No executor found for workflow {workflow_name}")

    def _submit_workflow(self, workflow_id, workflow_name, input):
        ctx  = WorkflowContext(workflow_id=workflow_id, storage=self.storage)
        ctx.submit_workflow(workflow_name, input)

    async def get_workflow_status(self, workflow_id):
        status = self.storage.get_status(workflow_id)
        if status == None:
            raise Exception(f"Workflow {workflow_id} not found")
        return status

    async def get_workflows(self):
        return self.storage.list_workflows()

    def get_active_workflows(self):
        return [w["workflow_id"] for w in self.get_workflows() if w.get("status") == "active"]

    def get_executor_for_workflow(self, workflow_name):
        for executor_url, workflows in self.executors_map.items():
            if workflow_name in workflows["workflows"]:
                return executor_url
        return None