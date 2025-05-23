import asyncio

async def task1():
    await asyncio.sleep(5)

async def task2():
    await asyncio.sleep(5)

async def task3():
    await asyncio.sleep(5)

async def my_workflow_2(ctx):
    await ctx.call(task1)
    await ctx.wait_for_event('user_approval')
    await ctx.call(task2)
    await ctx.sleep(5)   # durable sleep
    await ctx.call(task3)
