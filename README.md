# Reso: Resumable Orchestration

A lightweight, durable workflow orchestrator where **workflows are written in Python itself**. There is no YAML, JSON or custom DSL: a workflow is a plain async Python function, so you get normal `if`/`else`, loops, `try`/`except`, variables and your existing libraries and tooling. Every step is checkpointed, so a workflow can be resumed (replayed) after a crash, hibernation or executor restart.

- Workflow-as-code: workflows are described in Python, not a separate language
- Microservice orchestration
- Async processing
- Durable: step results and events are checkpointed to storage
- Scalable: multiple executors can run on multiple machines

## Project Structure

- **src/orchestrator**: Workflow orchestration, the HTTP API (FastAPI) and workflow management logic.
- **src/executor**: Runs workflows and exposes a small server the orchestrator talks to. There can be many executors.
- **src/storage**: Storage layer (`BaseStorage` interface plus a default implementation) for checkpoints, events, workflows and config.
- **src/models.py**: Shared models (`Workflow`, `Event`, ...).
- **examples**: Sample workflows and an example executor.
- **doc/concepts.md**: Workflow states, step IDs and step numbers.

## Writing a workflow

A workflow is an ordinary async Python function that takes a context `ctx` and its inputs. The control flow is just Python; use `ctx` for anything that must be durable:

```python
async def my_workflow_2(ctx):
    await ctx.call(task1)                      # checkpointed step
    await ctx.wait_for_event('user_approval')  # pause until an external event arrives
    await ctx.call(task2)
    await ctx.sleep(5)                         # durable sleep
    await ctx.call(task3)
```

| Method | Purpose |
| --- | --- |
| `ctx.call(fn, *args, **kwargs)` | Run a step; its result is checkpointed and reused on replay |
| `ctx.wait_for_event(name)` | Suspend until the named event is sent to the workflow |
| `ctx.sleep(seconds)` | Durable sleep |
| `ctx.submit_workflow(name, input)` | Start another workflow |

Register workflows on an executor (see [examples/my_executor.py](examples/my_executor.py)):

```python
executor = Executor(orchestrator_server='http://localhost:8008', executor_server='http://localhost:8009')
executor.register_workflow('my_workflow', my_workflow)
```

## Running

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/) (dependencies are in `pyproject.toml`).

```sh
uv sync

# 1. Orchestrator (port 8008)
sh scripts/start_reso_server.sh

# 2. Executor with example workflows (port 8009)
sh scripts/start_executor_server.sh
```

## Orchestrator API

| Endpoint | Description |
| --- | --- |
| `POST /workflow` | Start a workflow (`workflow_id`, `workflow_name`, `input`) |
| `GET /workflows` | List workflows |
| `GET /workflow/{workflow_id}` | Get workflow status |
| `POST /event` | Send an event to a waiting workflow (`workflow_id`, `event_name`, `event_data`) |
| `POST /register_executor` | Register an executor |
| `POST /register_workflow` | Register a workflow on an executor |
| `GET /executors` | List registered executors |
| `GET /storage_config` | Get storage configuration |

Example:

```sh
curl -X POST localhost:8008/workflow -H 'Content-Type: application/json' \
  -d '{"workflow_id": "wf1", "workflow_name": "my_workflow", "input": {"user_id": "42"}}'
```

## Status

Early development. See [TODO.md](TODO.md) for planned work.

## License

Released under the [MIT License](LICENSE).
