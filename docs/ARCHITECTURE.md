# Architecture note

| Layer | Files | Job | Imports Flask? |
|---|---|---|---|
| Web / handlers | `app/routes/*.py`, `app/schemas.py`, `app/routes/helpers.py` | HTTP in, method call, HTTP out. `schemas.py` validates untrusted input. | Yes (routes), no (schemas) |
| Service | `app/services/*.py` | One use case each (`enroll`, `drop`, `create_course` ...). Coordinates domain and repositories. Logs events. | No |
| Domain | `app/domain/*.py` | Entities and rules true everywhere: `Course.reserve_seat()` (no seats left), `Course.change_seats()` (not below enrolled). | No |
| Repository | `app/repositories/*.py`, `app/repositories/_memory.py`  | The only storage code. In-memory today; copies rows in and out like a SQL repo would. | No |
| Cross-cutting | `app/config.py`, `app/errors.py`, `app/error_handlers.py`, `app/middleware.py`, `app/logging_config.py` | Settings, error types, RFC 9457 responses, request ID + access log, logging setup. | Only `error_handlers`, `middleware` |
| Composition root | `app/__init__.py` (`create_app`) | The one place where config is read, objects are created and wired, blueprints registered. | Yes |

## Rules the code follows
- Handlers contain no SQL and no business rules.
- Services raise `NotFound`, `Conflict`, `ValidationFailed`; they never build HTTP responses.
- One error handler turns every failure into `application/problem+json`;Unexpected errors return a sanitized HTTP 500 response
to the client, while the full exception traceback is logged
on the server.
- Services receive repositories (and `max_seats`) through their constructors.

## Request walk-through: `POST /enrollments`
1. `middleware.assign_request_id` sets the request ID.
2. Router matches `routes/enrollments.py: enroll()`.
3. `schemas.parse_enrollment` validates `studentId` / `courseId` (422 with field errors).
4. `EnrollmentService.enroll` loads student and course (404), rejects duplicates (409), calls `Course.reserve_seat()` (409 when full), saves, logs.
5. Handler returns 201 with a `Location` header.
6. `middleware.finish_request` adds `X-Request-ID`, writes the access log line.
Any exception on the way is caught by `error_handlers.py`.

## Changing storage
Replace the classes in `app/repositories/` (same method names) and return them from `build_repositories()` in `app/repositories/__init__.py`. No service, domain, route or `create_app` file changes.
