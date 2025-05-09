import json
import hashlib
import httpx

class WorkflowContext:
    def __init__(self, workflow_id, storage_api_url):
        self.workflow_id = workflow_id
        self.storage_api_url = storage_api_url

    async def _get_checkpoint(self, step_id):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.storage_api_url}/storage/{self.workflow_id}/{step_id}")
            if resp.status_code == 200:
                return resp.json()
            return None

    async def _save_checkpoint(self, step_id, result):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.storage_api_url}/storage/{self.workflow_id}/{step_id}",
                json={"result": result}
            )

    async def _set_status(self, status):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.storage_api_url}/storage/{self.workflow_id}/status",
                json={"status": status}
            )

    async def _get_status(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.storage_api_url}/storage/{self.workflow_id}/status")
            if resp.status_code == 200:
                return resp.json().get("status")
            return None

    def _step_key(self, fn_name, kwargs):
        hash_input = fn_name + json.dumps(kwargs, sort_keys=True)
        return fn_name + '-' + hashlib.md5(hash_input.encode()).hexdigest()

    async def call(self, activity_fn, **kwargs):
        step_id = self._step_key(activity_fn.__name__, kwargs)
        cached_result = await self._get_checkpoint(step_id)
        if cached_result is not None:
            print(f"[{self.workflow_id}] {activity_fn.__name__} - Skipped")
            return cached_result
        print(f"[{self.workflow_id}] {activity_fn.__name__} - Running")
        result = await activity_fn(**kwargs)
        await self._save_checkpoint(step_id, result)
        return result

    async def set_status(self, status):
        await self._set_status(status)

    async def get_status(self):
        return await self._get_status()
