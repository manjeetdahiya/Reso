* Sleep?
* API calls return and error flags
* automated testing
* impl getter/setter
* Implement: Hibernation functions to push to disk
* How are worflow bugs handled?
* Check: What happens when executor disconnects?
* all the internal Ops should be atomic.

Done
---
* Implement: wait_for_event
* Storing events for replay?
* there could be parallel waiting for events in a wf. perhaps, executor should set waiting for event in events/ and orch should match and write there
* The log should be step name for debuggability
