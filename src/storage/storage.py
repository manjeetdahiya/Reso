import json
from pathlib import Path

class Storage:
    def __init__(self, checkpoint_dir=".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_workflow_path(self, workflow_id):
        workflow_path = self.checkpoint_dir / workflow_id
        workflow_path.mkdir(parents=True, exist_ok=True)
        return workflow_path
    
    def get_steps_path(self, workflow_id):
        dir = self.get_workflow_path(workflow_id) / "steps"
        dir.mkdir(parents=True, exist_ok=True)
        return dir

    def get_events_path(self, workflow_id):
        dir = self.get_workflow_path(workflow_id) / "events"
        dir.mkdir(parents=True, exist_ok=True)
        return dir
    
    def get_step_path(self, workflow_id, seq_number):
        return self.get_steps_path(workflow_id) / f"{seq_number}.json"

    def get_event_path(self, workflow_id, seq_number):
        return self.get_events_path(workflow_id) / f"{seq_number}.json"

    def get_status_path(self, workflow_id):
        return self.get_workflow_path(workflow_id) / "status.json"

    def get_result_path(self, workflow_id):
        return self.get_workflow_path(workflow_id) / "result.json"

    def get_info_path(self, workflow_id):
        return self.get_workflow_path(workflow_id) / "info.json"

    def read_json(self, path):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def write_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f)
   
    def find_step_sequence_number(self, workflow_id):
        dir = self.get_steps_path(workflow_id)
        if not dir.exists():
            return 0
        files = sorted([int(f.stem) for f in dir.iterdir() if f.is_file()])
        return files[-1] if len(files) > 0 else 0

    def find_event_sequence_number(self, workflow_id):
        dir = self.get_events_path(workflow_id)
        if not dir.exists():
            return 0
        files = sorted([int(f.stem) for f in dir.iterdir() if f.is_file()])
        return files[-1] if len(files) > 0 else 0

    def load_checkpoint(self, workflow_id, seq_number):
        path = self.get_step_path(workflow_id, seq_number)
        self.read_json(path)

    def save_checkpoint(self, workflow_id, seq_number, result):
        self.write_json(self.get_step_path(workflow_id, seq_number), {
            'workflow_id': workflow_id,
            'seq_number': seq_number,
            'result': result
        })

    def save_event(self, workflow_id, seq_number, event_name, event_data):
        self.write_json(self.get_event_path(workflow_id, seq_number), {
            'workflow_id': workflow_id,
            'seq_number': seq_number,
            'event_name': event_name,
            'event_data': event_data
        })

    def load_event(self, workflow_id, seq_number):
        path = self.get_event_path(workflow_id, seq_number)
        return self.read_json(path)

    def set_status(self, workflow_id, status):
        path = self.get_status_path(workflow_id)
        self.write_json(path, {"status": status})

    def get_status(self, workflow_id):
        path = self.get_status_path(workflow_id)
        return self.read_json(path).get("status")

    def set_result(self, workflow_id, result):
        path = self.get_result_path(workflow_id)
        self.write_json(path, {"result": result})

    def get_result(self, workflow_id):
        path = self.get_result_path(workflow_id)
        return self.read_json(path).get("result")

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
        return {"checkpoint_dir": str(self.checkpoint_dir)}

    def set_workflow_info(self, workflow_id, workflow_name, input):
        path = self.get_info_path(workflow_id)
        self.write_json(path, {
            "workflow_name": workflow_name,
            "input": input
        })
    
    def get_workflow_info(self, workflow_id):
        path = self.get_info_path(workflow_id)
        return self.read_json(path)
