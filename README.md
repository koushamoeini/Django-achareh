# Django Achareh Backend

This repository implements the backend for the Achareh assignment. It contains user authentication and role-based endpoints, Ads, Proposals, Comments, Ratings, Tickets, Schedules and admin features.

Key Endpoints:
- `POST /api/auth/register/`: register a user (role: customer/contractor/support/admin)
- `POST /api/auth/login/`: login and receive token
- `GET /api/ads/` and `POST /api/ads/`: list and create ads (only `customer` can create)
- `GET /api/ads/<id>/` : ad details (includes nested proposals & comments)
- `POST /api/proposals/` : create proposal (contractor only); `POST /api/proposals/<id>/accept/` to accept
- `POST /api/proposals/<id>/complete/` : contractor marks completed
- `POST /api/proposals/<id>/confirm/` : ad owner confirms completion (ad status -> done)
- `GET/POST /api/ads/<ad_id>/comments/` and `GET/PATCH/DELETE /api/comments/<id>/` for comments
- `GET/POST /api/contractors/<id>/ratings/` and `GET /api/ratings/` to list & create ratings (customers only)
- `GET /api/contractors/` to list contractors (ordering and filters available)
- `PATCH /api/users/<id>/role/` to change a user's role (admin/superuser only)
- `GET/POST /api/contractors/<id>/schedule/` and `GET/PATCH/DELETE /api/schedules/<id>/` for contractor availability; includes location/time/availability
- `GET/POST /api/tickets/` and `GET/PATCH/DELETE /api/tickets/<id>/` for support tickets

Filters and Query Params supported:
- Ratings: `?min_score=` and `?max_score=` for rating lists
- Contractor list: `?order_by=avg_rating|ratings_count`, `?min_avg=`, `?min_reviews=` 
- Ads: `?status=open|assigned|done|canceled`, `?title=` partial search

Pagination:
- All list endpoints use PageNumber pagination with `page` query parameter and a default page size of 10. Responses are in the form `{count, next, previous, results}`.

Run locally (PowerShell examples):
1. Create and activate venv, then install dependencies:
```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```
2. Run migrations and tests:
```powershell
python manage.py makemigrations; python manage.py migrate;
python manage.py test --verbosity 2
```
3. Run the dev server:
```powershell
python manage.py runserver
```

Testing (API examples):
```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/auth/register/' -Method POST -ContentType 'application/json' -Body '{"username":"alice","password":"pass123","email":"alice@example.com","role":"customer"}'
$login = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/auth/login/' -Method POST -ContentType 'application/json' -Body '{"username":"alice","password":"pass123"}'
$token = $login.token
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/ads/' -Method POST -ContentType 'application/json' -Headers @{ Authorization = "Token $token" } -Body '{"title":"Paint","description":"Need paint","status":"open"}'
```

If you prefer `curl` commands, use `curl.exe` in PowerShell or use a bash terminal.

More work can be done (optional): file uploads, nested permissions, email notifications, more complex state transitions and workflows. If you want me to add any of those, let me know.
