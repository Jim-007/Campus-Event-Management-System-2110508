# CampusConnect — Technical Design Document (TDD)

**Document version:** 1.0  
**Project name:** CampusConnect  
**Architecture:** React + TypeScript SPA, FastAPI REST API, relational database  
**Status:** Course project proposal

## 1. Purpose and Design Goals

This document describes the proposed architecture, modules, data model, REST API, authentication, authorization, and delivery plan for CampusConnect. The design prioritizes a small, understandable system that demonstrates course outcomes rather than unnecessary technology.

Design goals:
1. Keep frontend and backend responsibilities separate.
2. Use REST endpoints with consistent JSON schemas and HTTP status codes.
3. Centralize business rules in the backend.
4. Enforce authentication, RBAC, scopes, and resource ownership on the server.
5. Deliver core workflows in the MVP and add security/deployment in Beta.
6. Make the application straightforward to test and maintain.

## 2. Technology Choices

| Layer | Proposed technology | Rationale |
|---|---|---|
| Frontend | React.js + TypeScript | Required by course; component-based UI and type checking |
| Routing | React Router | Client-side navigation |
| HTTP client | Fetch API or Axios | Communicate with REST API |
| Styling | Tailwind CSS or plain CSS | Keep UI implementation simple |
| Backend | FastAPI + Python | Required by course; request validation and OpenAPI docs |
| Validation | Pydantic | Validate API input/output |
| ORM | SQLAlchemy | Relational persistence |
| Database | SQLite for local MVP; PostgreSQL for Beta deployment if available | Simple local setup and production-capable option |
| Authentication | JWT access token in Beta | Stateless API authentication |
| Password hashing | Argon2id or bcrypt through a maintained password-hashing library | Never store plaintext passwords |
| API testing | Swagger UI and Postman | Manual endpoint validation |
| Version control | Git + GitHub | Branch, issue, and PR workflow |

Versions should be pinned in project dependency files after the development environment is selected.

## 3. High-Level Architecture

```text
Browser
  |
  | React + TypeScript UI
  | - Public event pages
  | - Student dashboard
  | - Organizer dashboard
  | - Admin dashboard
  |
  | HTTPS/HTTP JSON requests (Bearer token for protected Beta endpoints)
  v
FastAPI application (/api/v1)
  |
  | Routers -> Authentication/Authorization -> Services -> SQLAlchemy
  | Pydantic validation             | business rules
  v
Relational database (SQLite local; PostgreSQL deployment option)
```

### 3.1 Request Flow
1. A user interacts with the React UI.
2. The frontend sends a JSON request to `/api/v1`.
3. FastAPI validates path, query, and body parameters using Pydantic schemas.
4. For protected Beta endpoints, the authentication dependency validates the access token.
5. Scope and resource-ownership checks run before protected data is accessed or changed.
6. The service layer applies business rules.
7. SQLAlchemy reads or writes the database.
8. FastAPI returns a response schema and appropriate HTTP status code.
9. The frontend updates the page or displays an error.

## 4. Suggested Repository Structure

```text
campusconnect/
├── docs/
│   ├── PRD.md
│   ├── SRS.md
│   └── TDD.md
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # settings, security, scopes
│   │   ├── api/           # routers
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # business logic
│   │   └── db/            # session and initialization
│   ├── tests/
│   └── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

This is a proposed structure; the team may adapt it while preserving separation of concerns.

## 5. Database Design

### 5.1 Entities

**User**
- `id` INTEGER/UUID, primary key
- `name` VARCHAR, not null
- `email` VARCHAR, unique and not null
- `password_hash` VARCHAR, not null in Beta
- `role` ENUM/string: `student`, `organizer`, `admin`
- `is_active` BOOLEAN, default true
- `created_at` timestamp

**Event**
- `id` INTEGER/UUID, primary key
- `title` VARCHAR, not null
- `description` TEXT, not null
- `category` VARCHAR, not null
- `venue` VARCHAR, not null
- `start_at` timestamp, not null
- `end_at` timestamp, not null
- `capacity` INTEGER, positive
- `status` ENUM/string: `draft`, `published`, `cancelled`
- `organizer_id` foreign key to `User.id`
- `created_at`, `updated_at` timestamps

**Registration**
- `id` INTEGER/UUID, primary key
- `user_id` foreign key to `User.id`
- `event_id` foreign key to `Event.id`
- `status` ENUM/string: `registered`, `cancelled`
- `registered_at` timestamp

### 5.2 Relationships

```text
User (1) -------- (many) Event
  |                  organizer_id
  |
  +------------ (many) Registration (many) ------------ Event
                   user_id                         event_id
```

- One organizer can own many events.
- One student can have many registrations.
- One event can have many registrations.
- A registration belongs to one user and one event.

### 5.3 Constraints and Indexes
- Unique index on normalized `User.email`.
- Foreign keys from Event to User and Registration to User/Event.
- Check constraint or service validation that `capacity > 0`.
- Check constraint or service validation that `end_at > start_at`.
- Unique active registration for each `(user_id, event_id)`. Depending on database support, use a partial unique index or a reliable transaction/service approach. If cancelled registrations are retained, re-registration behavior must be implemented consistently.
- Index `Event.start_at`, `Event.status`, `Event.category`, and `Registration.event_id` for common list queries.
- Capacity checks and registration insertion should occur in a transaction to reduce overbooking risk.

## 6. API Design

Base path: `/api/v1`  
Payload format: JSON  
Authentication: public endpoints in MVP; JWT Bearer access token for protected Beta endpoints.

### 6.1 Event Endpoints

| Method and path | Purpose | Access / Release |
|---|---|---|
| `GET /events` | List published events; query params may include `q`, `category`, `date_from`, `date_to`, `page`, `limit` | Public, MVP |
| `GET /events/{event_id}` | Read event details | Public for published events, MVP |
| `POST /events` | Create event | MVP; Beta requires `event:create` |
| `PATCH /events/{event_id}` | Update event fields | MVP; Beta requires ownership + `event:update_own` or admin scope |
| `DELETE /events/{event_id}` | Delete event | MVP; Beta organizer owner/admin permission |
| `POST /events/{event_id}/publish` | Publish event | Beta, owner or admin |
| `POST /events/{event_id}/cancel` | Cancel event | Beta, owner or admin |

For Beta, use a draft status until an authorized organizer publishes an event. Public event listing returns only published, non-cancelled events.

### 6.2 Registration Endpoints

| Method and path | Purpose | Access / Release |
|---|---|---|
| `POST /events/{event_id}/registrations` | Register current user for event | MVP; Beta requires `registration:create` |
| `GET /registrations/me` | List current user's registrations | Beta, `registration:read_own` |
| `DELETE /registrations/{registration_id}` | Cancel own registration | MVP/Beta; Beta checks ownership and `registration:cancel_own` |
| `GET /organizer/events/{event_id}/registrations` | List participants for event | Beta, organizer owns event + `registration:read_event` |
| `GET /admin/registrations` | Administrative registration overview | Beta, admin only if needed |

The MVP may use a development-only test identity for registration while authentication is not yet implemented. This must be documented and removed or replaced by authenticated identity in Beta.

### 6.3 Authentication and User Endpoints

| Method and path | Purpose | Access / Release |
|---|---|---|
| `POST /auth/register` | Create student account | Public, Beta |
| `POST /auth/login` | Verify credentials and issue access token | Public, Beta |
| `GET /users/me` | Read current user's profile | Authenticated, Beta |
| `PATCH /users/me` | Update allowed profile fields | Authenticated, Beta |
| `GET /admin/users` | List users | `user:manage`, Beta |
| `PATCH /admin/users/{user_id}` | Change role or active status | `user:manage`, Beta |

Public registration must always assign the `student` role. It must not accept an Admin or Organizer role from the client. An administrator assigns organizer privileges.

### 6.4 Example Request and Response

Create event request:
```json
{
  "title": "Programming Workshop",
  "description": "An introductory campus workshop.",
  "category": "Workshop",
  "venue": "Room 302",
  "start_at": "2026-11-15T10:00:00",
  "end_at": "2026-11-15T12:00:00",
  "capacity": 40
}
```

Example success response:
```json
{
  "id": 12,
  "title": "Programming Workshop",
  "category": "Workshop",
  "venue": "Room 302",
  "start_at": "2026-11-15T10:00:00",
  "end_at": "2026-11-15T12:00:00",
  "capacity": 40,
  "status": "draft",
  "organizer_id": 5
}
```

In Beta, response schemas must never include password hashes or secrets. Exact timestamp timezone policy should be agreed upon; store and exchange timestamps consistently, preferably in UTC.

### 6.5 HTTP Status Codes

- `200 OK`: successful read/update.
- `201 Created`: resource created.
- `204 No Content`: successful delete/cancel with no response body.
- `400 Bad Request`: business-rule violation where appropriate.
- `401 Unauthorized`: missing or invalid authentication.
- `403 Forbidden`: authenticated user lacks permission.
- `404 Not Found`: resource not found or deliberately concealed as inaccessible.
- `409 Conflict`: duplicate registration or capacity/state conflict.
- `422 Unprocessable Entity`: request schema validation error.
- `500 Internal Server Error`: unexpected server error; do not expose stack traces to clients.

## 7. Authentication and Security Design (Beta)

### 7.1 Authentication Flow
1. User submits email and password to `POST /auth/login`.
2. Backend finds the normalized email and verifies the password hash.
3. On success, backend issues a signed, short-lived JWT access token with subject (`sub`), expiry (`exp`), and relevant scope claims.
4. Frontend sends the token in `Authorization: Bearer <token>` for protected API calls.
5. FastAPI validates signature and expiry before resolving the current user.
6. Invalid/expired tokens receive HTTP 401.

For a course SPA, storing tokens in memory is preferable to long-lived browser storage where practical. If local storage is used for simplicity, document the XSS trade-off and avoid storing sensitive information there. Do not store passwords in browser storage. Refresh-token support is out of scope unless required.

### 7.2 Password and Secret Handling
- Use Argon2id or bcrypt through a maintained library.
- Never log passwords, token values, or signing secrets.
- Load `JWT_SECRET_KEY`, database URL, and other environment-specific configuration from environment variables.
- Commit `.env.example` with placeholder values only; ignore `.env`.
- Use HTTPS for deployment.
- Configure CORS to allow only the frontend origins needed by the application.

### 7.3 Scopes and RBAC

Suggested scopes:
- `event:read`
- `event:create`
- `event:update_own`
- `event:manage_all`
- `registration:create`
- `registration:read_own`
- `registration:cancel_own`
- `registration:read_event`
- `user:manage`
- `profile:read_own`
- `profile:update_own`

Suggested mapping:
- **Student:** `event:read`, `registration:create`, `registration:read_own`, `registration:cancel_own`, `profile:read_own`, `profile:update_own`.
- **Organizer:** `event:read`, `event:create`, `event:update_own`, `registration:read_event`, `profile:read_own`, `profile:update_own`.
- **Admin:** `event:read`, `event:manage_all`, `registration:read_event`, `registration:read_own` for oversight if needed, `user:manage`, `profile:read_own`.

Scopes are capability checks, not substitutes for ownership checks. For example, an organizer with `event:update_own` must still be denied when the event's `organizer_id` does not match the authenticated user's ID. Admin access should use explicit administrative permissions rather than relying on frontend behavior.

### 7.4 Security Controls
- Validate and normalize all client input.
- Apply authorization to every protected API endpoint.
- Enforce object-level authorization for events and registrations.
- Prevent mass assignment by using explicit Pydantic request schemas; never accept role, owner ID, or internal status fields unless that operation is specifically authorized.
- Apply database constraints for unique email and registration consistency.
- Return generic login errors.
- Limit CORS origins.
- Do not expose debug tracebacks in deployed mode.
- Add basic rate limiting to login if feasible; otherwise document it as a production hardening item.
- Use dependency and package versions that are maintained.

## 8. Backend Module Design

- `main.py`: create FastAPI app, register routers, configure CORS, startup/shutdown.
- `core/config.py`: settings loaded from environment.
- `core/security.py`: password hashing, JWT creation/validation, current-user dependency, scope helpers.
- `db/session.py`: SQLAlchemy engine and session dependency.
- `models/`: User, Event, Registration ORM models.
- `schemas/`: Pydantic request/response schemas.
- `api/`: route handlers for auth, events, registrations, users, admin.
- `services/`: business rules for event management and registration.
- `tests/`: API, business-rule, and authorization tests.

Route handlers should remain thin: validate the request, call service logic, and return the response schema.

## 9. Frontend Module Design

Suggested pages:
- `EventsPage`: list/search/filter published events.
- `EventDetailsPage`: details and registration action.
- `LoginPage` and `RegisterPage`: Beta authentication.
- `StudentDashboard`: profile and own registrations.
- `OrganizerDashboard`: owned events and participant counts.
- `EventFormPage`: create/edit event.
- `AdminDashboard`: user and event management.
- `NotFoundPage`: unknown route.

Suggested shared components:
- `Navbar`, `EventCard`, `EventFilters`, `EventForm`, `RegistrationStatus`, `LoadingState`, `ErrorMessage`, `ProtectedRoute`.

Suggested API modules:
- `api/client.ts`: base URL and common HTTP/error handling.
- `api/events.ts`: event API functions.
- `api/registrations.ts`: registration API functions.
- `api/auth.ts`: login/register/current user.
- `api/admin.ts`: administrative API functions.

TypeScript interfaces should mirror API response schemas. Frontend route guards improve navigation but do not replace backend authorization.

## 10. MVP and Beta Implementation Plan

### MVP — Mid-term Demo
1. Initialize React + TypeScript and FastAPI projects.
2. Create database models and initialize SQLite.
3. Implement event list/detail/create/update/delete endpoints.
4. Implement registration, cancellation, duplicate checks, and capacity validation.
5. Test endpoints with Swagger UI/Postman.
6. Build a basic React event listing, event detail, event form, and registration interface.
7. Document local run instructions.

### Beta — Final Demo
1. Add user registration/login and password hashing.
2. Add JWT access-token validation.
3. Add role assignment and permission/scope dependencies.
4. Enforce event ownership and registration privacy.
5. Build role-specific dashboards and admin user management.
6. Add tests for allowed and denied role actions.
7. Configure deployment, HTTPS, CORS, and environment variables.
8. Update documentation with deployment URL and final API behavior.

## 11. Testing Strategy

### Unit Tests
- Event time/capacity validation.
- Duplicate registration rule.
- Event capacity rule.
- Permission mapping and ownership checks.

### API Integration Tests
- Event CRUD.
- Registration and cancellation.
- Invalid request schema.
- Missing/invalid token.
- Insufficient scope.
- Organizer access to own versus another organizer's event.
- Student access to own versus another student's registrations.
- Admin user management.

### Frontend Manual Tests
- Browse/search events.
- Validation and error states.
- Registration confirmation and cancellation.
- Correct dashboard for each role.
- Direct navigation to protected pages.
- Responsive layout at desktop and mobile widths.

### Minimum Beta Security Test Matrix
| Test | Expected result |
|---|---|
| No token calls protected endpoint | 401 |
| Student calls `user:manage` endpoint | 403 |
| Organizer edits own event | Allowed |
| Organizer edits another organizer's event | Denied |
| Student reads own registrations | Allowed |
| Student reads another user's registrations | Denied/no data disclosure |
| Public registration submits `role=admin` | Role ignored/rejected; account remains student |
| Expired or tampered token | 401 |

## 12. Deployment and Configuration

Local development:
- Frontend runs using the selected React tooling (for example, Vite).
- Backend runs using Uvicorn.
- SQLite database file is stored locally and excluded from Git if it contains real user data.
- CORS permits the local frontend origin.

Beta deployment:
- Deploy frontend and backend separately or through a supported combined setup.
- Use a managed PostgreSQL database if available.
- Configure production environment variables through the hosting platform.
- Set CORS to the deployed frontend origin.
- Enable HTTPS.
- Run database migrations or a documented schema initialization step.
- Add a health endpoint such as `GET /health`.
- Do not commit credentials, real user data, or production tokens.

Required configuration examples in `.env.example`:
```text
DATABASE_URL=sqlite:///./campusconnect.db
JWT_SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_ORIGIN=http://localhost:5173
```

These are examples only; the production secret must be generated securely and must never use the placeholder.

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Too many features delay delivery | Keep to MVP/Beta list; postpone optional enhancements |
| RBAC implemented only in UI | Enforce scopes and ownership in FastAPI dependencies/services |
| Capacity overbooking | Use transaction-safe checks and database constraints |
| Inconsistent API types | Define Pydantic schemas and matching TypeScript types early |
| Secret leakage | Use `.env`, `.gitignore`, and `.env.example` placeholders |
| Deployment differences | Test deployment configuration before final week |

## 14. Decisions to Confirm

- Instructor's required document template and citation/diagram conventions.
- Final hosting provider and whether PostgreSQL is available.
- Whether the team will use Alembic for database migrations.
- Whether organizer accounts are created by an admin or approved from requests.
- Whether event deletion should be hard deletion or soft cancellation. Recommended: cancel published events and restrict hard deletion once registrations exist.
