# Submission checklist (CSE 3102L Topic 04)

## 1. Git repository with meaningful commits
```bash
cd enrollment-api
git init -b main
git add .gitignore .env.example requirements*.txt requirements.lock pytest.ini
git commit -m "chore: project setup, pinned dependencies, env example"
git add app/errors.py app/config.py app/logging_config.py
git commit -m "feat: config from environment, error types, logging setup"
git add app/domain app/repositories
git commit -m "feat: domain rules (seats) and in-memory repositories"
git add app/services
git commit -m "feat: student, course and enrollment services"
git add app/schemas.py app/routes app/middleware.py app/error_handlers.py app/__init__.py run.py
git commit -m "feat: REST endpoints, request ID middleware, RFC 9457 errors"
git add tests pytest.ini
git commit -m "test: integration, lifecycle, live HTTP, service and config tests"
git add README.md docs SUBMISSION.md
git commit -m "docs: README and architecture note"
# create an empty repo on GitHub/GitLab, then:
git remote add origin <YOUR-REPO-URL>
git push -u origin main
```
Check: `git status` is clean and `.env` / `.venv` are NOT in `git ls-files`.
Submit the repository URL.

## 2. README: framework and why, how to run, how to test
Done in `README.md`. Re-read it and make the "Why Flask?" sentence your own words.

## 3. Architecture note
Done in `docs/ARCHITECTURE.md` (file to layer table).

## 4. Five or more automated tests including failure paths
`pytest` runs 102 tests (404, 409, 413, 422, 500 paths included).

## 5. AI-use disclosure (replace the README section with true statements)
Draft, edit to match what you really did:
- AI (Claude) generated the first version of the project code, tests and documentation from the lab slides.
- I ran the project from a fresh clone and ran `pytest` (all passing).
- I read every file and can explain it; I changed: <list your own changes>.
- I tried the curl examples by hand and saw the 409 and 422 responses.
- Things I verified against official docs: <Flask routing/errorhandler, RFC 9457, ...>.

## Final self-check from the slides
- [ ] Fresh clone runs using only the README
- [ ] `tests/test_services_without_http.py` shows a use case running without a server
- [ ] Storage can change by editing only `app/repositories/`
- [ ] `test_unexpected_error_is_hidden_from_client_but_logged_in_full` shows the hidden error
- [ ] You can explain every line
