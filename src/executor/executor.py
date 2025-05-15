from src.storage.storage import Storage
from src.executor.server import Server
import httpx
import logging

logging.basicConfig(level=logging.DEBUG, format='RESO LOG: %(asctime)s - %(levelname)s - %(message)s')

class Executor:
    def __init__(self, orchestrator_server, executor_server):
        self.orchestrator_server = orchestrator_server
        self.server = Server(self)
        self.executor_server = executor_server
        self.event_registry = {}
        
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
        from src.executor.context import WorkflowContext
        context = WorkflowContext(workflow_id, self.storage, self)
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
            logging.debug(f"Workflow {workflow_id} executed successfully")
        except Exception:
            context.set_status("ERROR")
            logging.debug(f"Workflow {workflow_id} failed")
            raise

    async def send_event(self, workflow_id, event_name, value):
        logging.debug(f"Sending event {event_name} to workflow {workflow_id}")
        if workflow_id in self.event_registry and event_name in self.event_registry[workflow_id]:
            future = self.event_registry[workflow_id][event_name]
            future.set_result(value)
            del self.event_registry[workflow_id][event_name]
        else:
            logging.debug(f"No waiting workflow found for event {event_name} in {workflow_id}")