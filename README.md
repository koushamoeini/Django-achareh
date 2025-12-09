
## Achareh — Backend API

This repository contains the backend implementation for a sample service called Achareh, built with Django and Django REST Framework. The API supports managing Ads, Proposals, Comments, Ratings, Tickets, and Schedules, and includes role-based behavior for Customers, Contractors, Support staff, and Admins.

**Tech stack:**
- Python + Django
- Django REST Framework (DRF)
- Token authentication (DRF Token)
- `django-filter` for filtering
- `drf-spectacular` for generating OpenAPI / Swagger documentation

**Quick start (local):**

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Seed example/demo data (creates demo users and sample content)
python manage.py seed_examples

# Run development server
python manage.py runserver
```

**API documentation (Swagger / OpenAPI):**

The interactive API documentation is an important artifact for QA and integration. We recommend using `drf-spectacular` to generate OpenAPI schema and serve an interactive Swagger UI. Please make sure the README or project docs include a link to the Swagger UI (for example `/api/schema/swagger-ui/`) so testers and integrators can quickly explore the API.

Also, include representative request and response examples for key endpoints in the schema so the interactive docs show concrete payloads for both requests and responses.

After starting the server, the documentation endpoints are available at:

- OpenAPI JSON: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- Redoc: `http://localhost:8000/api/schema/redoc/`

**QA / manual testing tips:**
- Run `python manage.py seed_examples` to create demo accounts and content that exercise common flows (create ad, submit proposal, accept/complete/confirm proposal, submit rating).
- Use the examples shown in Swagger (or the example payloads you add to the schema) to make valid requests with tools like Postman, HTTPie, or `curl`.

If you'd like, I can also prepare ready-to-run `curl` commands or a PowerShell script that exercises the main endpoints end-to-end for quick verification.

**Upload checklist:**
- Delete `db.sqlite3` (or any local database file) and any `__pycache__`/`.pyc` artifacts so the repo only contains source, migrations and docs.
- After cloning, run `python manage.py migrate` followed by `python manage.py seed_examples` to rebuild the schema and demo data.
- Use the seeded admin panel account `demo_admin` / `DemoPass123` (superuser + staff) to log in at `/admin/` once the server is running.

