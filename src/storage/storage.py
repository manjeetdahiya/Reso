from pathlib import Path
from src.models import Event, EventState, Workflow
import portalocker
from src.storage.base import BaseStorage

class Storage(BaseStorage):
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
    
    def get_step_path(self, workflow_id, step_id):
        return self.get_steps_path(workflow_id) / f"{step_id}.json"

    def get_event_path(self, workflow_id, step_id):
        return self.get_events_path(workflow_id) / f"{step_id}.json"

    def get_workflow_json_path(self, workflow_id):
        return self.get_workflow_path(workflow_id) / "workflow.json"

    def read_json(self, path):
        if path.exists():
            import json
            with open(path, "r") as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    portalocker.unlock(f)
        return None

    def write_json(self, path, data):
        import json
        from pydantic.json import pydantic_encoder
        with open(path, "w") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                json.dump(data, f, default=pydantic_encoder)
            finally:
                portalocker.unlock(f)
   
    def get_checkpoint(self, workflow_id, step_id):
        path = self.get_step_path(workflow_id, step_id)
        return self.read_json(path)

    def set_checkpoint(self, workflow_id, step_id, result):
        self.write_json(self.get_step_path(workflow_id, step_id), {
            'workflow_id': workflow_id,
            'step_id': step_id,
            'result': result
        })

    def find_event_logs(self, workflow_id, event_name):
        dir = self.get_events_path(workflow_id)
        if not dir.exists():
            return None
        ret = []
        for f in dir.iterdir():
            if f.is_file():
                event_dict = self.read_json(f)
                if event_dict and event_dict['event_name'] == event_name:
                    event = Event(**event_dict)
                    ret.append(event)
        return ret
    
    def set_event(self, event: Event):
        self.write_json(self.get_event_path(event.workflow_id, event.step_id), event.dict())

    def get_event(self, workflow_id, step_id):
        path = self.get_event_path(workflow_id, step_id)
        event_dict = self.read_json(path)
        if event_dict:
            return Event(**event_dict)
        return None

    def set_workflow(self, workflow_id, workflow_name, input, state):
        wf = Workflow(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input=input,
            state=state,
            result=None
        )
        self.write_json(self.get_workflow_json_path(workflow_id), wf.dict())

    def update_state(self, workflow_id, state, result=None):
        wf = self.get_workflow(workflow_id)
        wf.state = state
        wf.result = result
        self.write_json(self.get_workflow_json_path(workflow_id), wf.dict())

    def get_workflow(self, workflow_id):
        path = self.get_workflow_json_path(workflow_id)
        data = self.read_json(path) or {}
        return Workflow(**data)

    def list_workflows(self):
        workflows = []
        if not self.checkpoint_dir.exists():
            return workflows
        for wf_dir in self.checkpoint_dir.iterdir():
            if wf_dir.is_dir():
                wf = self.get_workflow(wf_dir.name)
                if wf is None:
                    continue
                workflows.append(wf)
        return workflows

    def set_config(self, config: dict):
        checkpoint_dir = config.get("checkpoint_dir")
        if checkpoint_dir is not None:
            from pathlib import Path
            self.checkpoint_dir = Path(checkpoint_dir)

    def get_config(self):
        return {"checkpoint_dir": str(self.checkpoint_dir)}
