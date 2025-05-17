import json
import hashlib
from src.storage.storage import Storage
import logging
import asyncio
from src.executor.executor import Executor

logging.basicConfig(level=logging.DEBUG, format='RESO LOG: %(asctime)s - %(levelname)s - %(message)s')

class WorkflowContext:
    def __init__(self, workflow_id, storage, executor):
        self.workflow_id = workflow_id
        self.storage = storage
        self.executor = executor
        self.step_nr = 0

    def _step_id(self, fn_name, step_nr):
        return f'{fn_name}::{step_nr}'
    
    def _inc_and_get_step_nr(self):
        self.step_nr += 1
        return self.step_nr

    async def call(self, activity_fn, **kwargs):
        step_nr = self._inc_and_get_step_nr()
        step_id = self._step_id(activity_fn.__name__, step_nr)
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            logging.debug(f"[{self.workflow_id}] {activity_fn.__name__} step_id: {step_id} - Skipped")
            return cached_result['result']
        logging.debug(f"[{self.workflow_id}] {activity_fn.__name__} step_id: {step_id} - Running")
        result = await activity_fn(**kwargs)
        self.storage.save_checkpoint(self.workflow_id, step_id, result)
        return result

    def submit_workflow(self, workflow_name, input):
        self.storage.set_status(self.workflow_id, "SUBMITTED")
        self.storage.set_workflow_info(self.workflow_id, workflow_name, input)

    def set_status(self, status):
        self.storage.set_status(self.workflow_id, status)

    def get_status(self):
        return self.storage.get_status(self.workflow_id)

    def set_result(self, result):
        self.storage.set_result(self.workflow_id, result)

    def get_result(self):
        return self.storage.get_result(self.workflow_id)

    def save_event_waiting(self, event_name, step_id):
        self.storage.save_event(self.workflow_id, step_id, event_name, None, "WAITING")
        
    def load_event(self, event_name, step_id):
        event = self.storage.load_event(self.workflow_id, step_id)
        if event is not None and event['event_name'] == event_name:
            return event
        return None
    
    def save_event_completion(self, event_name, event_data):
        event_list = self.storage.find_event_logs(self.workflow_id, event_name)
        if event_list is not None:
            for event in event_list:
                if event['event_name'] == event_name and event['state'] == "WAITING":
                    self.storage.save_event(self.workflow_id, event['step_id'], event_name, event_data, "COMPLETED")
                    return True
        else:
            return False

    async def wait_for_event(self, event_name):
        step_nr = self._inc_and_get_step_nr()
        step_id = self._step_id('wait_for_event.event_name', step_nr)
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            logging.debug(f"[{self.workflow_id}] {step_id} - Skipped")
            return cached_result['result']
        
        event = self.load_event(event_name, step_id)
        if event is not None and event['state'] == "COMPLETED":
            logging.debug(f"[{self.workflow_id}] {step_id} - Event found in storage")
            event_data = event['event_data']
        else:
            logging.debug(f"[{self.workflow_id}] wait_for_event: {event_name}")
            self.save_event_waiting(event_name, step_id)
            event_data = await self.suspend_until_event(event_name)
        
        self.storage.save_checkpoint(self.workflow_id, step_id, event_data)

    async def suspend_until_event(self, event_name):
        logging.debug(f"[{self.workflow_id}] Suspending until event: {event_name}")
        future = asyncio.Future()

        if self.workflow_id not in self.executor.event_registry:
            self.executor.event_registry[self.workflow_id] = {}
        self.executor.event_registry[self.workflow_id][event_name] = future
        self.set_status("WAITING")
        value = await future
        return value
