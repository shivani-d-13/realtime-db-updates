# Realtime Order Tracker

A real-time order tracking system where clients automatically receive updates whenever data in the database changes, no polling required.

---

## What it does

Any insert, update, or delete on the `orders` table is instantly reflected in the browser without the client ever asking "did something change?". The browser just listens, and the server tells it.

---

## Architecture

```
Browser Client (index.html)
        │
        │  1. fetches existing orders on load
        ▼
FastAPI Backend (main.py)
        │
        │  2. Read/write
        ▼
Supabase (PostgreSQL)
        │
        │  3. change detected
        ▼
Supabase Realtime Server
        │
        │  4. Pushes change over WebSocket
        ▼
Browser Client (index.html)
        │
        │  5. Updates UI instantly
        ▼
User sees the change in real time
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python + FastAPI | Clean, fast, minimal boilerplate. Easy to understand and build CRUD APIs with. |
| Database | PostgreSQL via Supabase | Postgres is reliable and proven over time. Supabase builds on top of it & adds built-in realtime features. |
| Realtime | Supabase Realtime | Built on Postgres logical replication. Eliminates need to write custom LISTEN/NOTIFY triggers. |
| Frontend | Vanilla HTML + JS | No framework overhead. Supabase JS client handles WebSocket connection natively. |

---

## Why this architecture?

The assignment asks for a backend service that listens for DB changes and pushes updates to clients. One approach could be:

```
DB → Backend (listens) → Backend (pushes) → Client
```

Instead, current implementation follows:

```
DB → Supabase Realtime (listens + pushes) → Client
FastAPI → handles all CRUD operations
```

Routing Realtime events through FastAPI would introduce an additional layer in the communication flow, increasing latency and adding unnecessary operational complexity. Supabase Realtime is already designed to efficiently handle WebSocket-based event delivery at scale.

In this architecture, each component is responsible for what it is best suited for. FastAPI manages business logic and database interactions, while Supabase Realtime is responsible for delivering live updates to connected clients.

---

## How Supabase Realtime works

Supabase Realtime uses PostgreSQL logical replication. Postgres maintains a replication slot - a stream of every change made to the database (inserts, updates, deletes). Supabase Realtime listens to this stream, filters changes by table and schema, and broadcasts them to subscribed clients over WebSocket.


```sql
ALTER TABLE orders REPLICA IDENTITY FULL;
```
By default, Postgres only includes the primary key in DELETE events. REPLICA IDENTITY FULL tells Postgres to include the entire old row — so clients receive
full order details even on delete.

---

## Features

- Real-time INSERT, UPDATE, DELETE events pushed to browser via WebSocket
- Row flash animations — green for insert, blue for update, red for delete
- Live event log showing every change with timestamp
- Full CRUD via FastAPI REST API
- Orders persist across page refreshes (loaded from DB on mount)

---

## Project Structure

```
realtime-db-updates/
├── backend/
│   └── main.py          # FastAPI app — CRUD routes for orders
├── frontend/
│   └── index.html       # Browser client — Realtime subscription + UI
├── .env                 # Supabase credentials (not committed to git)
├── requirements.txt     # Python dependencies
└── README.md
```

---

## How to run

### Prerequisites
- Python 3.8+
- A Supabase project with the orders table set up (see below)

### 1. Clone the repo

```bash
git clone https://github.com/shivani-d-13/realtime-db-updates.git
cd realtime-db-updates
```

### 2. Create the orders table in Supabase

Go to your Supabase project → SQL Editor and run:

```sql
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_name TEXT NOT NULL,
  product_name TEXT NOT NULL,
  status TEXT CHECK (status IN ('pending', 'shipped', 'delivered')) NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE orders REPLICA IDENTITY FULL;

ALTER PUBLICATION supabase_realtime ADD TABLE orders;
```

### 3. Set up environment variables

Create a `.env` file in the root:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

### 4. Install dependencies and run the backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

### 5. Open the frontend

Open `frontend/index.html` in your browser.

Add your Supabase URL and anon key in the script section of `index.html`:

```js
const SUPABASE_URL = 'YOUR_SUPABASE_URL'
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'
```

---

## Scaling & production

**Scaling:** This architecture scales well. Supabase Realtime handles WebSocket connections independently of FastAPI. If traffic grew to tens of thousands of concurrent clients, you would:
- Scale Supabase Realtime horizontally, since it operates as a stateless service per channel.
- Put FastAPI behind a load balancer
- Add Redis pub/sub if you need cross-instance event broadcasting from the backend

**Persistent event log:** The live event log is in-memory and clears on refresh. In production, events would be stored in a separate `order_events` table for full audit history.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/orders` | Fetch all orders |
| POST | `/orders` | Create a new order |
| PATCH | `/orders/{id}` | Update an existing order |
| DELETE | `/orders/{id}` | Delete an order |