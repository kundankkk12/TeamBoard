# TeamBoard Backend

TeamBoard is a Django REST API for an AI-powered knowledge base platform sold as a B2B service. Companies register on the platform, receive an API key, authenticate with JWT, query a curated knowledge base, and generate usage data that platform admins can inspect through an aggregated dashboard.

This project implements the backend requirements for:

- company registration
- JWT-based authentication
- knowledge base querying
- per-query usage logging
- admin-only usage analytics
- PostgreSQL-based persistence
- Docker-based database setup

## Project Goal

The backend solves four business problems:

1. A company must be able to register and receive credentials.
2. A registered company must be able to search the knowledge base securely.
3. Every search must be logged for platform usage tracking.
4. Platform admins must be able to inspect aggregate usage statistics.

## Main Features

- Public registration endpoint that creates a Django `User`, auto-creates a `Company`, generates an API key, and returns a JWT access token.
- Public login endpoint that returns a fresh JWT access token plus company credentials.
- Protected knowledge base query endpoint using JWT authentication.
- Atomic query logging through `QueryLog`.
- Admin-only dashboard endpoint using a custom DRF permission class.
- PostgreSQL configured through environment variables only.
- Seed command for inserting knowledge base entries.
- Automated API tests covering expected success and failure scenarios.

## Tech Stack

- Python 3.14
- Django 6.0.7
- Django REST Framework 3.17.1
- SimpleJWT 5.5.1
- PostgreSQL 16
- Docker Compose
- python-dotenv

## Project Structure

```text
TeamBoard/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── manage.py
├── README.md
├── requirements.txt
├── TeamBoard/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── permissions.py
    ├── signals.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── management/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── seed_kb_entries.py
    └── migrations/
        ├── __init__.py
        └── 0001_initial.py
```

## Environment Variables

Create `.env` in the project root using `.env.example` as a template.

Example:

```env
DEBUG=True
SECRET_KEY=replace-with-a-long-random-secret-at-least-32-characters
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=teamboard
DB_USER=teamboard_user
DB_PASSWORD=teamboard_pass
DB_HOST=127.0.0.1
DB_PORT=5432
```

### Why `.env` is required

All credentials are loaded from environment variables. The project intentionally raises an error if required values are missing. This prevents accidental hardcoding of secrets in `settings.py`.

## Installation and Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL with Docker

```bash
docker compose up -d
```

Check that the database is up:

```bash
docker compose ps
docker compose logs --tail=50 db
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Seed the knowledge base

```bash
python manage.py seed_kb_entries --reset
```

### 6. Run tests

```bash
python manage.py test api
```

### 7. Start the development server

```bash
python manage.py runserver 0.0.0.0:8000
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## Postman Collection Guide

This section explains how to create, run, verify, and export a Postman collection that covers all required API scenarios.

### Goal of the Postman Collection

The Postman collection should prove that:

- registration works
- duplicate usernames are rejected
- login works
- invalid login is rejected
- protected query access is enforced
- query results are returned correctly
- zero-result searches still succeed and log usage
- missing search input is rejected
- client users cannot access the usage dashboard
- admin users can access the usage dashboard
- query logs are actually written to the database

### Suggested Postman Setup

Create a new Postman collection named:

```text
TeamBoard API Tests
```

Create a Postman environment named:

```text
TeamBoard Local
```

Add these environment variables:

- `base_url` = `http://127.0.0.1:8000`
- `username` = `acmecorp`
- `password` = `securepass123`
- `company_name` = `Acme Corp`
- `email` = `dev@acmecorp.com`
- `access_token` = leave blank initially
- `admin_access_token` = leave blank initially

### How to Create the Requests in Postman

For each request below:

1. Click `New` in Postman.
2. Choose `HTTP Request`.
3. Name the request exactly as shown.
4. Save it inside the `TeamBoard API Tests` collection.
5. Use the endpoint, headers, and body exactly as listed.

### Request 1: Register a New Company

Name the request:

```text
01 - Register New Company
```

Method and URL:

```text
POST {{base_url}}/api/auth/register/
```

Headers:

- `Content-Type: application/json`

Body type:

- `raw`
- `JSON`

Body:

```json
{
  "username": "{{username}}",
  "password": "{{password}}",
  "company_name": "{{company_name}}",
  "email": "{{email}}"
}
```

Expected result:

- status code `201`
- response contains `api_key`
- response contains `access`

Recommended Tests tab script:

```javascript
pm.test("Status is 201", function () {
  pm.response.to.have.status(201);
});

const data = pm.response.json();
pm.environment.set("access_token", data.access);

pm.test("api_key exists", function () {
  pm.expect(data.api_key).to.exist;
});

pm.test("access token exists", function () {
  pm.expect(data.access).to.exist;
});
```

### Request 2: Register with Duplicate Username

Name the request:

```text
02 - Register Duplicate Username
```

Method and URL:

```text
POST {{base_url}}/api/auth/register/
```

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "username": "{{username}}",
  "password": "{{password}}",
  "company_name": "{{company_name}}",
  "email": "{{email}}"
}
```

Expected result:

- status code `400`

Recommended Tests tab script:

```javascript
pm.test("Status is 400", function () {
  pm.response.to.have.status(400);
});
```

### Request 3: Login with Valid Credentials

Name the request:

```text
03 - Login Valid Credentials
```

Method and URL:

```text
POST {{base_url}}/api/auth/login/
```

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "username": "{{username}}",
  "password": "{{password}}"
}
```

Expected result:

- status code `200`
- response contains `access`

Recommended Tests tab script:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

const data = pm.response.json();
pm.environment.set("access_token", data.access);

pm.test("access token exists", function () {
  pm.expect(data.access).to.exist;
});
```

### Request 4: Login with Wrong Password

Name the request:

```text
04 - Login Wrong Password
```

Method and URL:

```text
POST {{base_url}}/api/auth/login/
```

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "username": "{{username}}",
  "password": "wrongpass"
}
```

Expected result:

- status code `401`

Recommended Tests tab script:

```javascript
pm.test("Status is 401", function () {
  pm.response.to.have.status(401);
});
```

### Request 5: Query KB Without Token

Name the request:

```text
05 - Query KB Without Token
```

Method and URL:

```text
POST {{base_url}}/api/kb/query/
```

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "search": "select_related"
}
```

Expected result:

- status code `401`

Recommended Tests tab script:

```javascript
pm.test("Status is 401", function () {
  pm.response.to.have.status(401);
});
```

### Request 6: Query KB with Valid Token and Matching Results

Name the request:

```text
06 - Query KB With Results
```

Method and URL:

```text
POST {{base_url}}/api/kb/query/
```

Headers:

- `Content-Type: application/json`
- `Authorization: Bearer {{access_token}}`

Body:

```json
{
  "search": "select_related"
}
```

Expected result:

- status code `200`
- response contains `results`
- response `count` is greater than `0`

Recommended Tests tab script:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

const data = pm.response.json();

pm.test("Results array exists", function () {
  pm.expect(data.results).to.be.an("array");
});

pm.test("Count is greater than zero", function () {
  pm.expect(data.count).to.be.above(0);
});
```

### Request 7: Query KB with Valid Token and No Matching Results

Name the request:

```text
07 - Query KB No Matching Results
```

Method and URL:

```text
POST {{base_url}}/api/kb/query/
```

Headers:

- `Content-Type: application/json`
- `Authorization: Bearer {{access_token}}`

Body:

```json
{
  "search": "zzzz-no-match"
}
```

Expected result:

- status code `200`
- `results` is an empty list
- `count` equals `0`

Recommended Tests tab script:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

const data = pm.response.json();

pm.test("Results array is empty", function () {
  pm.expect(data.results).to.be.an("array").that.is.empty;
});

pm.test("Count is zero", function () {
  pm.expect(data.count).to.eql(0);
});
```

### Request 8: Query KB with Missing Search Field

Name the request:

```text
08 - Query KB Missing Search
```

Method and URL:

```text
POST {{base_url}}/api/kb/query/
```

Headers:

- `Content-Type: application/json`
- `Authorization: Bearer {{access_token}}`

Body:

```json
{}
```

Expected result:

- status code `400`

Recommended Tests tab script:

```javascript
pm.test("Status is 400", function () {
  pm.response.to.have.status(400);
});
```

### Request 9: Usage Summary with CLIENT Token

Name the request:

```text
09 - Usage Summary Client Forbidden
```

Method and URL:

```text
GET {{base_url}}/api/admin/usage-summary/
```

Headers:

- `Authorization: Bearer {{access_token}}`

Expected result:

- status code `403`

Recommended Tests tab script:

```javascript
pm.test("Status is 403", function () {
  pm.response.to.have.status(403);
});
```

### Request 10: Usage Summary with Admin Token

Name the request:

```text
10 - Usage Summary Admin Success
```

Important note:

Before running this request, the test company must be promoted to `admin` in the database. That can be done in Django shell or PGAdmin.

Example Django shell command:

```bash
python manage.py shell
```

Then:

```python
from django.contrib.auth.models import User
user = User.objects.get(username='acmecorp')
company = user.company
company.role = 'admin'
company.save()
```

After promotion, run the login request again and store the new access token as `admin_access_token`.

Method and URL:

```text
GET {{base_url}}/api/admin/usage-summary/
```

Headers:

- `Authorization: Bearer {{admin_access_token}}`

Expected result:

- status code `200`
- response contains usage stats

Recommended Tests tab script:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

const data = pm.response.json();

pm.test("total_queries exists", function () {
  pm.expect(data.total_queries).to.not.equal(undefined);
});

pm.test("active_companies exists", function () {
  pm.expect(data.active_companies).to.not.equal(undefined);
});

pm.test("top_search_terms is an array", function () {
  pm.expect(data.top_search_terms).to.be.an("array");
});
```

### Request 11: Verify QueryLog in PGAdmin

Name this verification step:

```text
11 - Verify QueryLog Rows in PGAdmin
```

This is not an HTTP request. It is a manual database verification step after Requests 6 and 7.

Expected result:

- at least one row exists for the successful search
- at least one row exists for the zero-result search

Detailed verification steps in PGAdmin:

1. Ensure services are running before opening PGAdmin.
2. In terminal, run `docker compose ps` and confirm `teamboard-postgres` is `Up`.
3. If needed, start it with `docker compose up -d`.
4. Launch pgAdmin and sign in.
5. In the left sidebar, right-click `Servers` and choose `Register` then `Server...` if no server is configured yet.
6. In `General`, set Name to `TeamBoard Local`.
7. In `Connection`, set Host to `127.0.0.1`, Port to `5432`, Maintenance DB to `postgres`, Username to `teamboard_user`, and Password to `teamboard_pass`.
8. Click `Save`.
9. Expand `Servers` then `TeamBoard Local` then `Databases`.
10. Click the `teamboard` database.
11. Open `Tools` then `Query Tool`.
12. Run the SQL below to inspect all recent query logs.

```sql
SELECT q.id,
       u.username,
       c.company_name,
       q.search_term,
       q.results_count,
       q.queried_at
FROM api_querylog q
JOIN api_company c ON q.company_id = c.id
JOIN auth_user u ON c.user_id = u.id
ORDER BY q.queried_at DESC;
```

13. Find the username you used in Postman (for example, `postman_acme_...`).
14. Confirm one row exists for the Request 6 term (for example `select_related`) with `results_count > 0`.
15. Confirm one row exists for the Request 7 term (for example `zzzz-no-match`) with `results_count = 0`.

Optional filtered SQL for one specific Postman user:

```sql
SELECT q.id,
       u.username,
       q.search_term,
       q.results_count,
       q.queried_at
FROM api_querylog q
JOIN api_company c ON q.company_id = c.id
JOIN auth_user u ON c.user_id = u.id
WHERE u.username = 'postman_acme_1785058080'
ORDER BY q.queried_at DESC;
```

Optional strict pass/fail checks:

```sql
SELECT EXISTS (
  SELECT 1
  FROM api_querylog q
  JOIN api_company c ON q.company_id = c.id
  JOIN auth_user u ON c.user_id = u.id
  WHERE u.username = 'postman_acme_1785058080'
    AND q.search_term = 'select_related'
) AS has_select_related;
```

```sql
SELECT EXISTS (
  SELECT 1
  FROM api_querylog q
  JOIN api_company c ON q.company_id = c.id
  JOIN auth_user u ON c.user_id = u.id
  WHERE u.username = 'postman_acme_1785058080'
    AND q.search_term = 'zzzz-no-match'
    AND q.results_count = 0
) AS has_no_match;
```

Request 11 is considered passed when both checks are `true`.

### Recommended Execution Order in Postman

Run the requests in this order:

1. `01 - Register New Company`
2. `02 - Register Duplicate Username`
3. `03 - Login Valid Credentials`
4. `04 - Login Wrong Password`
5. `05 - Query KB Without Token`
6. `06 - Query KB With Results`
7. `07 - Query KB No Matching Results`
8. `08 - Query KB Missing Search`
9. `09 - Usage Summary Client Forbidden`
10. Promote the company to admin in the database.
11. Run `03 - Login Valid Credentials` again and save the new token as `admin_access_token`.
12. `10 - Usage Summary Admin Success`
13. `11 - Verify QueryLog Rows in PGAdmin`

### How to Export the Collection as JSON

After creating and verifying all requests:

1. Open the `TeamBoard API Tests` collection in Postman.
2. Click the collection menu.
3. Choose `Export`.
4. Select Collection v2.1 format.
5. Save the exported `.json` file.

Suggested filename:

```text
teamboard-postman-collection.json
```

### Expected Final Postman Coverage

The exported collection should demonstrate all of the following scenarios as tested and passing:

1. Register a new company
2. Register with duplicate username
3. Login with valid credentials
4. Login with wrong password
5. Query KB without token
6. Query KB with token and matching results
7. Query KB with token and no matching results
8. Query KB with missing search field
9. Usage summary with client token
10. Usage summary with admin token
11. QueryLog verification in PGAdmin

## Assignment Steps and How They Were Implemented

## Step 1: Project Setup

### What was required

- Create a Django project and one app.
- Use PostgreSQL via Docker.
- Store credentials in `.env`.
- Install DRF, SimpleJWT, and `python-dotenv`.
- Add `rest_framework` to installed apps.
- Pin dependencies in `requirements.txt`.

### How it was implemented

- The Django project root is `TeamBoard`.
- The single app is `api`.
- PostgreSQL is configured in `docker-compose.yml`.
- Credentials are loaded from `.env` in `TeamBoard/settings.py`.
- Dependencies are pinned in `requirements.txt`.
- `rest_framework` and `rest_framework_simplejwt` are added to `INSTALLED_APPS`.

## Step 2: JWT Configuration

### What was required

- Protect endpoints globally by default using JWT authentication.
- Override global protection on public endpoints.

### How it was implemented

In `TeamBoard/settings.py`:

- `DEFAULT_AUTHENTICATION_CLASSES` is set to `JWTAuthentication`.
- `DEFAULT_PERMISSION_CLASSES` is set to `IsAuthenticated`.

This means every API endpoint requires a valid JWT unless it explicitly opts out.

The public endpoints opt out with:

- `@authentication_classes([])`
- `@permission_classes([])`

These decorators are applied on:

- `register_company`
- `login_company`

## Step 3: Models and Migrations

### Implemented Models

#### Company

Represents a B2B customer profile linked to Django's built-in `User` model.

Fields:

- `user`: one-to-one relation with `User`
- `company_name`: company display name
- `api_key`: unique platform-issued API key
- `role`: `admin` or `client`
- `created_at`: auto timestamp

#### KBEntry

Represents a question-and-answer record in the knowledge base.

Fields:

- `question`
- `answer`
- `category`
- `created_at`

Categories:

- `api`
- `database`
- `cloud`
- `framework`
- `general`

#### QueryLog

Tracks each knowledge base search request.

Fields:

- `company`
- `search_term`
- `results_count`
- `queried_at`

### Migration

The initial migration exists in `api/migrations/0001_initial.py` and creates the three project-specific tables.

## Step 4: Auto-Create Company Profile and API Key

### Requirement

When a new `User` is created:

- a `Company` profile must be created automatically
- an `api_key` must be generated automatically
- this must happen in a signal, not in the view
- first creation must be detected using `instance._state.adding`

### How it works

The implementation is split into two files:

- `api/signals.py`
- `api/apps.py`

### Signal flow

1. A `pre_save` signal stores whether the instance is being created.
2. A `post_save` signal checks the pre-save flag.
3. If the user was newly created, a `Company` is created automatically.
4. The API key is generated with `secrets.token_urlsafe(32)`.

### Why `pre_save` is used

By the time `post_save` executes, `instance._state.adding` has already changed. To preserve the required first-save detection pattern, the code snapshots the value in `pre_save` and uses that snapshot in `post_save`.

## Step 5: Register and Login Endpoints

### Register Endpoint

`POST /api/auth/register/`

#### Purpose

Creates a new user account, allows the signal to auto-create the company profile and API key, updates `company_name`, and returns a JWT access token.

#### Request Body

```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```

#### Success Response

```json
{
  "username": "acmecorp",
  "company_name": "Acme Corp",
  "api_key": "generated-api-key",
  "access": "jwt-access-token"
}
```

#### Implementation Notes

- Public endpoint, no JWT required.
- Rejects duplicate usernames with status `400`.
- Does not accept `role` from the request.
- Does not generate `api_key` in the view.

### Login Endpoint

`POST /api/auth/login/`

#### Purpose

Authenticates a company user and returns a fresh JWT access token plus company credentials.

#### Request Body

```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```

#### Success Response

```json
{
  "access": "jwt-access-token",
  "company_name": "Acme Corp",
  "api_key": "generated-api-key"
}
```

#### Implementation Notes

- Public endpoint, no JWT required.
- Uses Django `authenticate()`.
- Invalid credentials return `401`.

## Step 6: Seed the Knowledge Base

### Requirement

Insert at least 10 knowledge base entries with mixed categories and repeated keywords.

### How it was implemented

A custom management command was added:

```bash
python manage.py seed_kb_entries --reset
```

This command:

- optionally clears existing `KBEntry` records
- inserts 12 predefined entries
- uses multiple categories
- includes repeated keywords such as `select_related`, `transaction.atomic`, `JWT`, and `Q objects`

## Step 7: Knowledge Base Query Endpoint

### Endpoint

`POST /api/kb/query/`

### Purpose

Searches the knowledge base by keyword in both the `question` and `answer` fields and logs the query.

### Request Body

```json
{
  "search": "select_related"
}
```

### Success Response

```json
{
  "search": "select_related",
  "count": 2,
  "results": [
    {
      "id": "1",
      "question": "What is select_related in Django ORM?",
      "answer": "select_related performs a SQL JOIN and fetches related objects in one query.",
      "category": "database"
    }
  ]
}
```

### Implementation Details

- Protected endpoint, JWT required.
- The company is taken from `request.user.company`.
- It never trusts a company identifier from the request body.
- Search uses `Q(question__icontains=...) | Q(answer__icontains=...)`.
- Search execution and `QueryLog` creation happen inside one `transaction.atomic()` block.
- Blank or missing search terms return `400`.
- Zero-result searches still return `200` and still create a `QueryLog` row.

## Step 8: Admin Permission and Usage Summary

### Custom Permission

The custom DRF permission class is `IsAdminUser` in `api/permissions.py`.

It checks:

- the request user is authenticated
- the user has a related company profile
- `request.user.company.role == Company.Role.ADMIN`

It does not use:

- `is_staff`
- `is_superuser`

### Endpoint

`GET /api/admin/usage-summary/`

### Purpose

Returns aggregated platform-wide usage statistics.

### Response Shape

```json
{
  "total_queries": 3,
  "active_companies": 2,
  "top_search_terms": [
    {
      "search_term": "select_related",
      "count": 2
    }
  ]
}
```

### Aggregations Used

- total queries: `aggregate(total=Count('id'))`
- active companies: `values('company').distinct().count()`
- top terms: `values('search_term').annotate(count=Count('id')).order_by('-count')[:5]`

## API Routes

The project-level router includes the `api` app under `/api/`.

Available routes:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/kb/query/`
- `GET /api/admin/usage-summary/`

## File-by-File Explanation

### Root Files

#### `manage.py`

Django command entry point. Used to run migrations, tests, the development server, and custom management commands.

#### `requirements.txt`

Pinned Python dependencies for reproducible local setup.

#### `.env`

Contains local environment variables used by the Django settings file and Docker Compose.

#### `.env.example`

Template for required environment variables.

#### `.gitignore`

Prevents committing `.env`, the virtual environment, and generated local files.

#### `docker-compose.yml`

Defines the PostgreSQL container used by the application.

### `TeamBoard/` Directory

#### `settings.py`

Contains:

- installed apps
- middleware
- PostgreSQL configuration
- environment variable loading
- JWT global configuration

#### `urls.py`

Routes:

- Django admin under `/admin/`
- app API routes under `/api/`

#### `asgi.py` and `wsgi.py`

Standard Django deployment entry points.

### `api/` Directory

#### `models.py`

Defines the three domain models:

- `Company`
- `KBEntry`
- `QueryLog`

#### `signals.py`

Creates `Company` profiles and API keys automatically whenever a new `User` is created.

#### `apps.py`

Ensures signals are registered through `ready()`.

#### `views.py`

Contains the four function-based API endpoints.

#### `urls.py`

Maps URL paths to the four views.

#### `permissions.py`

Defines `IsAdminUser`.

#### `tests.py`

Contains API integration tests for:

- register success
- duplicate register failure
- login success
- invalid login failure
- unauthenticated query
- blank query
- query logging
- zero-result query logging
- client forbidden on usage summary
- admin success on usage summary

#### `management/commands/seed_kb_entries.py`

Populates the knowledge base with initial content.

#### `migrations/0001_initial.py`

Creates the initial database schema for the `api` app.

## Testing

Run all API tests:

```bash
python manage.py test api
```

### What the tests cover

- registration and duplicate username handling
- login success and failure
- JWT protection on the query endpoint
- search behavior with results
- search behavior with zero results
- query logging behavior
- admin access control
- usage summary aggregation

## Live Verification Already Performed

The project was manually smoke-tested over live HTTP with these scenarios:

- register company
- duplicate username
- valid login
- invalid login
- query without token
- query with token and matching results
- query with token and zero results
- query with missing search
- usage summary with client token
- usage summary with admin token
- QueryLog row verification after query scenarios

The automated test suite also passed successfully.

## Example cURL Requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "acmecorp",
    "password": "securepass123",
    "company_name": "Acme Corp",
    "email": "dev@acmecorp.com"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "acmecorp",
    "password": "securepass123"
  }'
```

### Query Knowledge Base

```bash
curl -X POST http://127.0.0.1:8000/api/kb/query/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{
    "search": "select_related"
  }'
```

### Usage Summary

```bash
curl -X GET http://127.0.0.1:8000/api/admin/usage-summary/ \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Troubleshooting

### Docker permission denied

If `docker compose up -d` fails with a permission error on `/var/run/docker.sock`:

```bash
sudo usermod -aG docker $USER
```

Then fully log out and log back in, or reboot.

### PostgreSQL connection refused

If migrations fail with connection errors:

- confirm Docker is running
- confirm the Postgres container is up
- inspect logs with `docker compose logs --tail=50 db`

### Missing environment variable error

If Django raises `ImproperlyConfigured`, compare your `.env` against `.env.example` and fill in all required values.

## Stop the Application

### Stop Django development server

Press `Ctrl+C` in the terminal where `runserver` is running.

### Stop PostgreSQL container

```bash
docker compose down
```

## Summary

This project implements a secure, test-covered Django backend for TeamBoard with:

- JWT authentication by default
- public registration and login
- automatic company and API key creation via signals
- protected knowledge base querying
- atomic query logging
- admin-only usage analytics
- PostgreSQL and Docker-based local setup
- seeding and automated verification
