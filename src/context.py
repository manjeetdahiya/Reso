# context.py
import json
import hashlib
from pathlib import Path

class WorkflowContext:
    def __init__(self, workflow_id, checkpoint_dir="checkpoints"):
        self.workflow_id = workflow_id
        self.checkpoint_dir = Path(checkpoint_dir) / workflow_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _step_key(self, fn_name, kwargs):
        hash_input = fn_name + json.dumps(kwargs, sort_keys=True)
        return fn_name + '-' + hashlib.md5(hash_input.encode()).hexdigest()

    def _get_checkpoint_path(self, checkpoint_id):
        return self.checkpoint_dir / f"{checkpoint_id}.json"

    def _load_checkpoint(self, step_id):
        path = self._get_checkpoint_path(step_id)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def _save_checkpoint(self, step_id, result):
        with open(self._get_checkpoint_path(step_id), "w") as f:
            json.dump(result, f)

    async def call(self, activity_fn, **kwargs):
        step_id = self._step_key(activity_fn.__name__, kwargs)

        cached_result = self._load_checkpoint(step_id)
        if cached_result is not None:
            print(f"[{self.workflow_id}] {activity_fn.__name__} - Skipped")
            return cached_result

        print(f"[{self.workflow_id}] {activity_fn.__name__} - Running")
        result = await activity_fn(**kwargs)
        self._save_checkpoint(step_id, result)
        return result
