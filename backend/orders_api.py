from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Mock Orders API")

@app.on_event("startup")
async def startup():
    pass

# Mock orders database
ORDERS = {
    "ORD001": {"id": "ORD001", "item": "Burger", "price": 12.99, "status": "pending"},
    "ORD002": {"id": "ORD002", "item": "Pizza", "price": 18.50, "status": "pending"},
    "ORD003": {"id": "ORD003", "item": "Salad", "price": 9.99, "status": "confirmed"},
}

class Order(BaseModel):
    id: str
    item: str
    price: float
    status: str

@app.get("/orders", response_model=List[Order])
async def get_orders(status: Optional[str] = None):
    if status:
        return [o for o in ORDERS.values() if o["status"] == status]
    return list(ORDERS.values())

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    return ORDERS.get(order_id, {"id": "NOT_FOUND", "item": "", "price": 0, "status": "not_found"})

@app.post("/orders/{order_id}/confirm")
async def confirm_order(order_id: str):
    if order_id in ORDERS:
        ORDERS[order_id]["status"] = "confirmed"
        return {"message": f"Order {order_id} confirmed", "order": ORDERS[order_id]}
    return {"message": "Order not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)