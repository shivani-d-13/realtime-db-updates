import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = FastAPI()

# Allow frontend to communicate with backend service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data model for creating/updating an order ---
class OrderPayload(BaseModel):
    customer_name: str
    product_name: str
    status: str

# --- Routes ---

@app.get("/")
def root():
    return {"message": "Realtime Order Tracking API is running"}

@app.get("/orders")
def get_orders():
    """Fetch all current orders from the database."""
    response = supabase.table("orders").select("*").order("id").execute()
    return response.data

@app.post("/orders")
def create_order(payload: OrderPayload):
    """Insert a new order into the database."""
    response = supabase.table("orders").insert({
        "customer_name": payload.customer_name,
        "product_name": payload.product_name,
        "status": payload.status,
    }).execute()
    return response.data

@app.patch("/orders/{order_id}")
def update_order(order_id: int, payload: OrderPayload):
    """Update an existing order's status."""
    response = supabase.table("orders").update({
        "customer_name": payload.customer_name,
        "product_name": payload.product_name,
        "status": payload.status,
        "updated_at": "now()",
    }).eq("id", order_id).execute()
    return response.data

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    """Delete an order from the database."""
    response = supabase.table("orders").delete().eq("id", order_id).execute()
    return {"message": f"Order {order_id} deleted"}