from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio
from src.storage.storage import Storage
from src.executor.executor import Executor

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict = {}

class Server:
    def __init__(self, workflow_mapping: dict):
        self.app = FastAPI()
        self.storage = Storage()
        self.executor = Executor(workflow_mapping={}, storage=self.storage)
        for name, workflow in workflow_mapping.items():
            self.executor.register_workflow(name, workflow)
        self.app.state.storage = self.storage
        self.app.state.executor = self.executor
        self._register_routes()

    def _register_routes(self):
        def handle_task_exception(task):
            try:
                task.result()
            except Exception as e:
                print(f"Background workflow task failed: {e}")

        @self.app.post("/workflow")
        async def start_workflow(req: WorkflowRequest, request: Request):
            executor = request.app.state.executor
            try:
                task = asyncio.create_task(executor.execute_workflow(req.workflow_id, req.workflow_name, req.input))
                task.add_done_callback(handle_task_exception)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return {"status": "started", "workflow_id": req.workflow_id}

        @self.app.get("/workflows")
        async def list_workflows(request: Request):
            executor = request.app.state.executor
            active_workflows = await executor.get_workflows()
            return active_workflows

        @self.app.get("/workflow/{workflow_id}")
        async def get_workflow(workflow_id: str, request: Request):
            executor = request.app.state.executor
            try:
                status = await executor.get_workflow_status(workflow_id)
                return {"workflow_id": workflow_id, "status": status}
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
