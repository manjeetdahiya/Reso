from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import uvicorn
from src.orchestrator.workflows_manager import WorkflowsManager
from src.orchestrator.test_workflow import test_workflow
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from src.storage.storage import Storage

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict

class WorkflowInfo(BaseModel):
    workflow_id: str
    tasks: List[str]
    status: str

# Instantiate and register workflows
storage = Storage(checkpoint_dir="checkpoints")
workflows_manager = WorkflowsManager(workflow_mapping={}, storage=storage                                     )
workflows_manager.register_workflow('test_workflow', test_workflow)

@app.post("/workflow")
async def start_workflow(req: WorkflowRequest):
    task = asyncio.create_task(workflows_manager.run_workflow(req.workflow_id, req.workflow_name, req.input))
    return {"status": "started", "workflow_id": req.workflow_id}

@app.get("/workflows")
async def list_workflows():
    active_workflows =  await workflows_manager.get_workflows()
    return active_workflows

@app.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):
    return await workflows_manager.get_workflow_status(workflow_id)
