from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Gemini Chatbot API")

@app.on_event("startup")
async def startup():
    os.environ.setdefault("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

ORDERS_API_URL = "http://localhost:8001"

agent = Agent(
    'google-gla:gemini-2.5-flash',
    system_prompt="You are an order assistant. Use the available tools to search orders and confirm them when requested."
)

@agent.tool_plain
def search_orders(status: str = None) -> str:
    """Search for orders. Optionally filter by status (pending, confirmed)."""
    try:
        params = {"status": status} if status else {}
        response = requests.get(f"{ORDERS_API_URL}/orders", params=params)
        orders = response.json()
        if not orders:
            return "No orders found."
        result = "\n".join([f"Order {o['id']}: {o['item']} - ${o['price']} ({o['status']})" for o in orders])
        return result
    except:
        return "Error connecting to orders API"

@agent.tool_plain
def get_order_details(order_id: str) -> str:
    """Get details of a specific order by order ID."""
    try:
        response = requests.get(f"{ORDERS_API_URL}/orders/{order_id}")
        order = response.json()
        if order["id"] == "NOT_FOUND":
            return f"Order {order_id} not found."
        return f"Order {order['id']}: {order['item']} - ${order['price']} (Status: {order['status']})"
    except:
        return "Error connecting to orders API"

@agent.tool_plain
def confirm_order(order_id: str) -> str:
    """Confirm an order by order ID."""
    try:
        response = requests.post(f"{ORDERS_API_URL}/orders/{order_id}/confirm")
        result = response.json()
        return result["message"]
    except:
        return "Error connecting to orders API"

@app.get("/")
async def root():
    return {"message": "Gemini Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await agent.run(request.message)
    return ChatResponse(response=result.output)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)