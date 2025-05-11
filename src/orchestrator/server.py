from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio
from src.storage.storage import Storage
from src.orchestrator.workflows_manager import WorkflowsManager
from src.orchestrator.orchestrator import Orchestrator

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict = {}

@app.on_event("startup")
async def startup_event():
    orchestrator = Orchestrator()
    storage = Storage()
    workflows_manager = WorkflowsManager(workflow_mapping={}, storage=storage)
    app.state.storage = storage
    app.state.workflows_manager = workflows_manager

@app.post("/workflow")
async def start_workflow(req: WorkflowRequest, request: Request):
    workflows_manager = request.app.state.workflows_manager
    task = asyncio.create_task(workflows_manager.run_workflow(req.workflow_id, req.workflow_name, req.input))
    return {"status": "started", "workflow_id": req.workflow_id}

@app.get("/workflows")
async def list_workflows(request: Request):
    workflows_manager = request.app.state.workflows_manager
    active_workflows = await workflows_manager.get_workflows()
    return active_workflows

@app.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    workflows_manager = request.app.state.workflows_manager
    try:
        status = await workflows_manager.get_workflow_status(workflow_id)
        return {"workflow_id": workflow_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/storage_config")
async def get_storage_config():
    return app.state.storage.get_config()
