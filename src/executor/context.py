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
        self.step_sequence_number = 0

    def _step_key(self, fn_name, kwargs):
        hash_input = fn_name + json.dumps(kwargs, sort_keys=True)
        return fn_name + '-' + hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_step_sequence_number(self):
        self.step_sequence_number += 1
        return self.step_sequence_number

    async def call(self, activity_fn, **kwargs):
        # step_id = self._step_key(activity_fn.__name__, kwargs)
        step_id = f"{self._get_step_sequence_number()}"
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            print(f"[{self.workflow_id}] {activity_fn.__name__} - Skipped")
            return cached_result['result']
        print(f"[{self.workflow_id}] {activity_fn.__name__} - Running")
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

    async def wait_for_event(self, event_name):
        step_name = f'wait_for_event::{event_name}'
        # step_id = self._step_key(step_name, {})
        step_id = f"{self._get_step_sequence_number()}"
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            print(f"[{self.workflow_id}] {step_name} - Skipped")
            return cached_result['result']
        logging.debug(f"[{self.workflow_id}] wait_for_event: {event_name}")
        value = await self.suspend_until_event(event_name)
        self.storage.save_checkpoint(self.workflow_id, step_id, value)

    async def suspend_until_event(self, event_name):
        logging.debug(f"[{self.workflow_id}] Suspending until event: {event_name}")
        future = asyncio.Future()

        if self.workflow_id not in self.executor.event_registry:
            self.executor.event_registry[self.workflow_id] = {}
        self.executor.event_registry[self.workflow_id][event_name] = future  #TODO multiple events of same name?

        value = await future
        return value
