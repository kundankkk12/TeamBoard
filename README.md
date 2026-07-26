# TeamBoard Backend

## Overview

TeamBoard is a Django REST API for an AI-powered knowledge base platform. Companies can register, log in, query knowledge base entries, and generate usage logs. Admin companies can view aggregated usage statistics.

## Features

- Public company registration
- Public company login
- Protected knowledge base search
- Query usage logging
- Admin-only usage summary
- PostgreSQL database via Docker
- Automatic `Company` creation and `api_key` generation via signals

## Tech Stack

- Python 3.14
- Django 6.0.7
- Django REST Framework 3.17.1
- SimpleJWT 5.5.1
- PostgreSQL 16
- Docker Compose

## Project Structure

```text
TeamBoard/
├── TeamBoard/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── api/
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── signals.py
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   ├── migrations/
│   └── management/commands/seed_kb_entries.py
├── postman/teamboard-postman-collection.json
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── manage.py
```

## Environment Variables

Create a `.env` file in the project root using `.env.example`.

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

## Installation

### 1. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=50 db
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Seed knowledge base entries

```bash
python manage.py seed_kb_entries --reset
```

### 6. Run the server

```bash
python manage.py runserver 0.0.0.0:8000
```

Server URL:

```text
http://127.0.0.1:8000/
```

## API Endpoints

### Register Company

- Method: `POST`
- URL: `/api/auth/register/`
- Access: Public

### Login Company

- Method: `POST`
- URL: `/api/auth/login/`
- Access: Public

### Query Knowledge Base

- Method: `POST`
- URL: `/api/kb/query/`
- Access: JWT required

### Usage Summary

- Method: `GET`
- URL: `/api/admin/usage-summary/`
- Access: Admin company only

## Implementation Notes

### Authentication

- JWT is enabled globally in `REST_FRAMEWORK` settings.
- Register and login explicitly set empty `authentication_classes` and `permission_classes`.

### Signals

- `api/signals.py` auto-creates a `Company` whenever a new `User` is created.
- `api_key` is generated with `secrets.token_urlsafe(32)`.
- Signal registration happens through `ApiConfig.ready()` in `api/apps.py`.

### Permissions

- `api/permissions.py` contains `IsAdminUser`.
- Admin access is based on `request.user.company.role`.

### Query Logging

- Queries use `Q(question__icontains=...) | Q(answer__icontains=...)`.
- Search and `QueryLog` creation are wrapped in `transaction.atomic()`.

## Postman Collection

Collection file:

```text
postman/teamboard-postman-collection.json
```

Covered scenarios:

1. Register a new company
2. Register with duplicate username
3. Login with valid credentials
4. Login with wrong password
5. Query KB without token
6. Query KB with results
7. Query KB with no results
8. Query KB with missing search field
9. Usage summary with client token
10. Usage summary with admin token
11. Verify `QueryLog` rows in pgAdmin

## pgAdmin Verification

Use pgAdmin Query Tool on the `teamboard` database and run:

```sql
SELECT q.id,
       u.username,
       q.search_term,
       q.results_count,
       q.queried_at
FROM api_querylog q
JOIN api_company c ON q.company_id = c.id
JOIN auth_user u ON c.user_id = u.id
ORDER BY q.queried_at DESC;
```

Confirm:

- one row exists for the successful search term
- one row exists for the zero-result search term with `results_count = 0`

## Submission Files

- Backend source code: `TeamBoard/`, `api/`, `manage.py`
- Docker setup: `docker-compose.yml`
- Environment template: `.env.example`
- Pinned dependencies: `requirements.txt`
- Signals: `api/signals.py`
- Permission class: `api/permissions.py`
- Postman collection: `postman/teamboard-postman-collection.json`
- Documentation: `README.md`

## Final Verification Commands

```bash
docker compose ps
python manage.py check
python manage.py migrate
python manage.py seed_kb_entries --reset
python manage.py runserver
```

## Troubleshooting

### Docker permission denied

```bash
sudo usermod -aG docker $USER
```

Log out and log back in afterward.

### PostgreSQL connection issues

```bash
docker compose up -d
docker compose logs --tail=50 db
```

### Missing environment variables

Compare `.env` against `.env.example` and fill in all required values.

## License

This project was created for an assignment submission.
