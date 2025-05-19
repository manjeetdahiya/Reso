* event Class
* API calls return and error flags
* same workflow id can be repeated??
* automated testing
* impl getter/setter
* Implement: Hibernation functions to push to disk
* How are worflow bugs handled?
* Check: What happens when executor disconnects?
* all the internal Ops should be atomic.
* retries -- why do I need this? can't one impl this in the step?
* activity? -- again why? focus is on workflows only

Done
---
* Implement: wait_for_event
* Storing events for replay?
* there could be parallel waiting for events in a wf. perhaps, executor should set waiting for event in events/ and orch should match and write there
* The log should be step name for debuggability
* Sleep?
