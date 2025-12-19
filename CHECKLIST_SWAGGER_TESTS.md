# Achareh Backend — Checklist Coverage + Swagger Test Guide (Updated)

This document maps the delivery checklist items to the current implementation in this repository and explains **exactly how to test each item in Swagger UI**.

Swagger UI URL (local):
- `http://localhost:8000/api/schema/swagger-ui/`

OpenAPI JSON:
- `http://localhost:8000/api/schema/`

---

## 0) One-time setup (required before Swagger tests)

1) Create the database tables (migrations):

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
```

2) Seed demo data (recommended):

```powershell
python manage.py seed_examples
```

3) Run the server:

```powershell
python manage.py runserver
```

### Demo accounts (created by `seed_examples`)
- Password for all: `DemoPass123`
-
- - Customer: `demo_customer` (email `customer@example.com`, phone_number `+989111000001`)
- - Customer: `demo_customer2` (email `customer2@example.com`, phone_number `+989111000002`)
- - Contractor: `demo_contractor` (email `contractor@example.com`, phone_number `+989222000001`)
- - Contractor: `demo_contractor2` (email `contractor2@example.com`, phone_number `+989222000002`)
- - Support: `demo_support` (email `support@example.com`, phone_number `+989333000001`)
- - Admin/Superuser (for `/admin/`): `demo_admin` (email `admin@example.com`, phone_number `+989444000001`)

---

## 1) Authentication (Register + Login)

### 1.1 Register (create a user)
**Status:** Implemented

Endpoint:
- `POST /api/auth/register/`

Swagger test:
1) Open `POST /api/auth/register/` → **Try it out**
2) Example request body:

```json
{
  "username": "u_test_1",
  "email": "u_test_1@example.com",
  "role": "customer",
  "password": "Pass12345"
}
```

Expected:
- `201 Created`

Notes:
- In the current code, the client can choose the `role` during registration.

### 1.2 Login (get auth token)
**Status:** Implemented

Endpoint:
- `POST /api/auth/login/`

Swagger test:
1) Open `POST /api/auth/login/` → **Try it out**
2) Example request body:

```json
{
  "username": "demo_customer",
  "password": "DemoPass123"
}
```

Expected:
- `200 OK` and a response like:

```json
{ "token": "..." }
```

Notes:
- Login accepts `username`, `email`, or `phone_number` as the identifier.
- Try these seeded identifiers:
  - `username`: `demo_customer`
  - `email`: `customer@example.com`
  - `phone_number`: `+989111000001`
- Email and phone_number are each unique per user so the same credential pair always hits a single account.

### 1.3 Using the token in Swagger
Most endpoints require authentication.

- For each protected endpoint you test, send this header:
  - `Authorization: Token <YOUR_TOKEN>`

If Swagger UI shows an **Authorize** button:
1) Click **Authorize**
2) Paste `Token <YOUR_TOKEN>`

If Swagger UI does **not** show an Authorize button:
- Use the endpoint’s header input (if available) or Swagger “Request headers” area (some Swagger builds allow adding headers). If your Swagger UI cannot add headers, use Postman/curl.

---

## 2) Entities & Relationships (User, Ad, Ticket, Comment)

### 2.1 User entity
**Status:** Implemented (Custom User model with `role`)

Evidence:
- Custom user model: `users.User` with `role` choices.

How to test (indirect via API):
- Register a user (`POST /api/auth/register/`) and check `role` in response.
- View user fields nested inside Ad/Proposal/Comment responses.

### 2.2 Ad entity
**Status:** Implemented

Endpoints:
- `GET /api/ads/`
- `POST /api/ads/`
- `GET /api/ads/{id}/`
- `PATCH /api/ads/{id}/`
- `DELETE /api/ads/{id}/`

Swagger test:
- Create an Ad (as customer) → then fetch, update, delete.

Example create request (Customer token required):
```json
{
  "title": "Test Ad",
  "description": "Need help",
  "status": "open",
  "budget": "1000.00",
  "category": "painting",
  "location": "Tehran",
  "start_date": "2025-12-01",
  "end_date": "2025-12-10",
  "hours_per_day": "6.0"
}
```

Expected:
- `201 Created`

### 2.3 Comment entity (comments on Ads)
**Status:** Implemented

Endpoints:
- `GET /api/ads/{ad_id}/comments/`
- `POST /api/ads/{ad_id}/comments/`
- `GET /api/comments/{id}/`
- `PATCH /api/comments/{id}/`
- `DELETE /api/comments/{id}/`

Swagger test:
1) Create an Ad
2) As any authenticated user, call `POST /api/ads/{ad_id}/comments/` with:
```json
{ "text": "Hello" }
```
3) Fetch list: `GET /api/ads/{ad_id}/comments/`

Expected:
- Create: `201`
- List: `200`

Permission check:
- Try to `PATCH` a comment as a different user → should be `403`.
Steps:
1. Authenticate with one seeded account (e.g., `demo_customer`) via `POST /api/auth/login/`, open `POST /api/ads/{ad_id}/comments/` in Swagger, provide `Authorization: Token <token>` and create a comment on any ad.
2. Switch to a different seeded account (`demo_contractor` or another demo user), authenticate, and set the new token in Swagger’s Authorization header (or use the per-endpoint header input).
3. Call `PATCH /api/comments/{comment_id}/` with the second user’s token to edit the comment you created earlier; the response should be `403 Forbidden` because only the original author can modify it.
Note: Swagger’s default example body (`{ "ad": 0, "text": "string" }`) is for the generic `comments/` endpoint. When you’re testing `POST /api/ads/{ad_id}/comments/`, you only need to send `{ "text": "Hello" }` because the ad is already specified in the path. Pick a real `ad_id` from `GET /api/ads/` (or the ad you just created) before you hit "Execute" so the request succeeds on the first try.

### 2.4 Ticket entity
**Status:** Implemented

Endpoints:
- `GET /api/tickets/`
- `POST /api/tickets/`
- `GET /api/tickets/{id}/`
- `PATCH /api/tickets/{id}/`
- `DELETE /api/tickets/{id}/`

Swagger test:
- Create a ticket:
```json
{
  "title": "Help",
  "description": "Need help"
}
```
Expected:
- `201 Created`

---

## 3) Role-based access levels
Checklist roles:
- Customer
- Contractor
- Support
- System Admin

**Status:** Implemented (via `User.role` and permissions in views)

How to test in Swagger:
- Obtain tokens for each demo user by calling `POST /api/auth/login/`.

### 3.1 Only Customers can create Ads
**Status:** Implemented

Test:
- With `demo_customer` token → `POST /api/ads/` should return `201`.
- With `demo_contractor` token → `POST /api/ads/` should return `403`.

### 3.2 Only Contractors can create Proposals
**Status:** Implemented

Endpoints:
- `GET /api/proposals/`
- `POST /api/proposals/`

Test:
- As customer, try:
```json
{ "ad": 1, "price": "100.00", "message": "I can do it" }
```
Expected: `403`

- As contractor, same request
Expected: `201`

### 3.3 Only Customers can create Ratings
**Status:** Implemented

Endpoint:
- `POST /api/ratings/`

Test:
- As contractor, try rating another contractor → expected `403`.
- As customer, rate a contractor for an ad:
```json
{ "contractor": 2, "ad": 1, "score": 5, "comment": "Great" }
```
Expected: `201`

### 3.4 Support permissions on Tickets
**Status:** Implemented (assign + replies)

Test:
- Create ticket as customer.
- As support user, patch ticket (assign to self) by sending:
```json
{ "assignee": <support_user_id> }
```
Expected: `200`

- As support user, reply to the ticket:
`POST /api/tickets/{ticket_id}/messages/` with:
```json
{ "text": "We are checking this." }
```
Expected: `201`

---

## 4) CRUD endpoints for entities
Checklist expects CRUD endpoints for each main entity.

**Status:** Implemented (ratings detail still omitted by design)

Implemented CRUD:
- Ads: full CRUD
- Comments: full CRUD
- Tickets: full CRUD
- Schedules: full CRUD (detail endpoint is `/api/schedules/{id}/`)
- Proposals: have detail `GET/PATCH/DELETE /api/proposals/{id}/` in addition to list/create and workflow actions

Partially CRUD:
- Ratings: list/create; no detail update/delete endpoint (not required by spec text; can add if desired)

Swagger testing:
- Proposals detail: `GET /api/proposals/{id}/`, `PATCH /api/proposals/{id}/`, `DELETE /api/proposals/{id}/` (owner-only by permission)
- Others as listed in section 2.

---

## 5) Ad statuses (open / assigned / done / canceled)
**Status:** Implemented (model supports all 4)

How to test:

### 5.1 Set status to `open`
- Create Ad with `status: open`.

### 5.2 Move to `assigned` (customer accepts a proposal)
Endpoints:
- `POST /api/proposals/{id}/accept/`

Test flow:
1) Customer creates an Ad
2) Contractor creates a Proposal for that ad
3) Customer calls `POST /api/proposals/{proposal_id}/accept/`

Expected:
- `200` and Ad becomes `assigned`

### 5.3 Move to `done` (contractor completes, customer confirms)
Endpoints:
- `POST /api/proposals/{id}/complete/`
- `POST /api/proposals/{id}/confirm/`

Test flow:
1) Customer accepts proposal
2) Contractor calls `/complete/`
3) Customer calls `/confirm/`

Expected:
- Ad becomes `done`

### 5.4 `canceled`
**Status:** Model supports it; no dedicated cancel endpoint.

Test:
- As Ad owner, `PATCH /api/ads/{id}/` with:
```json
{ "status": "canceled" }
```

---

## 6) Proposal workflow (contractor request → customer accept → contractor complete → customer confirm)
**Status:** Implemented

Endpoints:
- `POST /api/proposals/`
- `POST /api/proposals/{id}/accept/`
- `POST /api/proposals/{id}/complete/`
- `POST /api/proposals/{id}/confirm/`

Swagger test:
- Follow the exact steps described in section 5.2 and 5.3.

---

## 7) “Customer can comment and rate per Ad”
**Status:** Implemented

- Comments are linked to Ads.
- Ratings now include an `ad` field, so ratings can be tied to a specific job/ad.

Swagger test:
- Comments: use `/api/ads/{ad_id}/comments/`
- Ratings: use `/api/ratings/` with body:
```json
{ "contractor": <contractor_id>, "ad": <ad_id>, "score": 5, "comment": "Great" }
```
Filters:
- `GET /api/contractors/{contractor_id}/ratings/?min_score=4`
- `GET /api/ratings/?ad=<ad_id>`
Example defaults you can type before hitting Execute:
```
min_score=4
min_reviews=2
ordering=-created_at
page=1
```
Swagger will append those as query params so the first response already shows filtered content.

---

## 8) Contractor profile + average rating + ratings count
**Status:** Implemented

Endpoints:
- `GET /api/contractors/` (list with `avg_rating`, `ratings_count`)
- `GET /api/contractors/{id}/profile/`
- `GET /api/contractors/{id}/ratings/`

Swagger test:
1) Ensure ratings exist (seed data already creates some)
2) Call `GET /api/contractors/`
3) Optionally filter/order:
   - `GET /api/contractors/?min_avg=4`
   - `GET /api/contractors/?min_reviews=2`
   - `GET /api/contractors/?order_by=avg_rating`

Expected:
- Each contractor row includes `avg_rating` and `ratings_count`.

---

## 9) Customer profile + customer ads
**Status:** Implemented

Endpoint:
- `GET /api/customers/{id}/profile/`

Response includes: id, username, email, role, `ad_count`, and the list of ads created by that customer.

Swagger test:
- `GET /api/customers/{customer_id}/profile/`

---

## 10) Filtering and ranking contractors
**Status:** Implemented

Endpoints:
- `GET /api/contractors/`

Swagger test:
- Filter by minimum average rating:
  - `GET /api/contractors/?min_avg=4`
- Filter by minimum number of reviews:
  - `GET /api/contractors/?min_reviews=2`
- Order:
  - `GET /api/contractors/?order_by=avg_rating`
  - `GET /api/contractors/?order_by=ratings_count`

Expected:
- Ordered list with pagination.

---

## 11) Ticket creation by customer + support handling
**Status:** Implemented

What exists:
- Ticket create (any authenticated user)
- Support can assign tickets
- Support replies through `TicketMessage`

Swagger test:
1) As customer, create a ticket
2) As support, patch ticket `assignee`
3) As support, reply: `POST /api/tickets/{ticket_id}/messages/` with `{ "text": "Your ticket is being reviewed." }`

---

## 12) Schedules (contractor availability)
**Status:** Implemented

Endpoints:
- `GET /api/contractors/{contractor_id}/schedule/`
- `POST /api/contractors/{contractor_id}/schedule/`
- `GET /api/schedules/{id}/`
- `PATCH /api/schedules/{id}/`
- `DELETE /api/schedules/{id}/`

Swagger test:
- As contractor, create schedule:
```json
{ "day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00", "is_available": true, "location": "Tehran" }
```
Expected:
- `201`

Permission check:
- As customer, try to POST schedule → should be `403`.

---

## 13) Pagination
**Status:** Implemented (global DRF pagination: page size 10)

Swagger test:
- Create >10 ads (or use seed and add more)
- Call:
  - `GET /api/ads/`
  - `GET /api/ads/?page=2`

Expected:
- Response has `count`, `next`, `previous`, `results`.

---

## Summary of gaps vs. checklist (after updates)

- Addressed: customer profile endpoint added.
- Addressed: ratings now link to an Ad.
- Addressed: ticket replies via `TicketMessage` endpoint.
- Addressed: proposal detail CRUD added.
- Remaining: ratings still lack a detail update/delete endpoint (not demanded explicitly by spec; can be added if required).
