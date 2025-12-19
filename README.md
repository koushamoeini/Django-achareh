
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
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

python manage.py seed_examples

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
- Use the same credentials and passphrase for login: `/api/auth/login/` accepts `username`, `email`, or `phone_number` along with `password`.
- Emails and phone numbers are unique across users so the login endpoint can unambiguously map the identifier back to the right account.

**Demo accounts (created by `seed_examples`)**
Password for all: `DemoPass123`

- Customer: `demo_customer` (`email: customer@example.com`, `phone: +989111000001`)
- Customer: `demo_customer2` (`email: customer2@example.com`, `phone: +989111000002`)
- Contractor: `demo_contractor` (`email: contractor@example.com`, `phone: +989222000001`)
- Contractor: `demo_contractor2` (`email: contractor2@example.com`, `phone: +989222000002`)
- Support: `demo_support` (`email: support@example.com`, `phone: +989333000001`)
- Admin/Superuser: `demo_admin` (`email: admin@example.com`, `phone: +989444000001`)
