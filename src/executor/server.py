from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio

class WorkflowRequest(BaseModel):
    workflow_id: str

class Server:
    def __init__(self, executor):
        self.executor = executor
        self.app = FastAPI()
        self._register_routes()

    def _register_routes(self):
        def handle_task_exception(task):
            try:
                task.result()
            except Exception as e:
                print(f"Background workflow task failed: {e}")

        @self.app.post("/workflow")
        async def start_workflow(req: WorkflowRequest, request: Request):
            try:
                task = asyncio.create_task(self.executor.execute_workflow(req.workflow_id))
                task.add_done_callback(handle_task_exception)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return {"status": "started", "workflow_id": req.workflow_id}

        # these don't make sense in the executor...should be in the orchestrator
        @self.app.get("/workflows")
        async def list_workflows(request: Request):
            active_workflows = await self.executor.get_workflows()
            return active_workflows

        @self.app.get("/workflow/{workflow_id}")
        async def get_workflow(workflow_id: str, request: Request):
            try:
                status = await self.executor.get_workflow_status(workflow_id)
                return {"workflow_id": workflow_id, "status": status}
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
