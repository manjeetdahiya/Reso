from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from .storage import Storage
import os
from pathlib import Path
import json

app = FastAPI()
storage = Storage()

class CheckpointData(BaseModel):
    result: dict

class StatusData(BaseModel):
    status: str

@app.get("/storage/{workflow_id}/{checkpoint_id}")
def get_checkpoint(workflow_id: str, checkpoint_id: str):
    data = storage.load_checkpoint(workflow_id, checkpoint_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return data

@app.post("/storage/{workflow_id}/{checkpoint_id}")
def save_checkpoint(workflow_id: str, checkpoint_id: str, data: CheckpointData):
    storage.save_checkpoint(workflow_id, checkpoint_id, data.result)
    return {"message": "Checkpoint saved"}

@app.get("/storage/{workflow_id}/status")
def get_status(workflow_id: str):
    status = storage.get_status(workflow_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    return {"status": status}

@app.post("/storage/{workflow_id}/status")
def set_status(workflow_id: str, data: StatusData):
    storage.set_status(workflow_id, data.status)
    return {"message": "Status set"}

@app.get("/storage/list")
def list_workflows():
    base_dir = storage.checkpoint_dir
    workflows = []
    if not base_dir.exists():
        return workflows
    for wf_dir in base_dir.iterdir():
        if wf_dir.is_dir():
            status = None
            status_file = wf_dir / "status.json"
            if status_file.exists():
                with open(status_file) as f:
                    try:
                        status = (json.load(f) or {}).get("status")
                    except Exception:
                        status = None
            workflows.append({
                "workflow_id": wf_dir.name,
                "status": status
            })
    return workflows
