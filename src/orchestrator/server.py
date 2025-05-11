from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.orchestrator.orchestrator import Orchestrator

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict = {}

class ExecutorRegisterRequest(BaseModel):
    executor_url: str

class WorkflowRegisterRequest(BaseModel):
    executor_url: str
    workflow_name: str

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
async def register_executor(req: ExecutorRegisterRequest):
    orchestrator = app.state.orchestrator
    if req.executor_url in orchestrator.executors_map:
        raise HTTPException(status_code=400, detail="Executor already registered")
    orchestrator.register_executor(req.executor_url)
    return {"status": "registered", "executor_url": req.executor_url}

@app.post("/register_workflow")
async def register_workflow(req: WorkflowRegisterRequest):
    orchestrator = app.state.orchestrator
    if req.executor_url not in orchestrator.executors_map:
        raise HTTPException(status_code=404, detail="Executor not found")
    if req.workflow_name in orchestrator.executors_map[req.executor_url]["workflows"]:
        raise HTTPException(status_code=400, detail="Workflow already registered")
    orchestrator.register_workflow(req.executor_url, req.workflow_name)
    return {"status": "workflow registered", "executor_url": req.executor_url, "workflow_name": req.workflow_name}

@app.get("/executors")
async def list_executors():
    orchestrator = app.state.orchestrator
    return {"executors": dict(orchestrator.executors_map)}
