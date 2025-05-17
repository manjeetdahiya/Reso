## Workflow states

### Logical state
    1. Submitted
    2. Running
    3. Waiting
    4. Failed
    4. Completed

### Execution state
    1. Active         -   worker available and running
    2. Hibernated     -   worker not available or hibernated


## Step ID and Step Number

* **Step number** is a unique number associated with each call or wait_for_event. This number remains same
                    at the time of reply also.
* **Step ID** is function name concatenated with step number
