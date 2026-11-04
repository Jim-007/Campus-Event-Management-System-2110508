# CampusConnect — Software Requirements Specification (SRS)

**Document version:** 1.0  
**Project name:** CampusConnect  
**Standard basis:** Structured requirements specification, informed by the organization of ISO/IEC/IEEE 29148. This student document is not a claim of formal compliance.  
**Status:** Course project proposal

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for CampusConnect, a campus event management web application. It defines expected system behavior, user roles, interfaces, constraints, and acceptance criteria for the MVP and Beta releases.

### 1.2 Scope
CampusConnect lets users discover campus events, register for events, and manage event information according to their role. The frontend uses React.js with TypeScript. The backend uses FastAPI and exposes REST APIs. A relational database stores users, events, and registrations.

### 1.3 Definitions
- **MVP:** Minimum Viable Product for the mid-term demo; core functionality runs locally.
- **Beta:** Final-demo release including authentication, RBAC, security scopes, dashboards, and deployment.
- **RBAC:** Role-Based Access Control.
- **Scope/permission:** A named authorization capability required to perform a protected operation.
- **Organizer ownership:** An event is owned by the user recorded as its organizer.
- **Registration:** A user's active request to attend an event.

### 1.4 References
- Course project instructions supplied by the instructor.
- FastAPI documentation: https://fastapi.tiangolo.com/
- React documentation: https://react.dev/
- TypeScript documentation: https://www.typescriptlang.org/docs/
- OWASP API Security Top 10: https://owasp.org/www-project-api-security/

## 2. Overall Description

### 2.1 Product Perspective
CampusConnect is a browser-based client-server application. The React client sends HTTP requests to the FastAPI backend. The backend validates input, applies business rules and authorization, interacts with the relational database, and returns JSON responses.

### 2.2 User Classes

| User class | Description | Beta access |
|---|---|---|
| Visitor | Not logged in | View published events and event details; register/login |
| Student | Authenticated student | Manage own registrations and view own profile |
| Event Organizer | Authenticated organizer | Manage own events and view participants for own events |
| Admin | Authenticated administrator | Manage users, roles, all events, and oversee registrations |

Visitor access to event browsing is public. Registration and management operations require authentication in Beta.

### 2.3 Operating Environment
- Modern browser with JavaScript enabled.
- Node.js/npm environment for frontend development.
- Python environment for FastAPI backend.
- SQLite database for local development; PostgreSQL may be used for deployment.
- Git and GitHub for version control and review.

### 2.4 Design and Implementation Constraints
- Frontend must use React.js with TypeScript.
- Backend must use FastAPI with Python.
- Client-server communication must use REST APIs with JSON payloads.
- Beta must implement authentication, RBAC, and security scopes/permissions.
- Authorization must be enforced by the backend.
- No ML, AI, payment, or real-time subsystem is required.

### 2.5 Assumptions and Dependencies
- Users have access to a modern browser and internet/local network as appropriate.
- The application has a configured database.
- Beta JWT signing secrets and database URLs are provided through environment variables.
- Organizers are assigned their role by an admin or seeded for development; public self-selection of the Admin role is prohibited.

## 3. External Interface Requirements

### 3.1 User Interface
The frontend shall provide:
1. Public event listing with search/filter controls.
2. Event details page.
3. Login and registration pages.
4. Student dashboard with personal registrations.
5. Organizer dashboard with owned events and participant lists.
6. Event create/edit form.
7. Admin dashboard with user and event management.
8. Clear loading, empty, validation, success, and error states.

The interface shall be responsive and shall not expose actions the current user is not expected to perform. Backend authorization remains authoritative.

### 3.2 Software Interfaces
- React frontend communicates with FastAPI over HTTP/HTTPS.
- REST requests and responses use JSON except for standard protocol responses.
- FastAPI exposes OpenAPI documentation through Swagger UI during development.
- SQLAlchemy provides database access to SQLite or PostgreSQL.

### 3.3 Communication Interfaces
- Local development: frontend and backend may run on separate localhost ports with a configured CORS allowlist.
- Deployment: use HTTPS and configure allowed origins explicitly.
- JWT access tokens are sent using the `Authorization: Bearer <token>` header for protected requests.

## 4. Functional Requirements

Each requirement has a unique ID and release label. “MVP” requirements are targeted for the mid-term demo; “Beta” requirements are targeted for the final demo.

### 4.1 Event Discovery and Management

- **FR-01 (MVP):** The system shall return a list of published events.
- **FR-02 (MVP):** The system shall return the details of a specified published event.
- **FR-03 (MVP):** The system shall support searching events by title and filtering by category or date.
- **FR-04 (MVP):** The system shall create an event when all required fields are valid.
- **FR-05 (MVP):** The system shall retrieve, update, and delete an event by identifier.
- **FR-06 (MVP):** The system shall reject events whose end time is not later than their start time.
- **FR-07 (MVP):** The system shall require a positive event capacity.
- **FR-08 (Beta):** The system shall require an authenticated user with `event:create` to create an event.
- **FR-09 (Beta):** The system shall require `event:update_own` and verify ownership when an organizer updates their event.
- **FR-10 (Beta):** The system shall allow an admin with `event:manage_all` to manage any event.
- **FR-11 (Beta):** The system shall allow organizers to publish or cancel their own events, subject to permission checks.

### 4.2 Registration

- **FR-12 (MVP):** The system shall create a registration for a user and event when registration is allowed.
- **FR-13 (MVP):** The system shall reject duplicate active registrations for the same user and event.
- **FR-14 (MVP):** The system shall reject registrations when event capacity is full.
- **FR-15 (MVP):** The system shall list registrations for an event and registrations belonging to a user.
- **FR-16 (MVP):** The system shall allow a registration to be cancelled and shall release the associated capacity slot.
- **FR-17 (Beta):** The system shall require authentication and `registration:create` to register.
- **FR-18 (Beta):** The system shall require `registration:read_own` to view a student's registrations and shall return only that student's data.
- **FR-19 (Beta):** The system shall allow an organizer to view participant lists only for events they own, using `registration:read_event`.
- **FR-20 (Beta):** The system shall reject registration for unpublished, cancelled, or ended events.

### 4.3 Authentication and User Management

- **FR-21 (Beta):** The system shall allow a user to create an account with a unique email and valid password.
- **FR-22 (Beta):** The system shall allow users to log in and receive a signed access token after successful credential verification.
- **FR-23 (Beta):** The system shall reject invalid credentials without revealing whether a specific email is registered.
- **FR-24 (Beta):** The system shall hash passwords using a modern password-hashing algorithm before storage.
- **FR-25 (Beta):** The system shall allow an admin with `user:manage` to list, deactivate, and assign approved roles to users.
- **FR-26 (Beta):** The system shall prevent users from granting themselves elevated roles through public registration or profile updates.
- **FR-27 (Beta):** The system shall return the authenticated user's profile and role to the client.

### 4.4 Dashboards

- **FR-28 (Beta):** The student dashboard shall display the current user's profile and registrations.
- **FR-29 (Beta):** The organizer dashboard shall display events owned by the organizer and registration counts.
- **FR-30 (Beta):** The admin dashboard shall provide access to user and event management functions.
- **FR-31 (Beta):** The system shall return `401 Unauthorized` for requests without valid authentication when authentication is required.
- **FR-32 (Beta):** The system shall return `403 Forbidden` when an authenticated user lacks the required permission.

## 5. Authorization Requirements

### 5.1 Permission Matrix (Beta)

| Permission | Visitor | Student | Organizer | Admin |
|---|---:|---:|---:|---:|
| `event:read` | Yes | Yes | Yes | Yes |
| `event:create` | No | No | Yes | Yes |
| `event:update_own` | No | No | Yes, own only | Yes, via admin permission |
| `event:manage_all` | No | No | No | Yes |
| `registration:create` | No | Yes | No | Optional admin support only |
| `registration:read_own` | No | Yes, own only | No | Yes, for oversight |
| `registration:read_event` | No | No | Yes, owned events only | Yes |
| `registration:cancel_own` | No | Yes, own only | No | Optional admin support only |
| `user:manage` | No | No | No | Yes |
| `profile:read_own` | No | Yes | Yes | Yes |

The backend must check both the permission and resource ownership. A scope alone must not grant access to another user's private data.

### 5.2 Authorization Failure Behavior
- Missing or invalid credentials for protected endpoints: HTTP 401.
- Valid credentials but insufficient permission: HTTP 403.
- Resource that does not exist: HTTP 404.
- The implementation may return 404 instead of 403 for inaccessible owned resources to reduce resource enumeration, provided behavior is consistent and documented.

## 6. Data Requirements

### 6.1 User
- `id`: primary key.
- `name`: required display name.
- `email`: required, unique, normalized.
- `password_hash`: required in Beta; never returned by API.
- `role`: Student, Organizer, or Admin.
- `is_active`: boolean.
- `created_at`: timestamp.

### 6.2 Event
- `id`: primary key.
- `title`: required.
- `description`: required.
- `category`: required.
- `venue`: required.
- `start_at`, `end_at`: required timestamps.
- `capacity`: positive integer.
- `status`: Draft, Published, or Cancelled.
- `organizer_id`: foreign key to User.
- `created_at`, `updated_at`: timestamps.

### 6.3 Registration
- `id`: primary key.
- `user_id`: foreign key to User.
- `event_id`: foreign key to Event.
- `status`: Registered or Cancelled.
- `registered_at`: timestamp.
- The database shall enforce uniqueness for an active registration per user/event, or the backend shall enforce an equivalent reliable constraint.

## 7. Non-Functional Requirements

- **NFR-01 Performance:** On a local development environment, normal list/detail requests should respond within 2 seconds for a small course-project dataset, excluding startup and network delays.
- **NFR-02 Security:** Passwords must be hashed; secrets must be externalized; protected endpoints must be authorized server-side.
- **NFR-03 Privacy:** API responses must include only fields needed by the client; password hashes and token secrets must never be returned.
- **NFR-04 Reliability:** Invalid input and expected business-rule failures must return predictable HTTP responses.
- **NFR-05 Integrity:** Foreign keys and uniqueness constraints must protect relational consistency.
- **NFR-06 Maintainability:** Code shall separate routers, schemas, models, services, and configuration.
- **NFR-07 Compatibility:** The UI shall support current mainstream versions of Chrome, Firefox, and Edge.
- **NFR-08 Accessibility/usability:** Forms shall have labels, validation messages, and keyboard-accessible controls.
- **NFR-09 Portability:** The application shall provide reproducible setup instructions and a documented environment configuration.
- **NFR-10 Testability:** Core business rules and authorization checks shall have manual or automated tests.

## 8. API Requirements (Summary)

The API prefix is `/api/v1`. The TDD defines the initial endpoint plan.

| Method | Endpoint | Purpose | Release |
|---|---|---|---|
| GET | `/events` | List/search published events | MVP |
| GET | `/events/{event_id}` | Event details | MVP |
| POST | `/events` | Create event | MVP |
| PATCH | `/events/{event_id}` | Update event | MVP |
| DELETE | `/events/{event_id}` | Delete event | MVP |
| POST | `/events/{event_id}/registrations` | Register for event | MVP |
| GET | `/registrations/me` | Current user's registrations | Beta |
| DELETE | `/registrations/{registration_id}` | Cancel own registration | MVP/Beta |
| POST | `/auth/register` | Create student account | Beta |
| POST | `/auth/login` | Authenticate and issue token | Beta |
| GET | `/users/me` | Current user's profile | Beta |
| GET | `/organizer/events/{event_id}/registrations` | Participant list for owned event | Beta |
| GET | `/admin/users` | List users | Beta |
| PATCH | `/admin/users/{user_id}` | Update status/role | Beta |

## 9. Use Cases

### UC-01: Browse Events
**Actor:** Visitor or authenticated user  
**Preconditions:** Application is available.  
**Main flow:** User opens the event list; system returns published events; user may search/filter; user opens an event; system displays details.  
**Alternate flow:** If no events match, system displays an empty state.  
**Acceptance:** Only published events appear in public browsing.

### UC-02: Register for an Event
**Actor:** Student  
**Preconditions:** In Beta, student is authenticated; event is published and open for registration.  
**Main flow:** Student opens event details, selects Register, and submits; backend checks eligibility, duplicate status, and capacity; backend creates registration; UI displays confirmation.  
**Alternate flows:** Duplicate registration, full event, or closed event returns a clear error without creating a registration.  
**Acceptance:** One active registration per student/event; capacity is not exceeded.

### UC-03: Create or Update an Event
**Actor:** Event Organizer  
**Preconditions:** In Beta, organizer is authenticated and has the relevant scope.  
**Main flow:** Organizer submits event details; backend validates data and ownership; system saves and returns the event.  
**Alternate flow:** Invalid fields produce validation errors; editing an event owned by another organizer is denied.  
**Acceptance:** Organizer can manage own events only; admin can manage all events.

### UC-04: Manage Users
**Actor:** Admin  
**Preconditions:** Admin is authenticated with `user:manage`.  
**Main flow:** Admin opens user management, reviews accounts, and changes an account's role or active status; backend validates and saves changes.  
**Acceptance:** Non-admins cannot access admin endpoints or elevate their own role.

## 10. Acceptance Test Scenarios

| ID | Scenario | Expected result | Release |
|---|---|---|---|
| AT-01 | Request published event list | HTTP 200 and event list | MVP |
| AT-02 | Create event with end time before start time | Validation error; no event created | MVP |
| AT-03 | Register twice for the same event | Second active registration rejected | MVP |
| AT-04 | Register when capacity is full | Registration rejected | MVP |
| AT-05 | Call protected endpoint without token | HTTP 401 | Beta |
| AT-06 | Student calls admin user-management endpoint | HTTP 403 | Beta |
| AT-07 | Organizer attempts to edit another organizer's event | Access denied | Beta |
| AT-08 | Student requests another student's registrations | No other student's data returned | Beta |
| AT-09 | Admin changes a user's role | Change succeeds and is enforced on subsequent requests | Beta |
| AT-10 | Load each role dashboard | Only role-appropriate actions/data are shown | Beta |

## 11. Traceability

| Product goal | Related requirements |
|---|---|
| Central event discovery | FR-01, FR-02, FR-03 |
| Event management | FR-04 to FR-11 |
| Registration management | FR-12 to FR-20 |
| Secure accounts and access | FR-21 to FR-27, FR-31, FR-32 |
| Role-specific experience | FR-28 to FR-30 |
| Data consistency and security | NFR-02, NFR-03, NFR-05 |

## 12. Open Decisions

- Confirm the exact course template and any required diagrams with the instructor.
- Confirm whether PostgreSQL is required for deployment or SQLite is acceptable for the whole project.
- Confirm the team's final hosting provider.
- Confirm whether organizer accounts are admin-created or can be requested and approved. Until confirmed, only admins can assign the Organizer role.
