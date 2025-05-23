from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any, Dict

class WorkflowState(Enum):
    SUBMITTED = 'SUBMITTED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    WAITING = 'WAITING'

class EventState(Enum):
    WAITING = 'WAITING'
    COMPLETED = 'COMPLETED'

class Event(BaseModel):
    workflow_id: str
    step_id: str
    event_name: str
    event_data: Optional[Any] = None
    state: EventState
    event_meta: Optional[Dict[str, Any]] = None

class Workflow(BaseModel):
    workflow_id: str
    workflow_name: str
    input: Optional[Dict[str, Any]] = None
    state: Optional[WorkflowState] = None
    result: Optional[Any] = None
