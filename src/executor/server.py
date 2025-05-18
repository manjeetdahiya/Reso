from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio
import logging

class WorkflowRequest(BaseModel):
    workflow_id: str

class WorkflowEventRequest(BaseModel):
    workflow_id: str
    event_name: str
    event_data: str

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
        async def start_workflow(req: WorkflowRequest):
            try:
                task = asyncio.create_task(self.executor.execute_workflow(req.workflow_id))
                task.add_done_callback(handle_task_exception)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return {"status": "started", "workflow_id": req.workflow_id}
        
        @self.app.post("/event")
        async def send_event(req: WorkflowEventRequest):
            try:
                await self.executor.send_event(req.workflow_id, req.event_name, req.event_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return {"status": "event sent", "workflow_id": req.workflow_id}

        @self.app.on_event("startup")
        async def startup_event():
            asyncio.create_task(self.executor._register_workflows())
            logging.debug("Executor server started")
