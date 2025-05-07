from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import uvicorn
from runner import run_workflow
import os
import json
from pathlib import Path
from typing import List, Dict, Any

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    input: dict

class WorkflowInfo(BaseModel):
    workflow_id: str
    tasks: List[str]
    status: str

@app.post("/workflow")
async def start_workflow(req: WorkflowRequest):
    task = asyncio.create_task(run_workflow(req.workflow_id, req.workflow_name, req.input))
    return {"status": "started", "workflow_id": req.workflow_id}

@app.get("/workflows")
async def list_workflows() -> Dict[str, List[WorkflowInfo]]:
    checkpoints_dir = Path("checkpoints")
    if not checkpoints_dir.exists():
        return {"workflows": []}
    
    workflow_infos = []
    for workflow_dir in checkpoints_dir.iterdir():
        if workflow_dir.is_dir():
            tasks = [f.stem for f in workflow_dir.glob("*.json")]
            workflow_info = WorkflowInfo(
                workflow_id=workflow_dir.name,
                tasks=tasks,
                status="completed" if tasks else "in_progress"
            )
            workflow_infos.append(workflow_info)
    
    return {"workflows": workflow_infos}

@app.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    workflow_dir = Path("checkpoints") / workflow_id
    if not workflow_dir.exists():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    tasks = {}
    for task_file in workflow_dir.glob("*.json"):
        with open(task_file, "r") as f:
            tasks[task_file.stem] = json.load(f)
    
    return {
        "workflow_id": workflow_id,
        "tasks": tasks,
        "status": "completed" if tasks else "in_progress"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=True)
