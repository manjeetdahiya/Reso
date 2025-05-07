# services.py
import asyncio

async def task1(user_id):
    await asyncio.sleep(5)
    return {"user_id": user_id, "email": "user@example.com"}

async def task2(email):
    await asyncio.sleep(5)
    print(f"Email sent to {email}")
    return {"status": "sent"}

async def test_workflow(context):
    user = await context.call(task1, user_id="123")
    await context.call(task2, email=user["email"])
    return {"status": "complete"}
