# runner.py
import asyncio
from context import WorkflowContext
from test_workflow import test_workflow
from pathlib import Path
import json

class WorkflowsManager:
    def __init__(self, workflow_mapping=None):
        self.workflow_mapping = workflow_mapping

    def register_workflow(self, workflow_name, workflow_func):
        self.workflow_mapping[workflow_name] = workflow_func

    async def run_workflow(self, workflow_id, workflow_name=None, input=None):
        context = WorkflowContext(workflow_id, **(input or {}))
        assert workflow_name in self.workflow_mapping, f"Workflow {workflow_name} not found"
        try:
            context.set_status("active")
            result = await self.workflow_mapping[workflow_name](context)
            context.set_status("completed")
        except Exception:
            context.set_status("failed")
            raise
        print(f"Workflow {workflow_id} completed with result: {result}")

    async def get_workflow_status(self, workflow_id):
        context = WorkflowContext(workflow_id)
        status = context.get_status()
        if status is None:
            raise Exception(f"Workflow {workflow_id} not found")
        return status
    
    async def get_workflows(self):
        workflows = []
        checkpoints_dir = Path("checkpoints")
        if not checkpoints_dir.exists():
            return workflows
        
        for workflow_dir in checkpoints_dir.iterdir():
            if workflow_dir.is_dir():
                status_file = workflow_dir / "status.json"
                if not status_file.exists():
                    continue
                with open(status_file, 'r') as f:
                    status = json.load(f)
                workflows.append({
                    "workflow_id": workflow_dir.name,
                    "status": status.get("status"),
                })
        return workflows
    
    async def get_active_workflows(self):
        active_workflows = []
        checkpoints_dir = Path("checkpoints")
        if not checkpoints_dir.exists():
            return active_workflows
        
        for workflow_dir in checkpoints_dir.iterdir():
            if workflow_dir.is_dir():
                status_file = workflow_dir / "status.json"
                if not status_file.exists():
                    continue
                with open(status_file, 'r') as f:
                    status = json.load(f)
                if status.get("status") == "active":
                    active_workflows.append(workflow_dir.name)
        return active_workflows
