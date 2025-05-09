import json
import hashlib
from src.storage.storage import Storage

class WorkflowContext:
    def __init__(self, workflow_id, storage):
        self.workflow_id = workflow_id
        self.storage = storage

    def _step_key(self, fn_name, kwargs):
        hash_input = fn_name + json.dumps(kwargs, sort_keys=True)
        return fn_name + '-' + hashlib.md5(hash_input.encode()).hexdigest()

    async def call(self, activity_fn, **kwargs):
        step_id = self._step_key(activity_fn.__name__, kwargs)
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            print(f"[{self.workflow_id}] {activity_fn.__name__} - Skipped")
            return cached_result
        print(f"[{self.workflow_id}] {activity_fn.__name__} - Running")
        result = await activity_fn(**kwargs)
        self.storage.save_checkpoint(self.workflow_id, step_id, result)
        return result

    def set_status(self, status):
        self.storage.set_status(self.workflow_id, status)

    def get_status(self):
        return self.storage.get_status(self.workflow_id)
