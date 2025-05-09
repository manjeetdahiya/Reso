import asyncio
from src.orchestrator.context import WorkflowContext
from pathlib import Path
import json

class WorkflowsManager:
    def __init__(self, workflow_mapping, storage_api_url):
        self.workflow_mapping = workflow_mapping
        self.storage_api_url = storage_api_url

    def register_workflow(self, workflow_name, workflow_func):
        self.workflow_mapping[workflow_name] = workflow_func

    async def run_workflow(self, workflow_id, workflow_name=None, input=None):
        context = WorkflowContext(workflow_id, **(input or {}), storage_api_url=self.storage_api_url)
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
        context = WorkflowContext(workflow_id, storage_api_url=self.storage_api_url)
        status = context.get_status()
        if status is None:
            raise Exception(f"Workflow {workflow_id} not found")
        return status
    
    async def get_workflows(self):
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.storage_api_url}/storage/list")
            if resp.status_code == 200:
                return resp.json()
            return []
    
    async def get_active_workflows(self):
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.storage_api_url}/storage/list")
            if resp.status_code == 200:
                workflows = resp.json()
                return [w["workflow_id"] for w in workflows if w.get("status") == "active"]
            return []
