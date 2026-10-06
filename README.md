# Vaultra — Django backend

The banking site (landing page, login/signup, customer dashboard, bank
admin dashboard) wired to a real Django backend: models, forms, views,
a small JSON API for the live-updating parts, and Django's session auth.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations accounts banking
python manage.py migrate

python manage.py seed_demo          # creates demo@vaultra.bank / demo1234
                                     # and admin@vaultra.bank / admin1234
python manage.py createsuperuser    # optional, for /django-admin/

python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

## Project layout

```
vaultra_project/   settings.py, root urls.py, wsgi/asgi
accounts/          custom User model (email login, role field), signup/login/logout views
banking/           Balance, Transaction, LiveTransactionStatus, SavingsGoal, Notification
                    models + services.py (all balance-mutating logic in one place)
                    + views.py (pages + JSON API) + forms.py
templates/         base.html, landing/, accounts/login.html, dashboard/
static/js/app.js   fetch() API wrapper, remote smart-table component, the
                    animated "heartbeat" canvas — no business logic, UI only
```

## How the pieces map to the original static prototype

| Frontend feature                         | Backend                                                              |
|-------------------------------------------|-----------------------------------------------------------------------|
| Login / signup                            | `accounts` app — `EmailBackend`, `SignupForm`, `LoginForm`            |
| Checking / savings / fixed deposit        | `banking.Balance` (one row per user)                                  |
| Transaction history, smart table          | `banking.Transaction` + `banking.utils.smart_table_response`          |
| "Send to another bank"                    | `banking.ExternalTransferDetail` + `services.send_external_transfer`  |
| Live heartbeat monitor                    | `banking.LiveTransactionStatus`, polled via `GET /api/live-status/`   |
| Admin "Live transaction control"          | `POST /api/admin/live-status/<id>/set/`, called repeatedly by the admin dashboard's `runLiveSim()` to animate a pipeline — no background worker needed |
| Notification bell                         | `banking.Notification` (`audience` = customer or admin)               |
| Admin adjust balance / freeze / approve   | `services.py` functions, each behind an `@admin_required` API view    |

## Notes for going further

- **Real-time push**: the live monitor currently polls once a second
  (see `static/js/app.js` and `vaultra_project/asgi.py`). Swapping this
  for a Django Channels WebSocket per account would remove the polling
  delay without changing `LiveTransactionStatus` at all.
- **Analytics charts**: the two chart panels (balance trend, spending by
  category, deposits under management, etc.) still plot illustrative
  numbers client-side, exactly like the static prototype — wiring them
  to real monthly aggregates of `Transaction`/`Balance` is a clean
  follow-up (`django.db.models.functions.TruncMonth` + `Sum`).
- **Production checklist**: search this codebase for `PRODUCTION NOTE`
  — `SECRET_KEY`, `DEBUG`, the SQLite database, and the HTTPS-only
  cookie settings in `settings.py` all need a real value before deploy.
