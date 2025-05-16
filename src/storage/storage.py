import json
from pathlib import Path

class Storage:
    def __init__(self, checkpoint_dir=".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_workflow_log_path(self, workflow_id):
        workflow_path = self.checkpoint_dir / workflow_id
        workflow_path.mkdir(parents=True, exist_ok=True)
        return workflow_path
    
    def get_checkpoint_path(self, workflow_id, seq_number):
        steps_dir = self.get_workflow_log_path(workflow_id) / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)
        return steps_dir / f"{seq_number}.json"

    def get_event_path(self, workflow_id, seq_number):
        events_dir = self.get_workflow_log_path(workflow_id) / "events"
        events_dir.mkdir(parents=True, exist_ok=True)
        return events_dir / f"{seq_number}.json"

    def find_step_sequence_number(self, workflow_id):
        dir = self.get_workflow_log_path(workflow_id) / "steps"
        if not dir.exists():
            return 0
        files = sorted([int(f.stem) for f in dir.iterdir() if f.is_file()])
        return files[-1] if len(files) > 0 else 0

    def find_event_sequence_number(self, workflow_id):
        dir = self.get_workflow_log_path(workflow_id) / "events"
        if not dir.exists():
            return 0
        files = sorted([int(f.stem) for f in dir.iterdir() if f.is_file()])
        return files[-1] if len(files) > 0 else 0

    def load_checkpoint(self, workflow_id, seq_number):
        path = self.get_checkpoint_path(workflow_id, seq_number)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def save_event(self, workflow_id, seq_number, event_name, event_data):
        with open(self.get_event_path(workflow_id, seq_number), "w") as f:
            json.dump({'workflow_id': workflow_id, 'seq_number': seq_number, 'event_name': event_name, 'event_data': event_data}, f)

    def load_event(self, workflow_id, seq_number):
        path = self.get_event_path(workflow_id, seq_number)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def save_checkpoint(self, workflow_id, seq_number, result):
        with open(self.get_checkpoint_path(workflow_id, seq_number), "w") as f:
            json.dump({'workflow_id': workflow_id, 'seq_number': seq_number, 'result': result}, f)

    def set_status(self, workflow_id, status):
        workflow_dir = self.get_workflow_log_path(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        path = workflow_dir / "status.json"
        with open(path, "w") as f:
            json.dump({"status": status}, f)

    def get_status(self, workflow_id):
        workflow_dir = self.get_workflow_log_path(workflow_id)
        path = workflow_dir / "status.json"
        if path.exists():
            with open(path) as f:
                return json.load(f).get("status")
        return None

    def set_result(self, workflow_id, result):
        workflow_dir = self.get_workflow_log_path(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        path = workflow_dir / "result.json"
        with open(path, "w") as f:
            json.dump({"result": result}, f)

    def get_result(self, workflow_id):
        workflow_dir = self.get_workflow_log_path(workflow_id)
        path = workflow_dir / "result.json"
        if path.exists():
            with open(path) as f:
                return json.load(f).get("result")
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
        workflow_dir = self.get_workflow_log_path(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        path = workflow_dir / "info.json"
        with open(path, "w") as f:
            json.dump({
                "workflow_name": workflow_name,
                "input": input
            }, f)
    
    def get_workflow_info(self, workflow_id):
        workflow_dir = self.get_workflow_log_path(workflow_id)
        path = workflow_dir / "info.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None
    
    