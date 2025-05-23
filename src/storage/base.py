from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from src.models import Event, Workflow

class BaseStorage(ABC):
    @abstractmethod
    def get_checkpoint(self, workflow_id: str, step_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def set_checkpoint(self, workflow_id: str, step_id: str, result: Any) -> None:
        pass

    @abstractmethod
    def find_event_logs(self, workflow_id: str, event_name: str) -> Optional[List[Event]]:
        pass

    @abstractmethod
    def set_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def get_event(self, workflow_id: str, step_id: str) -> Optional[Event]:
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Workflow:
        pass

    @abstractmethod
    def set_workflow(self, workflow_id: str, workflow_name: str, input: Dict, state: Any) -> None:
        pass

    @abstractmethod
    def update_state(self, workflow_id: str, state: Any, result: Any = None) -> None:
        pass

    @abstractmethod
    def list_workflows(self) -> List[Workflow]:
        pass

    @abstractmethod
    def set_config(self, config: dict) -> None:
        pass

    @abstractmethod
    def get_config(self) -> dict:
        pass
