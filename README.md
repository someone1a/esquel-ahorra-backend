# PrecioJusto API

Grocery price comparison REST API built with FastAPI + MySQL.

## Requirements

- Python 3.11+
- MySQL 8.0+

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

### 4. Create the MySQL database

```sql
CREATE DATABASE preciojusto CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Seed the database (optional)

```bash
python seed.py
```

### 7. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

## Environment Variables

| Variable                   | Description                          | Example                                      |
|----------------------------|--------------------------------------|----------------------------------------------|
| DATABASE_URL               | MySQL connection string              | mysql+pymysql://user:pass@localhost/db        |
| SECRET_KEY                 | JWT signing secret                   | change-this-in-production                    |
| ALGORITHM                  | JWT algorithm                        | HS256                                        |
| ACCESS_TOKEN_EXPIRE_MINUTES| Token lifetime in minutes            | 60                                           |
| FRONTEND_ORIGIN            | Allowed CORS origin                  | http://localhost:5173                        |

## API Overview

| Method | Endpoint                        | Auth | Description                        |
|--------|---------------------------------|------|------------------------------------|
| POST   | /api/auth/register              | No   | Register new user                  |
| POST   | /api/auth/login                 | No   | Login and get JWT                  |
| GET    | /api/auth/me                    | Yes  | Get current user                   |
| GET    | /api/products                   | No   | List/search products               |
| GET    | /api/products/{id}              | No   | Product detail with best prices    |
| POST   | /api/products                   | Yes  | Create product                     |
| GET    | /api/prices?product_id={id}     | No   | List prices for a product          |
| POST   | /api/prices                     | Yes  | Report a price (+10 pts)           |
| POST   | /api/prices/{id}/confirm        | Yes  | Confirm a price (+5 pts)           |
| GET    | /api/stores                     | No   | List stores                        |
| GET    | /api/stores/{id}                | No   | Store detail                       |
| GET    | /api/shopping-list              | Yes  | Get user's shopping list           |
| POST   | /api/shopping-list/items        | Yes  | Add item to list                   |
| PATCH  | /api/shopping-list/items/{id}   | Yes  | Toggle item checked status         |
| DELETE | /api/shopping-list/items/{id}   | Yes  | Remove item from list              |
| GET    | /api/profile                    | Yes  | Get user profile/stats             |
| PATCH  | /api/profile                    | Yes  | Update profile                     |

## Points System

- Reporting a new price: **+10 points**
- Confirming a price: **+5 points**
- Price status: `unconfirmed` (0) → `recent` (1-2) → `confirmed` (3+)
