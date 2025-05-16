from src.storage.storage import Storage
from src.executor.context import WorkflowContext
import httpx
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG)

class Orchestrator:
    def __init__(self):
        self.storage = Storage()
        self.executors = {}
        self.workflow_id_executor_map = {}

    def register_executor(self, executor_server):
        if executor_server in self.executors:
            logging.warning(f"Executor {executor_server} already registered")
        self.executors[executor_server] = {"workflows": []}

    def unregister_executor(self, executor_server):
        if executor_server in self.executors:
            del self.executors[executor_server]
            self.remove_all_mappings_of_executor(executor_server)
            logging.info(f"Unregistered executor {executor_server}")
        else:
            logging.warning(f"Executor {executor_server} not found")

    def register_workflow(self, executor_server, workflow_name):
        logging.info(f"Registering workflow {workflow_name} on executor {executor_server}")
        if executor_server not in self.executors:
            self.executors[executor_server] = {"workflows": []}
        if workflow_name not in self.executors[executor_server]["workflows"]:
            self.executors[executor_server]["workflows"].append(workflow_name)
            asyncio.create_task(self._start_pending_workflows(workflow_name))

    async def _start_pending_workflows(self, workflow_name):
        wfs = self.storage.list_workflows()
        for wf in wfs:
            status = wf["status"]
            workflow_id = wf["workflow_id"]
            workflow_name_stored = self.storage.get_workflow_info(workflow_id)["workflow_name"]
            if workflow_name_stored == workflow_name and status != "COMPLETED":
                logging.info(f"Starting pending workflow {workflow_id} for {workflow_name}")
                self._start_workflow_on_executor(workflow_id, workflow_name)

    def start_workflow(self, workflow_id, workflow_name, input):
        self._submit_workflow(workflow_id, workflow_name, input)
        self._start_workflow_on_executor(workflow_id, workflow_name)

    def _start_workflow_on_executor(self, workflow_id, workflow_name):
        executor_server = self.get_executor_for_workflow(workflow_name)
        if executor_server:
            try:
                payload = {"workflow_id": workflow_id}
                httpx.post(f"{executor_server}/workflow", json=payload)
                self.workflow_id_executor_map[workflow_id] = executor_server
            except Exception as e:
                logging.error(f"Failed to start workflow {workflow_id} on executor {executor_server}: {e}")
                self.unregister_executor(executor_server)
        else:
            logging.error(f"No executor found for workflow {workflow_name}")

    def _submit_workflow(self, workflow_id, workflow_name, input):
        ctx  = WorkflowContext(workflow_id=workflow_id, storage=self.storage, executor=None)
        ctx.submit_workflow(workflow_name, input)

    def store_event(self, workflow_id, event_name, event_data):
        ctx = WorkflowContext(workflow_id=workflow_id, storage=self.storage, executor=None)
        ctx.event_sequence_number = self.storage.find_event_sequence_number(workflow_id)
        event_sequence_number = ctx.event_sequence_number + 1
        ctx.storage.save_event(workflow_id, event_sequence_number, event_name, event_data)

    def get_workflow_status(self, workflow_id):
        status = self.storage.get_status(workflow_id)
        if status == None:
            raise Exception(f"Workflow {workflow_id} not found")
        return status

    async def get_workflows(self):
        return self.storage.list_workflows()

    def get_active_workflows(self):
        return [w["workflow_id"] for w in self.get_workflows() if w.get("status") == "active"]

    def get_executor_for_workflow(self, workflow_name):
        for executor_server, workflows in self.executors.items():
            if workflow_name in workflows["workflows"]:
                return executor_server
        return None
    
    def remove_workflow_id_executor_mapping(self, workflow_id):
        if workflow_id in self.workflow_id_executor_map:
            executor_server = self.workflow_id_executor_map[workflow_id]
            del self.workflow_id_executor_map[workflow_id]
            logging.info(f"Removed mapping for workflow {workflow_id} from executor {executor_server}")
        else:
            logging.warning(f"No mapping found for workflow {workflow_id}")

    def remove_all_mappings_of_executor(self, executor_server):
        for workflow_id, server in list(self.workflow_id_executor_map.items()):
            if server == executor_server:
                del self.workflow_id_executor_map[workflow_id]
                logging.info(f"Removed mapping for workflow {workflow_id} from executor {executor_server}")

    def get_executor_for_workflow_id(self, workflow_id):
        return self.workflow_id_executor_map.get(workflow_id, None)
    