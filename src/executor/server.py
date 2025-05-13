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

        @self.app.on_event("startup")
        async def startup_event():
            print(f"Starting executor server...")
            # Any startup logic can be added here
            pass
