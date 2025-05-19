import asyncio

async def get_email(user_id):
    await asyncio.sleep(5)
    return f"{user_id}@mail.com"

async def send_email(email_id):
    await asyncio.sleep(5)
    return True

async def my_workflow(ctx, user_id):
    email_id = await ctx.call(get_email, user_id)
    result = await ctx.call(send_email, email_id)
    return result
