import asyncio

async def task1():
    await asyncio.sleep(5)

async def task2():
    await asyncio.sleep(5)

async def my_workflow(context):
    await context.call(task1)
    await context.call(task2)
