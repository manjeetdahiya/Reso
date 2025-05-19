import json
import hashlib
from src.storage.storage import Storage
import logging
import asyncio
from src.executor.executor import Executor

logger = logging.getLogger("reso")

sleep_event_name = "__sleep_reso__"

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

    async def call(self, step_fn, *args, **kwargs):
        step_nr = self._inc_and_get_step_nr()
        step_id = self._step_id(step_fn.__name__, step_nr)
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            logger.debug(f"[{self.workflow_id}] {step_fn.__name__} step_id: {step_id} - Skipped")
            return cached_result['result']
        logger.debug(f"[{self.workflow_id}] {step_fn.__name__} step_id: {step_id} - Running")
        result = await step_fn(*args, **kwargs)
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

    # called by Executor
    def save_event_waiting(self, event_name, step_id, event_meta=None):
        self.storage.save_event(self.workflow_id, step_id, event_name, None, "WAITING", event_meta)
        
    # called by Orchestrator (or by Executor in case of sleep event completion)
    def save_event_completion(self, event_name, event_data):
        event_list = self.storage.find_event_logs(self.workflow_id, event_name)
        if event_list is not None:
            for event in event_list:
                if event['event_name'] == event_name and event['state'] == "WAITING":
                    self.storage.save_event(self.workflow_id, event['step_id'], event_name, event_data, "COMPLETED", event_meta=event['event_meta'])
                    return True
        else:
            return False

    async def wait_for_event(self, event_name, event_meta=None):
        step_nr = self._inc_and_get_step_nr()
        step_id = self._step_id(f'wait_for_event.{event_name}', step_nr)
        cached_result = self.storage.load_checkpoint(self.workflow_id, step_id)
        if cached_result is not None:
            logger.debug(f"[{self.workflow_id}] {step_id} - Skipped")
            return cached_result['result']
        
        event = self.storage.load_event(self.workflow_id, step_id)
        
        # event found in storage and completed. Get event data
        event_data = None
        if event is not None and event['event_name'] == event_name and event['state'] == "COMPLETED":
            logger.debug(f"[{self.workflow_id}] {step_id} - Event found in storage")
            event_data = event['event_data']
        else:
            if event:  # event found in storage but not completed, get event_meta[IMP]
                logger.debug(f"[{self.workflow_id}] {step_id} - Event found in storage, but still waiting")
                event_meta = event["event_meta"]
            else:
                logger.debug(f"[{self.workflow_id}] wait_for_event: {event_name}")
                self.save_event_waiting(event_name, step_id, event_meta)
            event_data = await self.suspend_until_event(event_name, event_meta)

        self.storage.save_checkpoint(self.workflow_id, step_id, event_data)

    async def suspend_until_event(self, event_name, event_meta):
        logger.debug(f"[{self.workflow_id}] Suspending until event: {event_name}")
        future = asyncio.Future()
        if self.workflow_id not in self.executor.event_registry:
            self.executor.event_registry[self.workflow_id] = {}
        self.executor.event_registry[self.workflow_id][event_name] = future
        self.set_status("WAITING")
        if event_name.startswith(sleep_event_name):  # event is sleep event, create a task to handle wake it
            asyncio.create_task(self.trigger_sleep_wakeup_event(event_meta['wakeup_timestamp'], event_name))
        value = await future
        self.set_status("RUNNING")
        return value

    async def trigger_sleep_wakeup_event(self, wakeup_timestamp, event_name):
        from datetime import datetime, timedelta
        wakeup_dt = datetime.fromisoformat(wakeup_timestamp)
        now_dt = datetime.now()
        if now_dt < wakeup_dt:
            sleep_duration = (wakeup_dt - now_dt).total_seconds()
            logger.debug(f"[{self.workflow_id}] Sleeping for {sleep_duration} seconds")
            await asyncio.sleep(sleep_duration)
        else:
            logger.debug(f"[{self.workflow_id}] Wakeup time already passed, skipping sleep")
        self.save_event_completion(event_name, True)
        await self.executor.send_event(self.workflow_id, event_name, True)

    async def sleep(self, seconds):
        from datetime import datetime, timedelta
        wakeup_dt = datetime.now() + timedelta(seconds=seconds)
        wakeup_ts_iso = wakeup_dt.isoformat()
        await self.wait_for_event(sleep_event_name, event_meta={"wakeup_timestamp": wakeup_ts_iso})