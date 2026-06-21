# 💸 Split-Wise

A Splitwise-style expense sharing app. Create people, form groups, add expenses
that split equally or by exact amounts, see who owes whom, and settle up — with
debts automatically simplified into the fewest payments.

Flask + SQLAlchemy backend, vanilla JS frontend served from the same origin,
SQLite in dev / PostgreSQL in production. Deployable to Render in one click.

## Features

- **People** – add users (name + unique email)
- **Groups** – create groups and add members
- **Expenses** – record who paid and split **equally** or by **exact amounts**
  (exact shares must sum to the total)
- **Balances** – per-person net (gets back / owes) for a group
- **Settle up** – greedy debt simplification → minimal set of payments
- **Settlements** – record a payment to clear a balance
- **Delete** expenses

## Architecture

```
backend/
  app.py              App factory: serves the UI, registers blueprints, creates tables
  config.py           DB config (sqlite dev / postgres prod)
  extensions.py       SQLAlchemy instance
  models.py           User, Group, GroupMember, Expense, ExpenseSplit, Settlement
  services/balances.py  Net balances + debt simplification + equal-split rounding
  routes/             users, groups, expenses, settlements (Flask blueprints)
frontend/             index.html + style.css + script.js (single-page UI)
```

## API

| Method | Path                              | Purpose                              |
| ------ | --------------------------------- | ------------------------------------ |
| GET/POST | `/api/users`                    | List / create people                 |
| GET/POST | `/api/groups`                   | List / create groups                 |
| GET    | `/api/groups/<id>`                | Group detail: members, expenses, balances, settle-up |
| POST   | `/api/groups/<id>/members`        | Add a member                         |
| POST   | `/api/expenses`                   | Add an expense (equal or exact split) |
| DELETE | `/api/expenses/<id>`              | Delete an expense                    |
| POST   | `/api/settlements`                | Record a payment                     |
| GET    | `/health`                         | Health check                         |

### Add-expense body

```jsonc
// equal split among selected participants
{ "group_id": 1, "description": "Dinner", "amount": 90, "paid_by": 2,
  "split_type": "equal", "participants": [1, 2, 3] }

// exact amounts (must sum to amount)
{ "group_id": 1, "description": "Hotel", "amount": 100, "paid_by": 1,
  "split_type": "exact", "shares": [{"user_id": 1, "share": 60}, {"user_id": 2, "share": 40}] }
```

## Run locally

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
gunicorn --chdir backend app:app --bind 127.0.0.1:8000
# open http://localhost:8000
```

## Deploy to Render

This repo ships a [`render.yaml`](render.yaml) blueprint (web service + free
PostgreSQL).

1. Push to GitHub (done).
2. Render dashboard → **New → Blueprint** → connect this repo → **Apply**.
3. `DATABASE_URL` and `SECRET_KEY` are injected automatically. Health check is
   `/health`.

The web service serves both the API and the UI on the same origin, so no extra
frontend hosting is needed.
