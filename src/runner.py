# runner.py
import asyncio
from context import WorkflowContext
from test_workflow import test_workflow

workflow_mapping = {'test_workflow': test_workflow}

async def run_workflow(workflow_id, workflow_name=None, input=None):
    context = WorkflowContext(workflow_id, **input)
    
    assert workflow_name in workflow_mapping, f"Workflow {workflow_name} not found"
    result = await workflow_mapping[workflow_name](context)
    
    print(f"Workflow {workflow_id} completed with result: {result}")

if __name__ == "__main__":
    asyncio.run(run_workflow("wf-001"))
