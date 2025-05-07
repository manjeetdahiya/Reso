# runner.py
import asyncio
from context import WorkflowContext
from test_workflow import test_workflow

async def run_workflow(workflow_id):
    context = WorkflowContext(workflow_id)
    result = await test_workflow(context)
    print(f"Workflow {workflow_id} completed with result: {result}")

if __name__ == "__main__":
    asyncio.run(run_workflow("wf-001"))
