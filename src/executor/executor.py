from src.executor.context import WorkflowContext
from src.storage.storage import Storage
from src.executor.server import Server
import httpx

class Executor:
    def __init__(self, orchestrator_server, executor_server):
        self.orchestrator_server = orchestrator_server
        self.server = Server(self)
        self.executor_server = executor_server
        
        self.storage = Storage()
        response = httpx.get(self.orchestrator_server + "/storage_config")
        self.storage.set_config(response.json())

        httpx.post(self.orchestrator_server + "/register_executor", json={"executor_server": executor_server})

        self.workflow_mapping = {}

    def register_workflow(self, workflow_name, workflow_func):
        self.workflow_mapping[workflow_name] = workflow_func
        httpx.post(self.orchestrator_server + "/register_workflow", json={
            "executor_server": self.executor_server,
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
