# Course Enrollment API

Small REST backend (Flask, Python 3.11+) for CSE 3102L Topic 04.
Domain: **students**, **courses with limited seats**, **enrollments**.
Failing business rules: *no seats left* (409), *already enrolled* (409), *cannot shrink seats below enrolled* (409), *cannot delete a student/course that still has enrollments* (409).

**Why Flask?** Small and readable, lets me wire the layers by hand so I can explain every line, and it matches the course starter project.

## Run
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # optional; defaults work without it
python run.py                        # http://127.0.0.1:5000
```

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python run.py
```

## Test (replaces manual Postman checking)
```bash
pytest            # 102 tests, about 1-2 seconds
pytest -v         # list every test name
```
| File | What it checks |
|---|---|
| `test_students_api.py`, `test_courses_api.py`, `test_enrollments_api.py` | Integration tests: every endpoint through the real Flask app, with success and failure cases, status codes, `Location`, error body, side effects on seats |
| `test_lifecycle.py` | One scripted create, read, update, enroll, fail, drop, delete run (a Postman "collection run") |
| `test_live_http.py` | Starts a real server on a free port and calls it over HTTP with urllib |
| `test_platform.py` | Request IDs, access log, no personal data in logs, 404/405/413/500 in the same error format, stack trace hidden from client but logged |
| `test_services_without_http.py` | Domain rules, services and repositories with no web server; fake repository injection |
| `test_config.py` | Settings and fail-fast on bad values |

## API
| Method and path | Success | Failures |
|---|---|---|
| `POST /students` `{name,email}` | 201 + `Location` | 422, 409 duplicate email |
| `GET /students`, `GET /students/{id}` | 200 | 404 |
| `PUT /students/{id}` | 200 | 422, 404, 409 |
| `DELETE /students/{id}` | 204 | 404, 409 has enrollments |
| `POST /courses` `{code,title,seats}` | 201 + `Location` | 422, 409 duplicate code |
| `GET /courses[?available=true]`, `GET /courses/{id}` | 200 | 404 |
| `PUT /courses/{id}` | 200 | 422, 404, 409 |
| `DELETE /courses/{id}` | 204 | 404, 409 has students |
| `POST /enrollments` `{studentId,courseId}` | 201 + `Location` | 422, 404, 409 full / duplicate |
| `GET /enrollments[?studentId=&courseId=]`, `GET /enrollments/{id}` | 200 | 422, 404 |
| `DELETE /enrollments/{id}` (drop, frees the seat) | 204 | 404 |
| `GET /health` | 200 | |

Errors are RFC 9457 `application/problem+json`:
```json
{"type": "/problems/conflict", "title": "Request conflicts with current state",
 "status": 409, "detail": "No seats left in course CSE3102L", "requestId": "c631fdb3d304"}
```
Validation errors add `"errors": [{"field": "seats", "message": "must be at least 1"}]`.

## Try it by hand (curl)
```bash
curl -i -X POST localhost:5000/students -H 'Content-Type: application/json' -d '{"name":"Rahim","email":"rahim@example.com"}'
curl -i -X POST localhost:5000/courses  -H 'Content-Type: application/json' -d '{"code":"CSE3102L","title":"Web Lab","seats":1}'
curl -i -X POST localhost:5000/enrollments -H 'Content-Type: application/json' -d '{"studentId":1,"courseId":1}'
curl -i -X POST localhost:5000/enrollments -H 'Content-Type: application/json' -d '{"studentId":1,"courseId":1}'   # 409
```

## Configuration
Environment variables (see `.env.example`): `APP_ENV`, `LOG_LEVEL`, `MAX_SEATS`, `MAX_BODY_BYTES`, `PORT`. Invalid values stop the app at startup. `.env` is git-ignored.

## Dependencies
`requirements.txt` (direct, pinned), `requirements-dev.txt` (adds pytest), `requirements.lock` (full `pip freeze`). Audit with `pip install pip-audit && pip-audit -r requirements.txt`.

## Security choices
Allow-listed input fields (no mass assignment), validated and size-limited bodies, request IDs sanitised, no personal data in logs, no stack traces to clients, debug mode off, `nosniff` header. Not included (out of scope): authentication and authorization.

## Limits
Data lives in memory and resets on restart; single process only. Swap `app/repositories/` for a database (see `docs/ARCHITECTURE.md`, which also maps every file to its layer).

## AI-use disclosure

- **What AI helped with:**
 AI was used for understanding the project architecture, explaining Flask concepts, reviewing code structure, and assisting with debugging and documentation.

- **What I verified myself:**
 I installed the dependencies, ran the Flask application, executed the test suite, verified that all 102 tests passed, and reviewed the project files and API behavior.