from src.executor.context import WorkflowContext
from src.storage.storage import Storage
from src.executor.server import Server
import httpx

class Executor:
    def __init__(self, orchestrator_server, executor_url):
        self.orchestrator_server = orchestrator_server
        self.executor_url = executor_url
        
        self.storage = Storage()
        response = httpx.get(self.orchestrator_server + "/storage_config")
        self.storage.set_config(response.json())

        httpx.post(self.orchestrator_server + "/register_executor", json={"executor_url": executor_url})

        self.server = Server(self)
        self.workflow_mapping = {}

    def register_workflow(self, workflow_name, workflow_func):
        self.workflow_mapping[workflow_name] = workflow_func
        httpx.post(self.orchestrator_server + "/register_workflow", json={
            "executor_url": self.executor_url,
            "workflow_name": workflow_name
        })

    async def execute_workflow(self, workflow_id):
        context = WorkflowContext(workflow_id, self.storage)
        wf_info = context.storage.get_workflow_info(workflow_id)
        workflow_name = wf_info["workflow_name"]
        input = wf_info["input"]
        
        if workflow_name not in self.workflow_mapping:
            raise Exception(f"Workflow {workflow_name} not registered")
        
        workflow_func = self.workflow_mapping[workflow_name]
        try:
            context.set_status("RUNNING")
            result = await workflow_func(context, **input)
            context.set_status("COMPLETED")
        except Exception:
            context.set_status("ERROR")
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

