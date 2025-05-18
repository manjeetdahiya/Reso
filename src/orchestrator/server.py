from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.orchestrator.orchestrator import Orchestrator
from src.executor.server import WorkflowEventRequest
import httpx
import logging

logger = logging.getLogger('reso')
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('RESO %(levelname)s: %(message)s'))
    logger.addHandler(handler)

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

@app.on_event("startup")
async def startup_event():
    app.state.orchestrator = Orchestrator()

def build_workflow_status_response(workflow_id, orchestrator):
    status = orchestrator.storage.get_status(workflow_id)
    ret = {
        "workflow_id": workflow_id,
        "status": status,
        "executor": orchestrator.get_executor_for_workflow_id(workflow_id)
    }
    if status == "COMPLETED":
        result = orchestrator.storage.get_result(workflow_id)
        ret["result"] = result
    return ret

@app.post("/workflow")
def start_workflow(req: WorkflowRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    try:
        orchestrator.start_workflow(req.workflow_id, req.workflow_name, req.input)
        return build_workflow_status_response(req.workflow_id, orchestrator)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workflows")
async def list_workflows(request: Request):
    orchestrator = request.app.state.orchestrator
    active_workflows = await orchestrator.get_workflows()
    return active_workflows

@app.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    orchestrator = request.app.state.orchestrator
    try:
        return build_workflow_status_response(workflow_id, orchestrator)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/storage_config")
async def get_storage_config(request: Request):
    orchestrator = request.app.state.orchestrator
    return orchestrator.storage.get_config()

@app.post("/register_executor")
def register_executor(req: ExecutorRegisterRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    orchestrator.register_executor(req.executor_server)
    return {"status": "registered", "executor_server": req.executor_server}

@app.post("/register_workflow")
async def register_workflow(req: WorkflowRegisterRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    if req.executor_server not in orchestrator.executors:
        raise HTTPException(status_code=404, detail="Executor not found")
    orchestrator.register_workflow(req.executor_server, req.workflow_name)
    return {"status": "workflow registered", "executor_server": req.executor_server, "workflow_name": req.workflow_name}

@app.get("/executors")
async def list_executors(request: Request):
    orchestrator = request.app.state.orchestrator
    return {"executors": dict(orchestrator.executors)}

@app.post("/event")
async def send_event(req: WorkflowEventRequest, request: Request):
    try:
        orchestrator = request.app.state.orchestrator
        stored = orchestrator.store_event(req.workflow_id, req.event_name, req.event_data)
        if not stored:
            raise HTTPException(status_code=404, detail="No waiting event found")
        executor_server = orchestrator.get_executor_for_workflow_id(req.workflow_id)
        if executor_server:
            res = httpx.post(f"{executor_server}/event", json=req.dict())
        else:
            raise HTTPException(status_code=404, detail="Executor not found for this workflow")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "event sent", "workflow_id": req.workflow_id, 'result': res.text}