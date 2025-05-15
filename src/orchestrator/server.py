from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.orchestrator.orchestrator import Orchestrator
import httpx
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict = {}

class ExecutorRegisterRequest(BaseModel):
    executor_server: str

class WorkflowRegisterRequest(BaseModel):
    executor_server: str
    workflow_name: str

class WrokflowEventRequest(BaseModel):
    workflow_id: str
    event_name: str
    value: str

@app.on_event("startup")
async def startup_event():
    app.state.orchestrator = Orchestrator()

@app.post("/workflow")
def start_workflow(req: WorkflowRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    task = orchestrator.start_workflow(req.workflow_id, req.workflow_name, req.input)
    return {"status": "started", "workflow_id": req.workflow_id}

@app.get("/workflows")
async def list_workflows(request: Request):
    orchestrator = request.app.state.orchestrator
    active_workflows = await orchestrator.get_workflows()
    return active_workflows

@app.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    orchestrator = request.app.state.orchestrator
    try:
        status = await orchestrator.get_workflow_status(workflow_id)
        return {"workflow_id": workflow_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/storage_config")
async def get_storage_config():
    return app.state.orchestrator.storage.get_config()

@app.post("/register_executor")
def register_executor(req: ExecutorRegisterRequest):
    orchestrator = app.state.orchestrator
    orchestrator.register_executor(req.executor_server)
    return {"status": "registered", "executor_server": req.executor_server}

@app.post("/register_workflow")
async def register_workflow(req: WorkflowRegisterRequest):
    orchestrator = app.state.orchestrator
    if req.executor_server not in orchestrator.executors:
        raise HTTPException(status_code=404, detail="Executor not found")
    orchestrator.register_workflow(req.executor_server, req.workflow_name)
    return {"status": "workflow registered", "executor_server": req.executor_server, "workflow_name": req.workflow_name}

@app.get("/executors")
async def list_executors():
    orchestrator = app.state.orchestrator
    return {"executors": dict(orchestrator.executors)}

@app.post("/event")
async def send_event(req: WrokflowEventRequest):
    try:
        orchestrator = app.state.orchestrator
        executor_server = orchestrator.get_executor_for_workflow_id(req.workflow_id)
        if executor_server:
            res = httpx.post(f"{executor_server}/event", json=req.dict())  # Remove await
        else:
            raise HTTPException(status_code=404, detail="Executor not found for this workflow")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "event sent", "workflow_id": req.workflow_id, 'result': res.text}