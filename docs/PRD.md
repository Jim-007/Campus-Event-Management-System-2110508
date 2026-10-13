# CampusConnect — Product Requirements Document (PRD)

**Document version:** 1.0  
**Project name:** CampusConnect  
**Project type:** Web-based Campus Event Management System  
**Status:** Course project proposal  
**Target stack:** React.js + TypeScript, FastAPI + Python, REST APIs

## 1. Product Overview

CampusConnect is a web application for discovering and managing university campus events. Students can browse published events and register for participation; event organizers can create and manage their own events and review their participant lists; administrators can manage users and oversee events.

The project will be delivered in two releases. **MVP** focuses on core event CRUD and registration workflows through REST APIs, running locally. **Beta** adds authentication, role-based access control (RBAC), security scopes/permissions, user profile dashboards, and deployment.

## 2. Problem Statement

Campus event information and registration can be scattered across social media posts, forms, and messages. This makes it difficult for students to find current event details and for organizers to track registrations consistently. CampusConnect provides one simple place to publish events, register participants, and manage event information.

## 3. Product Goals

1. Provide a centralized, searchable list of published campus events.
2. Allow students to register for events and review their own registrations.
3. Allow organizers to manage events they own and view their participant lists.
4. Provide administrators with user and event oversight.
5. Demonstrate a well-structured full-stack application using React + TypeScript, FastAPI, REST APIs, authentication, RBAC, and security scopes.
6. Keep the feature set achievable within the course timeline.

## 4. Target Users and Roles

| Role | Description | Main needs |
|---|---|---|
| Student | A campus user interested in attending events | Find events, view details, register, cancel own registration, see registration status |
| Event Organizer | A user responsible for campus events | Create and manage own events, set capacity and event details, view participants |
| Admin | Platform administrator | Manage user accounts and roles, view/manage all events, oversee registrations |

A user has one assigned role in the initial release. Multiple roles per user are out of scope unless required by the instructor.

## 5. Scope and Releases

### Release 1 — MVP (Mid-term demo)

All MVP features should run locally and be usable through REST APIs and a basic React interface.

- **MVP-01:** List published events and view event details.
- **MVP-02:** Create an event.
- **MVP-03:** Read, update, and delete an event.
- **MVP-04:** Register a participant for an event.
- **MVP-05:** View registrations for an event and view a participant's registrations.
- **MVP-06:** Prevent duplicate registration and reject registration when event capacity is full.
- **MVP-07:** Provide basic event search/filtering by title, category, or date.
- **MVP-08:** Validate required fields and return clear API errors.
- **MVP-09:** Provide a basic responsive React interface connected to the FastAPI backend.

For the MVP demo, role restrictions may be simulated for development only if needed; this must not be presented as secure authorization.

### Release 2 — Beta (Final demo)

- **BETA-01:** User registration and login.
- **BETA-02:** JWT-based authentication.
- **BETA-03:** Role-based access control for Student, Event Organizer, and Admin.
- **BETA-04:** Fine-grained security scopes/permissions enforced by FastAPI.
- **BETA-05:** Resource ownership checks: organizers can edit only their own events; students can access only their own registrations.
- **BETA-06:** Student profile dashboard showing personal registrations.
- **BETA-07:** Organizer dashboard showing owned events and registration counts.
- **BETA-08:** Admin dashboard for user and event management.
- **BETA-09:** Password hashing, environment-based secrets, CORS configuration, and consistent authorization/error handling.
- **BETA-10:** Deploy frontend and backend to an appropriate hosting service, with documented configuration.

## 6. Functional Requirements

| ID | Requirement | Release | Priority |
|---|---|---|---|
| FR-01 | The system shall display published events and event details. | MVP | Must |
| FR-02 | The system shall support creating, viewing, updating, and deleting events through REST APIs. | MVP | Must |
| FR-03 | The system shall allow a user to register for an event. | MVP | Must |
| FR-04 | The system shall prevent duplicate active registrations for the same user and event. | MVP | Must |
| FR-05 | The system shall enforce an event's capacity limit. | MVP | Must |
| FR-06 | The system shall allow users to view and cancel their registrations. | MVP | Must |
| FR-07 | The system shall allow event search and basic filtering. | MVP | Should |
| FR-08 | The system shall support account registration and login. | Beta | Must |
| FR-09 | The system shall enforce role and permission checks on protected operations. | Beta | Must |
| FR-10 | The system shall restrict organizers to managing their own events. | Beta | Must |
| FR-11 | The system shall provide role-appropriate dashboards. | Beta | Must |
| FR-12 | The system shall allow admins to manage users and roles. | Beta | Must |
| FR-13 | The system shall provide documented deployment instructions and a deployed demo. | Beta | Should |

## 7. Non-Functional Requirements

- **NFR-01 Usability:** Common tasks should be achievable through clear navigation and readable forms.
- **NFR-02 Responsiveness:** Core pages should work on desktop and mobile-width screens.
- **NFR-03 Security:** Passwords must be stored as salted hashes; passwords must never be stored or logged in plaintext.
- **NFR-04 Authorization:** Every protected backend endpoint must validate identity, permission, and relevant resource ownership. Frontend-only hiding is not security.
- **NFR-05 Data integrity:** The database must enforce unique email addresses and prevent duplicate user-event registrations.
- **NFR-06 Error handling:** APIs must return appropriate HTTP status codes and useful, non-sensitive error messages.
- **NFR-07 Maintainability:** Frontend, API routes, business logic, and database models should be separated into clear modules.
- **NFR-08 Documentation:** API endpoints and setup steps must be documented; FastAPI's OpenAPI/Swagger UI should be usable during development.
- **NFR-09 Configuration:** Secrets and environment-specific values must be stored in environment variables, not committed to Git.

## 8. Business Rules

1. Only published events appear in the public event listing.
2. Each event has a title, description, category, start time, end time, venue, organizer, publication status, and capacity.
3. Event end time must be later than start time.
4. Capacity must be a positive integer.
5. A user may have only one active registration per event.
6. Registration is rejected if the event is unpublished, cancelled, already ended, or full.
7. Students may cancel only their own registrations.
8. In Beta, organizers may update or delete only events they own; admins may manage all events.
9. In Beta, organizers may view participant information only for events they own; admins may oversee all events.
10. Registration cancellation frees a capacity slot.

## 9. Success Criteria

- All MVP requirements can be demonstrated locally.
- Students can register and cancel without duplicate registrations or capacity overbooking in normal use.
- In Beta, unauthenticated users cannot access protected endpoints.
- Student, Organizer, and Admin permissions are enforced on the backend.
- An organizer cannot edit another organizer's event by changing an ID in the request.
- The three role dashboards display the appropriate actions and data.
- Setup and API usage instructions are available in the repository.

## 10. Out of Scope

- Payment processing and ticket sales.
- QR-code check-in or attendance scanning.
- Email/SMS/push notifications.
- Live chat, social feeds, and comments.
- AI recommendations or machine-learning features.
- Complex university timetable integration.
- Multi-tenant support for multiple universities.
- Native mobile applications.

## 11. Assumptions and Constraints

- This is a course project built by a student team within the semester timeline.
- The first version uses a relational database; SQLite is suitable for local development. A PostgreSQL deployment may be used if available.
- Event registration is free and does not require payment.
- Organizers are registered application users whose role is assigned or approved by an administrator.
- Exact hosting provider and course-specific documentation templates will be confirmed by the team/instructor.

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Scope grows too large | Keep only the listed MVP/Beta requirements; defer optional features |
| Authorization bugs | Test each role against allowed and denied actions; enforce checks in FastAPI |
| Registration race conditions | Use database constraints and transaction-safe capacity checks where supported |
| Frontend/backend integration delays | Agree on request/response schemas early and test APIs with Swagger UI |
| Deployment configuration problems | Keep local setup reproducible and document environment variables |

## 13. Acceptance Summary

The project is accepted for the MVP demo when event CRUD, listing, filtering, and registration workflows work locally through REST APIs and the React UI. The Beta is accepted when authentication, backend-enforced RBAC and scopes, ownership checks, role-specific dashboards, user management, and deployment are demonstrable.
