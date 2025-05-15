import json
from pathlib import Path

class Storage:
    def __init__(self, checkpoint_dir=".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_checkpoint_path(self, workflow_id, checkpoint_id):
        workflow_dir = self.checkpoint_dir / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)
        return workflow_dir / f"{checkpoint_id}.json"

    def load_checkpoint(self, workflow_id, step_id):
        path = self.get_checkpoint_path(workflow_id, step_id)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def save_checkpoint(self, workflow_id, step_id, result):
        with open(self.get_checkpoint_path(workflow_id, step_id), "w") as f:
            json.dump({'workflow_id': workflow_id, 'step_id': step_id, 'result': result}, f)

    def set_status(self, workflow_id, status):
        workflow_dir = self.checkpoint_dir / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)
        path = workflow_dir / "status.json"
        with open(path, "w") as f:
            json.dump({"status": status}, f)

    def get_status(self, workflow_id):
        workflow_dir = self.checkpoint_dir / workflow_id
        path = workflow_dir / "status.json"
        if path.exists():
            with open(path) as f:
                return json.load(f).get("status")
        return None

    def list_workflows(self):
        workflows = []
        if not self.checkpoint_dir.exists():
            return workflows
        for wf_dir in self.checkpoint_dir.iterdir():
            if wf_dir.is_dir():
                status = self.get_status(wf_dir.name)
                workflows.append({
                    "workflow_id": wf_dir.name,
                    "status": status
                })
        return workflows

    def set_config(self, config: dict):
        checkpoint_dir = config.get("checkpoint_dir")
        if checkpoint_dir is not None:
            from pathlib import Path
            self.checkpoint_dir = Path(checkpoint_dir)

    def get_config(self):
        return {
            "checkpoint_dir": str(self.checkpoint_dir)
        }

    def set_workflow_info(self, workflow_id, workflow_name, input):
        workflow_dir = self.checkpoint_dir / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)
        path = workflow_dir / "info.json"
        with open(path, "w") as f:
            json.dump({
                "workflow_name": workflow_name,
                "input": input
            }, f)
    
    def get_workflow_info(self, workflow_id):
        workflow_dir = self.checkpoint_dir / workflow_id
        path = workflow_dir / "info.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None
    
    