Independent University, Bangladesh

CSE309 Web Application & Internet

# Final Project Submission Report

**Submitted by:**

Name: Musficur Rahman Jim

Student ID: 2110508

Section: 6

Team Number: Individual project

Project Title: Campus Event Management System

Vercel URL: https://campus-event-management-system-2110.vercel.app/

GitHub Repository: https://github.com/Jim-007/Campus-Event-Management-System-2110508

**Submitted To:**

Sayef Reyadh

Adjunct Lecturer

Department of Computer Science & Engineering

Independent University, Bangladesh

Semester: Autumn 2026

Date of Submission: November 28, 2026

## Table of Contents

* [1. Executive Summary](#1-executive-summary)

* [Part A. Product Requirements (PRD)](#part-a-product-requirements-prd)

* [Part B. Software Requirements (SRS)](#part-b-software-requirements-srs)

* [Part C. Technical Design (TDD)](#part-c-technical-design-tdd)

* [Part D. Evidence: Screenshots of the Running Application](#part-d-evidence-screenshots-of-the-running-application)

* [Part E. Project Management and Conclusion](#part-e-project-management-and-conclusion)

### List of Figures and Screenshots

* **Figure 1:** Use Case Diagram — Actors and System Boundaries (Section B5)

* **Figure 2:** High-Level System Architecture and Token Flow (Section C2)

* **Figure 3:** Entity-Relationship (ER) Diagram — Normalized PostgreSQL Schema (Section C4)

* **Figure 4:** Dual-Token JWT Authentication & Rotation Sequence Diagram (Section C6)

* **Figure 5:** Server-Side RBAC & Ownership Authorization Pipeline (Section C7)

* **Figure 6:** Admin Dashboard Architecture and Endpoint Mapping (Section C8)

* **Figure 7:** Vercel Serverless & Static Deployment Layout (Section C10)

* **Screenshots S1–S21:** Live Deployment Evidence (Part D)

## 1. Executive Summary

### 1.1 Project Overview

The **Campus Event Management System** is a multi-user, full-stack web application designed for university students, club organizers, and campus administrators to plan, coordinate, and moderate academic workshops, seminars, and cultural events. It replaces informal spreadsheet and messaging workflows with strict role-based access control (RBAC), shared committee workspaces with granular permissions, and centralized administrative oversight.

**Technology Stack:** React 19 with TypeScript and Vite (Frontend), FastAPI with SQLModel (Backend), Supabase PostgreSQL via `pg8000` (Database), and Vercel (Serverless API + Static Hosting).

### 1.2 What Was Built Since the Mid Assessment

Since the mid-term prototype, the system was upgraded from basic CRUD operations into a production-grade, multi-tenant secure web application:

* **JWT Authentication with Refresh Rotation and Logout:** Implemented a dual-token architecture combining short-lived HS256 JWT access tokens with `httpOnly` SHA-256 hashed refresh cookies, per-device session tracking, and refresh token reuse detection.

* **Role-Based Access Control (Roles, Ownership, Group Permissions):** Enforced server-side authorization across system roles (`admin`, `user`), record ownership (`owner_id`), and committee group permissions (`can_create`, `can_edit`, `can_assign`).

* **Admin Dashboard (Users, Content, Activity Log, Security View, Exports):** Built a dedicated administrative control center supporting user search/filtering, banning with reasons, role promotion, session revocation, bulk event/group moderation, security metrics, and filtered CSV exports.

* **Audit Logging, Brute-Force Protection, and Vercel Deployment:** Added append-only audit trail recording for all security-sensitive mutations, progressive login lockout protection, and full-stack deployment on Vercel backed by Supabase PostgreSQL.

### 1.3 Live Links

*(Note: Demo test account user IDs and passwords are omitted from this repository file for security and are provided exclusively in the Google Form submission and the PDF Report Appendix.)*

| Resource | Live URL | 
| ----- | ----- | 
| **GitHub Repository** | `https://github.com/Jim-007/Campus-Event-Management-System-2110508` | 
| **Vercel Frontend** | `https://campus-event-management-system-2110.vercel.app/` | 
| **Backend API Base** | `https://campus-event-management-system-2110.vercel.app/api` | 
| **Live API Docs (Swagger UI)** | `https://campus-event-management-system-2110.vercel.app/api/docs` | 
| **Video Demonstration** | `[Insert Unlisted YouTube or Public Google Drive Video Link Here]` | 

*Table 1: Live deployment, source code, documentation, and demonstration links.*

## Part A. Product Requirements (PRD)

### A1. Problem Statement

At Independent University, Bangladesh (IUB), student clubs, department societies, and event committees coordinate dozens of workshops, hackathons, and seminars every semester. Currently, organizers rely on fragmented messaging threads and shared spreadsheets to track venues, schedules, and task assignments. Because spreadsheets lack granular permissions, any collaborator with edit access can accidentally overwrite confirmed schedules or delete records, while committee leads cannot delegate limited responsibilities (such as assigning coordinators without altering event details).

Furthermore, campus administrators lack a centralized audit trail to verify who scheduled or modified an event, detect unauthorized access attempts, or immediately suspend compromised accounts. Without strict isolation and accountability, scheduling conflicts, unauthorized edits, and data loss occur frequently during peak campus weeks.

### A2. Users and Roles

| Role | Who They Are | Main Tasks | What They Must Never Be Able to Do | 
| ----- | ----- | ----- | ----- | 
| **Visitor** | Unauthenticated internet user or prospective student. | Register a new account (`/signup`), log in (`/login`), check API health status. | View private user events, inspect groups, create/modify records, or access admin endpoints. | 
| **User** | Authenticated student or event organizer (`role = "user"`). | Create/edit/delete own events, create shared groups, manage own profile/password, view and revoke active sessions. | Read or modify another user's private events, escalate own role to `admin`, or access `/api/admin/*`. | 
| **Group Member** | Authenticated user added to a shared committee group. | View shared group events; perform `create`, `edit`, or `assign` actions strictly within granted flags. | Exceed assigned flags (e.g., an `assign`-only member editing titles), delete the group, or alter member permissions. | 
| **Group Owner** | Creator of a shared group (`group.owner_id == user.id`). | Add/remove group members, grant/revoke `can_create`, `can_edit`, `can_assign` flags, manage all group events, delete the group. | Access other private groups they do not belong to or perform system-wide admin actions. | 
| **Admin** | Campus system administrator (`role = "admin"`). | View platform metrics, search/ban/unban users, promote users, revoke any session, bulk-moderate events/groups, inspect audit logs and security alerts, export CSVs. | Change their own role, ban another administrator, or bypass group membership rules inside private committees. | 

*Table 2: System users, roles, responsibilities, and security boundaries.*

### A3. Goals and Success Measures

| Goal ID | Goal Description | Measurable Success Criterion | 
| ----- | ----- | ----- | 
| **G-01** | Strict multi-tenant data isolation across users and groups. | $100\%$ of unauthorized cross-user or insufficient-permission requests return HTTP `403 Forbidden` or `404 Not Found` (zero unauthorized reads/writes). | 
| **G-02** | Short-lived, revocable session security. | Access tokens expire within $\le 15\text{ minutes}$; revoking a session or banning a user invalidates access on the very next protected API call (`401`/`403`). | 
| **G-03** | Resistance to credential stuffing and brute-force attacks. | After $5$ consecutive failed login attempts, the account/IP is locked for $15\text{ minutes}$ with HTTP `429 Too Many Requests`. | 
| **G-04** | Complete administrative accountability. | $100\%$ of authentication events, permission changes, bans, and bulk moderations generate an immutable row in `audit_logs`. | 
| **G-05** | Responsive serverless API performance. | Authenticated read endpoints (`/api/events`, `/api/groups`) respond in $< 500\text{ ms}$ on warm serverless invocations. | 

*Table 3: Project goals and testable success measures.*

### A4. Scope and Non-Goals

* **In Scope:**

  * Email/password registration and authentication with server-side peppered `bcrypt` hashing.

  * Dual-token JWT lifecycle (`access_token` + `httpOnly` `refresh_token` cookie with rotation and reuse detection).

  * Personal event management (`CRUD`) and shared committee group workspaces (`can_create`, `can_edit`, `can_assign`).

  * Administrative dashboard with user management, session revocation, bulk moderation, audit log filtering, brute-force security analytics, and CSV export.

  * Production deployment on Vercel (React static bundle + Python serverless functions) connected to Supabase PostgreSQL.

* **Out of Scope:**

  * External OAuth2 social login (Google/GitHub) — excluded to keep credential lifecycle, peppering, and lockout logic self-contained and verifiable.

  * Real-time WebSocket push notifications — excluded due to stateless Vercel serverless function execution limits.

  * Payment gateway integration for paid tickets — outside the scope of internal campus committee coordination.

* **Assumptions and Constraints:**

  * Users access the application via modern evergreen browsers (Chrome, Edge, Firefox) with cookies enabled for refresh token persistence.

  * Backend runs in stateless Vercel serverless containers; therefore, all session state and lockout counters must persist in PostgreSQL rather than in-memory Python dictionaries.

### A5. User Stories

| Story ID | Role | User Story | 
| ----- | ----- | ----- | 
| **US-01** | Visitor | As a **Visitor**, I want to register with my name, email, and strong password so that I can create an organizer account. | 
| **US-02** | User | As a **User**, I want my session to refresh automatically when my short-lived access token expires so that I am not logged out while filling out an event form. | 
| **US-03** | User | As a **User**, I want to view all my active device sessions and revoke unfamiliar ones so that I can secure my account if I forget to log out on a lab computer. | 
| **US-04** | User | As a **User**, I want to create personal campus events with title, category, venue, start/end times, and capacity so that I can track my schedule. | 
| **US-05** | Group Owner | As a **Group Owner**, I want to create a committee group and grant specific members `create`, `edit`, or `assign` flags so that teammates only perform their designated duties. | 
| **US-06** | Group Member | As a **Group Member** with `assign`-only permission, I want to assign a coordinator to a group event while being prevented from changing the event's venue or schedule. | 
| **US-07** | User | As a **User**, I want any attempt by another user to edit or delete my private event to be blocked by the server so that my records remain tamper-proof. | 
| **US-08** | Admin | As an **Admin**, I want to search users by email or role and ban abusive accounts with a documented reason so that platform integrity is maintained. | 
| **US-09** | Admin | As an **Admin**, I want to perform bulk delete or archive actions on flagged events and export filtered audit logs to CSV so that I can submit semester compliance reports. | 
| **US-10** | Admin | As an **Admin**, I want to view failed login attempts grouped by IP address and target email so that I can detect brute-force attacks early. | 

*Table 4: Prioritized user stories across all roles.*

## Part B. Software Requirements (SRS)

### B1. Introduction

This Software Requirements Specification (SRS) defines the exact functional, non-functional, security, and behavioral requirements for the **Campus Event Management System**. It serves as the authoritative contract for implementation, automated testing, and instructor evaluation.

| Term | Definition | 
| ----- | ----- | 
| **JWT** | JSON Web Token (RFC 7519); a cryptographically signed compact token carrying user identity and role claims. | 
| **Access Token** | Short-lived JWT ($15\text{ min}$) sent in the `Authorization: Bearer <token>` header to authorize API requests. | 
| **Refresh Token** | Long-lived opaque random token ($7\text{ days}$) stored in an `httpOnly` cookie and hashed with SHA-256 in the database for session renewal. | 
| **RBAC** | Role-Based Access Control; server-side enforcement combining system roles, record ownership, and group permission flags. | 
| **Permission** | Granular capability boolean (`can_create`, `can_edit`, `can_assign`) bound to a `(group_id, user_id)` membership row. | 
| **Audit Log** | Append-only database table (`audit_logs`) recording actor, action, target resource, IP address, user-agent, and timestamp. | 

*Table 5: Core technical definitions.*

**References:**

1. RFC 7519 — *JSON Web Token (JWT)*, IETF.

2. OWASP Application Security Verification Standard (ASVS) v4.0 — *Authentication & Access Control Verification Requirements*.

3. FastAPI Documentation — *Security, OAuth2 with Password (and hashing), Bearer with JWT tokens*.

### B2. Functional Requirements

#### Authentication & Session Management (`FR-AUTH`)

| Req ID | Requirement Statement | 
| ----- | ----- | 
| **FR-AUTH-01** | The system shall allow a visitor to register via `POST /api/auth/signup` with full name, unique valid email, and password ($\ge 6$ characters). | 
| **FR-AUTH-02** | The system shall hash all passwords using `bcrypt` combined with a server-side secret `PASSWORD_PEPPER` before storing them in PostgreSQL. | 
| **FR-AUTH-03** | The system shall authenticate valid credentials via `POST /api/auth/login`, issuing a 15-minute HS256 JWT access token (`sub`, `role`, `iat`, `exp`) and a 7-day `httpOnly` refresh cookie. | 
| **FR-AUTH-04** | The system shall store only the SHA-256 hash of each refresh token along with client IP and user-agent metadata in `user_sessions`. | 
| **FR-AUTH-05** | The system shall rotate the refresh token upon every `POST /api/auth/refresh` call and revoke all user sessions if a previously rotated token is reused. | 
| **FR-AUTH-06** | The system shall revoke the active session and clear the refresh cookie when a user calls `POST /api/auth/logout`. | 
| **FR-AUTH-07** | The system shall allow an authenticated user to list all active sessions (`GET /api/auth/sessions`) and revoke any individual session (`DELETE /api/auth/sessions/{session_id}`). | 
| **FR-AUTH-08** | The system shall enforce progressive brute-force lockout after $5$ consecutive failed login attempts, rejecting further attempts with HTTP `429`. | 
| **FR-AUTH-09** | The system shall allow authenticated users to update their display name (`PATCH /api/auth/me`) and change their password (`POST /api/auth/change-password`) after verifying their current password. | 

*Table 6: Authentication functional requirements.*

#### Role-Based Access Control (`FR-RBAC`)

| Req ID | Requirement Statement | 
| ----- | ----- | 
| **FR-RBAC-01** | The system shall enforce two system-wide roles (`user` and `admin`) on the server for every protected endpoint. | 
| **FR-RBAC-02** | The system shall restrict private event read, update, and delete operations strictly to the event's `owner_id` (unless shared via an authorized group). | 
| **FR-RBAC-03** | The system shall allow a group owner to grant or revoke `can_create`, `can_edit`, and `can_assign` permissions per member via `PATCH /api/groups/{group_id}/members/{user_id}`. | 
| **FR-RBAC-04** | The system shall enforce that a group member with `can_assign` only can update `assigned_to` on group events while receiving HTTP `403` if attempting to modify title, description, venue, or schedule. | 
| **FR-RBAC-05** | The system shall restrict member addition, permission updates, member removal, and group deletion exclusively to the group's `owner_id`. | 
| **FR-RBAC-06** | The system shall prevent any administrator from changing their own role or banning another administrator account (`403 Forbidden`). | 
| **FR-RBAC-07** | The system shall reject requests from a banned user (`is_banned == True`) immediately on their next API call with HTTP `403` and revoke their active sessions. | 

*Table 7: RBAC and ownership functional requirements.*

#### Administrative Controls (`FR-ADM`)

| Req ID | Requirement Statement | 
| ----- | ----- | 
| **FR-ADM-01** | The system shall provide platform summary statistics (`GET /api/admin/stats`) including total users, banned users, active sessions, total events, and total groups. | 
| **FR-ADM-02** | The system shall allow administrators to list users (`GET /api/admin/users`) with pagination, search by email/name, and filtering by role or ban status. | 
| **FR-ADM-03** | The system shall allow administrators to inspect detailed user records (`GET /api/admin/users/{user_id}`) including active sessions and recent audit activity. | 
| **FR-ADM-04** | The system shall allow administrators to ban (`POST /api/admin/users/{user_id}/ban`) with a required reason and unban (`POST /api/admin/users/{user_id}/unban`) non-admin users. | 
| **FR-ADM-05** | The system shall allow administrators to promote or demote other users' roles (`PATCH /api/admin/users/{user_id}/role`) and revoke any user session (`DELETE /api/admin/sessions/{session_id}`). | 
| **FR-ADM-06** | The system shall support bulk moderation actions (`POST /api/admin/events/bulk-delete` and `POST /api/admin/groups/bulk-delete`) reporting exact `affected` and `skipped` counts. | 
| **FR-ADM-07** | The system shall provide a filterable audit log viewer (`GET /api/admin/audit-logs`), a security view summarizing failed logins by IP and account (`GET /api/admin/security`), and filtered CSV export (`GET /api/admin/audit-logs/export`). | 

*Table 8: Admin dashboard functional requirements.*

#### Domain Features — Campus Events & Committees (`FR-DOMAIN`)

| Req ID | Requirement Statement | 
| ----- | ----- | 
| **FR-DOMAIN-01** | The system shall allow authenticated users to create personal or group campus events (`POST /api/events`) specifying title, description, category, venue, `start_time`, `end_time`, capacity, and optional `assigned_to`. | 
| **FR-DOMAIN-02** | The system shall validate that `end_time` is strictly after `start_time` and `capacity > 0` before persisting an event (`422 Unprocessable Entity` on invalid input). | 
| **FR-DOMAIN-03** | The system shall return only events owned by the current user or belonging to groups in which the user is a member (`GET /api/events`). | 
| **FR-DOMAIN-04** | The system shall allow users to create committee groups (`POST /api/groups`) with a name and description, automatically assigning the creator as `owner_id`. | 

*Table 9: Domain-specific functional requirements.*

### B3. Non-Functional Requirements

| Req ID | Category | Requirement Statement | 
| ----- | ----- | ----- | 
| **NFR-SEC-01** | Security | All cryptographic secrets (`JWT_SECRET_KEY`, `PASSWORD_PEPPER`, `DATABASE_URL`) shall be loaded exclusively from environment variables and never committed to Git. | 
| **NFR-SEC-02** | Security | Login failures shall return a generic `"Invalid email or password"` message so attackers cannot enumerate registered email addresses. | 
| **NFR-PERF-01** | Performance | All list endpoints (`/api/events`, `/api/admin/users`, `/api/admin/audit-logs`) shall enforce pagination limits (`limit <= 100`) and execute within $500\text{ ms}$. | 
| **NFR-USA-01** | Usability | The React frontend shall provide responsive layouts, loading indicators during network calls, and clear human-readable banners for `401`, `403`, and `422` errors. | 
| **NFR-REL-01** | Reliability | All user accounts, events, groups, sessions, and audit logs shall persist across serverless cold starts and redeployments in Supabase PostgreSQL. | 
| **NFR-MNT-01** | Maintainability | All authorization rules shall be centralized in `backend/rbac.py` and verified by automated `pytest` integration tests. | 

*Table 10: Non-functional requirements.*

### B4. Roles and Permission Matrix

#### Endpoint Groups by Role

| Endpoint Group | Visitor | User | Group Member | Group Owner | Admin | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `POST /api/auth/signup`, `/login`, `/refresh` | Yes | Yes | Yes | Yes | Yes | 
| `GET/PATCH /api/auth/me`, `/sessions` | No | Own | Own | Own | Own | 
| `GET/POST /api/events` (Personal) | No | Own | Own | Own | Own | 
| `PATCH/DELETE /api/events/{id}` (Personal) | No | Own | Own | Own | No (Admin moderates via `/admin`) | 
| `GET /api/events` (Group-scoped) | No | No | Yes | Yes | No (unless member) | 
| `POST/PATCH/DELETE /api/events` (Group-scoped) | No | No | By Flag | Yes | No (unless member) | 
| `PATCH/DELETE /api/groups/{id}` & Members | No | No | No | Own | No (Admin moderates via `/admin`) | 
| `GET/POST/PATCH/DELETE /api/admin/*` | No | No | No | No | Yes | 

*Table 11: Endpoint access matrix across roles.*

#### Group Permissions Breakdown

| Action / Capability | `can_create = True` | `can_edit = True` | `can_assign = True` | All Flags `False` (View Only) | Group Owner (`owner_id`) | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| View group details & group events | Yes | Yes | Yes | Yes | Yes | 
| Create new events inside the group | Yes | No | No | No | Yes | 
| Edit event title, description, venue, time | No | Yes | No | No | Yes | 
| Update `assigned_to` user ID on group events | No | Yes | Yes | No | Yes | 
| Delete events inside the group | No | Yes | No | No | Yes | 
| Add/remove members or change permission flags | No | No | No | No | Yes | 
| Delete the entire group | No | No | No | No | Yes | 

*Table 12: Granular group permission matrix.*

#### Administrative Rules & Boundaries

| Rule Area | System Behavior | 
| ----- | ----- | 
| **Self-Role Modification** | An admin attempting `PATCH /api/admin/users/{self_id}/role` is blocked with `403 Forbidden` to prevent accidental admin lockout. | 
| **Peer Admin Protection** | An admin attempting to ban or demote another user with `role == "admin"` is blocked with `403 Forbidden`. | 
| **Group Privilege Isolation** | System `admin` status grants **no automatic write permissions** inside private user groups; admins govern via `/api/admin/*` moderation endpoints with full audit logging. | 

*Table 13: Administrative self-protection and boundary rules.*

### B5. Use Cases

```
flowchart LR
    Visitor([Visitor])
    User([User / Group Owner])
    Member([Group Member])
    Admin([Admin])

    subgraph Campus Event Management System
        UC1(UC-01: Login & Token Refresh)
        UC2(UC-02: Create Campus Event)
        UC3(UC-03: Change Member Permissions)
        UC4(UC-04: Denied Unauthorized Action)
        UC5(UC-05: Ban User Account)
        UC6(UC-06: Inspect & Export Audit Log)
    end

    Visitor --> UC1
    User --> UC1
    User --> UC2
    User --> UC3
    Member --> UC4
    Admin --> UC5
    Admin --> UC6

```

*Figure 1: Use case diagram illustrating actors and core security workflows.*

| UC ID | Use Case | Actor | Preconditions | Main Flow | Error / Alternative Flows | Postconditions | 
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | 
| **UC-01** | Log In and Refresh Token | Visitor / User | Registered, unbanned account exists. | 1\. Submit credentials to `POST /api/auth/login`.  2\. Server verifies peppered bcrypt hash.  3\. Server returns access JWT + `httpOnly` refresh cookie.  4\. On `401`, client calls `POST /api/auth/refresh` to rotate tokens. | \- Invalid password $\rightarrow$ `401` + increment failed counter.  \- $\ge 5$ failures $\rightarrow$ `429` lockout.  \- Reused refresh token $\rightarrow$ `401` + revoke all sessions. | Active `user_sessions` row stored; `LOGIN_SUCCESS` logged. | 
| **UC-02** | Create Campus Event | User / Group Member | Authenticated user; if `group_id` set, must be owner or have `can_create`. | 1\. Fill event form and submit `POST /api/events`.  2\. Server validates timestamps and RBAC.  3\. Insert event into `events` table.  4\. Return `201 Created`. | \- Missing `can_create` in group $\rightarrow$ `403 Forbidden`.  \- `end_time <= start_time` $\rightarrow$ `422 Unprocessable Entity`. | Event persisted with `owner_id` and logged in `audit_logs`. | 
| **UC-03** | Change Member Permissions | Group Owner | Group exists and actor is `group.owner_id`. | 1\. Open Shared Groups tab and toggle flags.  2\. Send `PATCH /api/groups/{id}/members/{uid}`.  3\. Server updates `can_create`, `can_edit`, `can_assign`. | \- Non-owner actor $\rightarrow$ `403 Forbidden`.  \- Target user not in group $\rightarrow$ `404 Not Found`. | Updated permission row saved; `GROUP_PERMISSION_UPDATED` logged. | 
| **UC-04** | Denied Action (`assign` only) | Group Member | Member has `can_assign=True`, `can_edit=False`. | 1\. Member attempts `PATCH /api/events/{id}` changing `venue`.  2\. `verify_event_access` detects non-assignment field edit.  3\. Server rejects request with `403`. | \- If member only updates `assigned_to` $\rightarrow$ succeeds with `200 OK`. | Event remains unchanged; UI displays `403` RBAC banner. | 
| **UC-05** | Ban User Account | Admin | Actor has `role == "admin"`; target is `role == "user"`. | 1\. Admin selects user and enters ban reason.  2\. Send `POST /api/admin/users/{id}/ban`.  3\. Server sets `is_banned=True`, revokes all target sessions. | \- Target is another admin or self $\rightarrow$ `403 Forbidden`.  \- Empty ban reason $\rightarrow$ `422 Unprocessable Entity`. | Target user blocked immediately on next request; `USER_BANNED` logged. | 
| **UC-06** | Read & Export Audit Log | Admin | Authenticated admin on Admin Dashboard. | 1\. Filter logs by action or user ID (`GET /api/admin/audit-logs`).  2\. Inspect paginated trail.  3\. Click Export CSV (`GET /api/admin/audit-logs/export`). | \- Non-admin user calling endpoint $\rightarrow$ `403 Forbidden`. | Filtered CSV file downloaded matching active query filters. | 

*Table 14: Detailed use case specifications.*

### B6. Acceptance Criteria

| AC ID | Requirement | Given | When | Then | 
| ----- | ----- | ----- | ----- | ----- | 
| **AC-01** | `FR-AUTH-03` | A user holds a JWT access token whose `exp` timestamp has passed. | The client sends `GET /api/events` with that expired token. | The server returns HTTP `401 Unauthorized`, triggering the frontend's single refresh retry. | 
| **AC-02** | `FR-AUTH-03` | An attacker modifies the payload of a JWT (e.g., changing `role` from `"user"` to `"admin"`). | The modified token is sent in the `Authorization` header. | `jose.jwt.decode` fails signature verification and returns HTTP `401 Unauthorized`. | 
| **AC-03** | `FR-RBAC-02` | User A owns personal Event #10 (`group_id = None`). | User B sends `PATCH /api/events/10` or `DELETE /api/events/10`. | The server returns HTTP `403 Forbidden` (or `404`) and Event #10 is untouched. | 
| **AC-04** | `FR-RBAC-04` | Charlie is a member of Group #1 with `can_assign=True` and `can_edit=False`. | Charlie sends `PATCH /api/events/5` with `{"title": "Hacked Title"}`. | The server returns HTTP `403 Forbidden` stating edit permission is required. | 
| **AC-05** | `FR-RBAC-07` | Bob has a valid access token, and Admin1 bans Bob (`is_banned=True`). | Bob makes any subsequent authenticated API call (`GET /api/events`). | `get_current_user` immediately rejects the request with HTTP `403 Forbidden`. | 
| **AC-06** | `FR-RBAC-06` | Admin1 is logged in with `role == "admin"`. | Admin1 calls `POST /api/admin/users/{admin2_id}/ban`. | The server returns HTTP `403 Forbidden` (`"Cannot ban another administrator"`). | 
| **AC-07** | `FR-AUTH-08` | Five failed login attempts have occurred for `alice@campus.edu`. | A sixth login attempt is made within the 15-minute lockout window. | The server rejects the request with HTTP `429 Too Many Requests`. | 

*Table 15: Given-When-Then security acceptance criteria.*

### B7. Traceability Matrix

| Req ID | Implementing Endpoint / Screen | Automated Test (`pytest`) | Evidence Screenshot | 
| ----- | ----- | ----- | ----- | 
| `FR-AUTH-01`, `FR-AUTH-02` | `POST /api/auth/signup` (`/signup`) | `test_signup_and_password_hashing` | `S1` | 
| `FR-AUTH-03`, `FR-AUTH-04` | `POST /api/auth/login` (`/login`) | `test_login_issues_jwt_and_cookie` | `S7`, `S8` | 
| `FR-AUTH-05`, `FR-AUTH-06` | `POST /api/auth/refresh`, `/logout` | `test_refresh_rotation_and_reuse_detection` | `S8` | 
| `FR-AUTH-07` | `GET/DELETE /api/auth/sessions` (Profile tab) | `test_session_list_and_revoke` | `S4` | 
| `FR-AUTH-08` | `POST /api/auth/login` lockout guard | `test_brute_force_lockout_429` | `S16` | 
| `FR-AUTH-09` | `PATCH /api/auth/me`, `POST /change-password` | `test_change_password_validation` | `S3` | 
| `FR-RBAC-01`, `FR-RBAC-02` | `backend/rbac.py` (`verify_event_access`) | `test_cross_user_event_isolation` | `S2` | 
| `FR-RBAC-03`, `FR-RBAC-04`, `FR-RBAC-05` | `PATCH /api/groups/{id}/members/{uid}` | `test_group_permission_matrix` | `S5`, `S6` | 
| `FR-RBAC-06` | `backend/rbac.py` admin guard | `test_admin_cannot_ban_admin_or_self_demote` | `S13` | 
| `FR-RBAC-07` | `get_current_user` ban check | `test_banned_user_rejected_immediately` | `S9`, `S13` | 
| `FR-ADM-01`–`FR-ADM-07` | `/api/admin/*` (`/admin` Dashboard) | `test_admin_stats_bulk_and_csv_export` | `S10`–`S17` | 
| `FR-DOMAIN-01`–`FR-DOMAIN-04` | `/api/events`, `/api/groups` (`/dashboard`) | `test_event_crud_and_time_validation` | `S2`, `S5` | 

*Table 16: End-to-end requirement traceability matrix.*

## Part C. Technical Design (TDD)

### C1. Technology Stack

| Component | Technology | Version | Reason for Choosing | 
| ----- | ----- | ----- | ----- | 
| **Frontend Framework** | React + TypeScript | React 19.x / TS 5.x | Component-driven UI with compile-time type safety for API payloads and RBAC state. | 
| **Build Tool & Styling** | Vite + Tailwind CSS | Vite 6.x / Tailwind 3.x | Sub-second HMR during development and lightweight static bundle output for Vercel CDN. | 
| **Backend Framework** | FastAPI | 0.115+ | High-performance async/sync Python API with automatic OpenAPI/Swagger docs (`/api/docs`) and Pydantic validation. | 
| **ORM & Validation** | SQLModel + Pydantic | SQLModel 0.0.22+ | Combines SQLAlchemy models and Pydantic schemas into unified, type-safe database models. | 
| **Database & Driver** | PostgreSQL (Supabase) + `pg8000` | PostgreSQL 15 / `pg8000` | Managed cloud relational database with pure-Python driver (`pg8000`) compatible with Vercel serverless Linux containers without C-extension build issues. | 
| **Password Hashing** | `passlib[bcrypt]` + `hashlib` | `bcrypt` 4.0.1 | Industry-standard adaptive hashing with server-side peppering; SHA-256 used for fast lookup of high-entropy refresh tokens. | 
| **JWT Library** | `python-jose[cryptography]` | 3.3+ | RFC 7519 compliant HS256 token signing and verification. | 
| **Testing** | `pytest` + FastAPI `TestClient` | `pytest` 8.x | Fast isolated integration tests covering auth, RBAC matrix, and admin rules. | 
| **Hosting** | Vercel | Serverless + Static | Unified Git-based CI/CD serving both the React SPA and Python API under one origin (eliminating cross-origin cookie friction). | 

*Table 17: Complete technology stack and architectural justification.*

### C2. System Architecture

```
flowchart TB
    Browser["Client Browser (React SPA)"]
    VercelEdge["Vercel Edge Router (vercel.json)"]
    StaticCDN["Vercel Static CDN (frontend/dist)"]
    ServerlessAPI["Vercel Python Serverless Function (backend/main.py)"]
    RBAC["RBAC & Auth Layer (auth.py, rbac.py)"]
    SupabaseDB[("Supabase PostgreSQL")]
    AuditTable[("audit_logs Table")]

    Browser -- "1. GET /dashboard, /admin" --> VercelEdge
    VercelEdge -- "2. Static HTML/JS/CSS" --> StaticCDN
    Browser -- "3. /api/* + Authorization: Bearer JWT + httpOnly Cookie" --> VercelEdge
    VercelEdge -- "4. Rewrite /api/(.*) -> backend/main.py" --> ServerlessAPI
    ServerlessAPI -- "5. Verify JWT, Ban Status & Permissions" --> RBAC
    RBAC -- "6. SQLModel Queries (pg8000 + SSL)" --> SupabaseDB
    RBAC -- "7. Append Security & Mutation Events" --> AuditTable

```

*Figure 2: System architecture and request routing on Vercel.*

**Arrow Explanations:**

1. **Browser** $\rightarrow$ **Vercel Edge (Frontend Routes):** The browser requests UI routes such as `/login`, `/dashboard`, or `/admin`. Vercel Edge serves the compiled React Single-Page Application so client-side routing renders the interface.

2. **Vercel Edge** $\rightarrow$ **Static CDN:** Non-API paths fall through to `/frontend/$1`, delivering cached static JavaScript and CSS assets directly from Vercel's edge network.

3. **Browser** $\rightarrow$ **Vercel Edge (API Requests):** The React API client sends JSON requests to `/api/*` attaching the in-memory `access_token` via `Authorization: Bearer <token>` and automatically sending the `httpOnly` `refresh_token` cookie.

4. **Vercel Edge** $\rightarrow$ **Serverless API:** `vercel.json` intercepts all `/api/(.*)` traffic first and routes it to the Python serverless entry point `backend/main.py`.

5. **Serverless API** $\rightarrow$ **RBAC & Auth Layer:** FastAPI dependencies validate the JWT signature, check user existence and `is_banned` state, and enforce role, ownership, or group flags before executing business logic.

6. **RBAC Layer** $\rightarrow$ **Supabase PostgreSQL:** Authorized queries execute over TLS via SQLModel and `pg8000` against Supabase's connection pooler (`port 6543`).

7. **RBAC Layer** $\rightarrow$ **Audit Logs:** Every login, failed attempt, permission change, ban, or bulk moderation writes a structured audit record to `audit_logs` within the database transaction.

### C3. Backend and Frontend Structure

```
backend/
├── main.py           # FastAPI app entry, CORS, global exception handler, /api routes & /api/seed
├── database.py       # SQLModel engine configuration (Supabase PostgreSQL / SQLite fallback) & session generator
├── models.py         # SQLModel table definitions (User, UserSession, Group, GroupMember, Event, AuditLog)
├── auth.py           # Password peppering/bcrypt, HS256 JWT creation/decoding, SHA-256 token hashing, audit helper
├── rbac.py           # Reusable FastAPI dependencies (get_current_user, require_admin, verify_event_access)
├── schemas.py        # Pydantic request/response DTOs with input validation
├── requirements.txt  # Backend Python dependencies
└── tests/            # Pytest suite verifying auth, JWT rotation, RBAC permissions, and admin rules

```

```
frontend/
├── index.html        # Root HTML template
├── vite.config.ts    # Vite build and local dev proxy configuration
└── src/
    ├── App.tsx           # React Router setup and ProtectedRoute / AdminRoute guards
    ├── api/
    │   └── client.ts     # Fetch wrapper attaching Bearer token and auto-retrying once on 401 via /api/auth/refresh
    ├── context/
    │   └── AuthContext.tsx # Global auth state, in-memory access token storage, login/logout/refresh lifecycle
    └── pages/
        ├── LoginPage.tsx     # Visitor authentication form with lockout/error banners
        ├── SignupPage.tsx    # Visitor registration form with client & server validation
        ├── DashboardPage.tsx # User workspace: Personal & Group Events, Shared Groups matrix, Profile & Sessions
        └── AdminPage.tsx     # Admin control center: Stats, Users, Moderation, Audit Logs, Security View, CSV Export

```

### C4. Data Model

```
erDiagram
    USERS ||--o{ USER_SESSIONS : "has active"
    USERS ||--o{ EVENTS : "owns (owner_id)"
    USERS ||--o{ EVENTS : "assigned to (assigned_to)"
    USERS ||--o{ GROUPS : "owns (owner_id)"
    USERS ||--o{ GROUP_MEMBERS : "belongs to"
    GROUPS ||--o{ GROUP_MEMBERS : "has members"
    GROUPS ||--o{ EVENTS : "contains"
    USERS ||--o{ AUDIT_LOGS : "triggers"

    USERS {
        int id PK
        string email UK
        string full_name
        string password_hash
        string role
        bool is_banned
        string ban_reason
        int failed_login_attempts
        datetime locked_until
        datetime created_at
    }
    USER_SESSIONS {
        int id PK
        int user_id FK
        string refresh_token_hash UK
        string ip_address
        string user_agent
        bool is_revoked
        datetime expires_at
        datetime created_at
    }
    GROUPS {
        int id PK
        string name
        string description
        int owner_id FK
        datetime created_at
    }
    GROUP_MEMBERS {
        int id PK
        int group_id FK
        int user_id FK
        bool can_create
        bool can_edit
        bool can_assign
    }
    EVENTS {
        int id PK
        string title
        string description
        string category
        string venue
        datetime start_time
        datetime end_time
        int capacity
        int owner_id FK
        int group_id FK
        int assigned_to FK
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string target_type
        string target_id
        string details
        string ip_address
        datetime created_at
    }

```

*Figure 3: Normalized Entity-Relationship (ER) diagram of the PostgreSQL database.*

#### Core Schema Tables

| Table | Key Columns & Types | Keys, Constraints & Indexes | Purpose | 
| ----- | ----- | ----- | ----- | 
| **`users`** | `id` (INT), `email` (VARCHAR), `full_name` (VARCHAR), `password_hash` (VARCHAR), `role` (VARCHAR), `is_banned` (BOOL), `ban_reason` (VARCHAR, NULL), `failed_login_attempts` (INT), `locked_until` (TIMESTAMP, NULL) | `PK(id)`, `UNIQUE INDEX(email)`, default `role='user'`, `is_banned=False` | Stores user credentials, system roles, ban state, and brute-force lockout counters. | 
| **`user_sessions`** | `id` (INT), `user_id` (INT), `refresh_token_hash` (VARCHAR), `ip_address` (VARCHAR), `user_agent` (VARCHAR), `is_revoked` (BOOL), `expires_at` (TIMESTAMP) | `PK(id)`, `FK(user_id -> users.id)`, `UNIQUE INDEX(refresh_token_hash)` | Tracks active device sessions and enables refresh token rotation and revocation. | 
| **`groups`** | `id` (INT), `name` (VARCHAR), `description` (VARCHAR), `owner_id` (INT), `created_at` (TIMESTAMP) | `PK(id)`, `FK(owner_id -> users.id)` | Represents committee workspaces with a designated group owner. | 
| **`group_members`** | `id` (INT), `group_id` (INT), `user_id` (INT), `can_create` (BOOL), `can_edit` (BOOL), `can_assign` (BOOL) | `PK(id)`, `FK(group_id -> groups.id)`, `FK(user_id -> users.id)` | Junction table storing per-member granular permissions inside each group. | 
| **`events`** | `id` (INT), `title` (VARCHAR), `description` (TEXT), `category` (VARCHAR), `venue` (VARCHAR), `start_time` (TIMESTAMP), `end_time` (TIMESTAMP), `capacity` (INT), `owner_id` (INT), `group_id` (INT, NULL), `assigned_to` (INT, NULL) | `PK(id)`, `FK(owner_id -> users.id)`, `FK(group_id -> groups.id)`, `FK(assigned_to -> users.id)` | Stores both personal events (`group_id IS NULL`) and shared committee events. | 
| **`audit_logs`** | `id` (INT), `user_id` (INT, NULL), `action` (VARCHAR), `target_type` (VARCHAR), `target_id` (VARCHAR), `details` (TEXT), `ip_address` (VARCHAR), `created_at` (TIMESTAMP) | `PK(id)`, `FK(user_id -> users.id)`, `INDEX(action)`, `INDEX(created_at)` | Immutable trail of authentication, RBAC, and administrative events. | 

*Table 18: Database tables, columns, keys, and constraints.*

### C5. API Design

All API routes are prefixed with `/api`. Errors follow FastAPI's standardized JSON envelope: `{"detail": "<human-readable reason>"}`.

| Method & Path | Auth | Required Role / Permission | Request Body | Success | Error Statuses | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `GET /api/health` | No | Public | — | `200` | `500` | 
| `POST /api/seed` | No | Public (Idempotent demo seed) | — | `200` | `500` | 
| `POST /api/auth/signup` | No | Public | `{full_name, email, password}` | `201` | `400`, `422` | 
| `POST /api/auth/login` | No | Public (Unbanned) | `{email, password}` | `200` | `401`, `403`, `429` | 
| `POST /api/auth/refresh` | Cookie | Valid `refresh_token` cookie | — | `200` | `401`, `403` | 
| `POST /api/auth/logout` | Cookie | Authenticated | — | `200` | `401` | 
| `GET /api/auth/me` | JWT | Authenticated | — | `200` | `401`, `403` | 
| `PATCH /api/auth/me` | JWT | Authenticated | `{full_name}` | `200` | `401`, `422` | 
| `POST /api/auth/change-password` | JWT | Authenticated | `{current_password, new_password}` | `200` | `400`, `401` | 
| `GET /api/auth/sessions` | JWT | Authenticated | — | `200` | `401` | 
| `DELETE /api/auth/sessions/{id}` | JWT | Session Owner | — | `200` | `403`, `404` | 
| `GET /api/events` | JWT | Authenticated (Filtered by owner/group) | Query: `search`, `category` | `200` | `401` | 
| `POST /api/events` | JWT | User (or Group `can_create` / Owner) | `{title, description, category, venue, start_time, end_time, capacity, group_id?, assigned_to?}` | `201` | `403`, `422` | 
| `PATCH /api/events/{id}` | JWT | Owner, Group `can_edit`, or `can_assign` (`assigned_to` only) | Partial event fields | `200` | `403`, `404`, `422` | 
| `DELETE /api/events/{id}` | JWT | Owner or Group `can_edit` / Owner | — | `200` | `403`, `404` | 
| `GET /api/groups` | JWT | Authenticated (Member or Owner) | — | `200` | `401` | 
| `POST /api/groups` | JWT | Authenticated | `{name, description}` | `201` | `422` | 
| `POST /api/groups/{id}/members` | JWT | Group Owner | `{email, can_create, can_edit, can_assign}` | `201` | `403`, `404` | 
| `PATCH /api/groups/{id}/members/{uid}` | JWT | Group Owner | `{can_create, can_edit, can_assign}` | `200` | `403`, `404` | 
| `DELETE /api/groups/{id}/members/{uid}` | JWT | Group Owner | — | `200` | `403`, `404` | 
| `DELETE /api/groups/{id}` | JWT | Group Owner | — | `200` | `403`, `404` | 
| `GET /api/admin/stats` | JWT | `role == "admin"` | — | `200` | `403` | 
| `GET /api/admin/users` | JWT | `role == "admin"` | Query: `search`, `role`, `is_banned`, `skip`, `limit` | `200` | `403` | 
| `GET /api/admin/users/{id}` | JWT | `role == "admin"` | — | `200` | `403`, `404` | 
| `POST /api/admin/users/{id}/ban` | JWT | `role == "admin"` (Target non-admin) | `{reason}` | `200` | `403`, `404` | 
| `POST /api/admin/users/{id}/unban` | JWT | `role == "admin"` | — | `200` | `403`, `404` | 
| `PATCH /api/admin/users/{id}/role` | JWT | `role == "admin"` (Target != self) | `{role}` | `200` | `403`, `404` | 
| `POST /api/admin/events/bulk-delete` | JWT | `role == "admin"` | `{ids: int[]}` | `200` | `403` | 
| `GET /api/admin/audit-logs` | JWT | `role == "admin"` | Query: `action`, `user_id`, `skip`, `limit` | `200` | `403` | 
| `GET /api/admin/audit-logs/export` | JWT | `role == "admin"` | Query: `action`, `user_id` | `200` (CSV) | `403` | 
| `GET /api/admin/security` | JWT | `role == "admin"` | — | `200` | `403` | 

*Table 19: Complete REST API endpoint specification.*

### C6. JWT Authentication Design

```
sequenceDiagram
    actor Client as Browser (React)
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    Client->>API: POST /api/auth/login {email, password}
    API->>DB: Verify peppered bcrypt hash & check lockout
    DB-->>API: User valid
    API->>DB: Insert UserSession (SHA-256 refresh hash)
    API-->>Client: 200 OK {access_token (15m)} + Set-Cookie refresh_token (HttpOnly, 7d)

    Client->>API: GET /api/events (Authorization: Bearer access_token)
    API-->>Client: 200 OK [events]

    Note over Client,API: 15 minutes later — Access Token expires
    Client->>API: GET /api/events (expired access_token)
    API-->>Client: 401 Unauthorized

    Client->>API: POST /api/auth/refresh (sends HttpOnly refresh_token cookie)
    API->>DB: Lookup SHA-256(cookie) in user_sessions
    alt Token valid & not revoked
        API->>DB: Revoke old session, create rotated session
        API-->>Client: 200 OK {new access_token} + Set-Cookie rotated refresh_token
        Client->>API: Retry GET /api/events (new access_token)
        API-->>Client: 200 OK [events]
    else Token already revoked (Reuse Detected!)
        API->>DB: Revoke ALL sessions for user_id
        API-->>Client: 401 Unauthorized (Force Logout)
    end

```

*Figure 4: Sequence diagram of login, protected requests, silent refresh rotation, and reuse detection.*

| Claim | Type | Description | 
| ----- | ----- | ----- | 
| `sub` | `string` | Authenticated user's integer primary key (`str(user.id)`). | 
| `role` | `string` | System role (`"user"` or `"admin"`) for fast client UI rendering and server verification. | 
| `iat` | `integer` | Issued-at UTC Unix timestamp. | 
| `exp` | `integer` | Expiration UTC Unix timestamp (`iat + 900` seconds / 15 minutes). | 

*Table 20: JWT access token payload claims.*

**Security Architecture Decisions:**

* **Signing & Secret Management:** Signed with `HS256` using `JWT_SECRET_KEY` injected via Vercel Environment Variables.

* **Token Storage & XSS/CSRF Mitigation:** The short-lived `access_token` is held in React memory (`AuthContext`), preventing XSS scripts from reading it out of `localStorage`. The 7-day `refresh_token` is stored in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie so JavaScript cannot access it, while `SameSite=Lax` and CORS origin restrictions prevent cross-site request forgery.

* **Server-Side Per-Request Checks:** On every authenticated request, `get_current_user` verifies the JWT signature and expiry, loads the fresh `User` row from PostgreSQL, and verifies `user is not None` and `not user.is_banned`.

* **Frontend 401 Interceptor:** `frontend/src/api/client.ts` intercepts any `401` response once, calls `POST /api/auth/refresh`, updates the in-memory token, and retries the original request seamlessly; if refresh fails, it clears state and redirects to `/login`.

### C7. RBAC Design

```
flowchart TD
    Req["Incoming Protected Request"] --> TokenCheck{"1. Valid JWT Signature & Not Expired?"}
    TokenCheck -- No --> R401["401 Unauthorized"]
    TokenCheck -- Yes --> UserCheck{"2. User Exists & Not Banned?"}
    UserCheck -- No --> R403Ban["403 Forbidden (Banned / Inactive)"]
    UserCheck -- Yes --> AdminRoute{"3. Admin Endpoint?"}
    AdminRoute -- Yes --> IsAdmin{"user.role == 'admin'?"}
    IsAdmin -- No --> R403Admin["403 Forbidden (Admin Required)"]
    IsAdmin -- Yes --> Handler["Execute Handler & Log Audit"]
    AdminRoute -- No --> ScopeCheck{"4. Personal or Group Resource?"}
    ScopeCheck -- Personal --> OwnerCheck{"record.owner_id == user.id?"}
    OwnerCheck -- No --> R403Owner["403 Forbidden (Not Owner)"]
    OwnerCheck -- Yes --> Handler
    ScopeCheck -- Group --> GroupPerm{"5. Group Owner OR Required Flag (create/edit/assign)?"}
    GroupPerm -- No --> R403Perm["403 Forbidden (Insufficient Group Permission)"]
    GroupPerm -- Yes --> Handler

```

*Figure 5: Five-stage server-side authorization pipeline.*

**Roles and Permission Constants (`backend/rbac.py`):**

* System Roles: `ROLE_USER = "user"`, `ROLE_ADMIN = "admin"`

* Group Permissions: `PERM_CREATE = "create"`, `PERM_EDIT = "edit"`, `PERM_ASSIGN = "assign"`

```
def verify_event_access(
    event: Event,
    user: User,
    db: Session,
    required_perm: str,
    updating_only_assignee: bool = False,
) -> None:
    if event.group_id is None:
        if event.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this personal event")
        return

    group = db.get(Group, event.group_id)
    if group and group.owner_id == user.id:
        return

    member = db.exec(
        select(GroupMember).where(GroupMember.group_id == event.group_id, GroupMember.user_id == user.id)
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this event's group")

    if required_perm == PERM_EDIT and updating_only_assignee and member.can_assign:
        return
    if required_perm == PERM_EDIT and not member.can_edit:
        raise HTTPException(status_code=403, detail="Group edit permission required")

```

*Code Excerpt 1: Centralized group and ownership verification in `backend/rbac.py`.*

**Query-Level Isolation & Extensibility:**

* Read queries (`GET /api/events`) filter directly in SQL using `or_(Event.owner_id == user.id, Event.group_id.in_(member_group_ids))` so unauthorized records are never even loaded into application memory.

* Adding a new permission (e.g., `can_approve`) requires adding one boolean column to `GroupMember` and one `PERM_APPROVE` branch inside `verify_event_access`.

### C8. Admin Dashboard Design

```
flowchart LR
    AdminUI["Admin Dashboard (/admin)"]
    T1["Overview Cards"] --> E1["GET /api/admin/stats"]
    T2["Users Table & Detail Modal"] --> E2["GET /api/admin/users & /{id}"]
    T2 --> E3["POST /ban, /unban & PATCH /role"]
    T3["Content Moderation"] --> E4["POST /api/admin/events/bulk-delete"]
    T4["Audit Log & CSV Export"] --> E5["GET /api/admin/audit-logs & /export"]
    T5["Security Analytics"] --> E6["GET /api/admin/security"]

```

*Figure 6: Admin dashboard views and corresponding backend API endpoints.*

| Admin Tab / View | Endpoints Called | Filters & Pagination | Actions Supported | Audit Events Recorded | 
| ----- | ----- | ----- | ----- | ----- | 
| **Overview** | `GET /api/admin/stats` | — | View live user, ban, session, event, and group counts. | — | 
| **Users Management** | `GET /api/admin/users`, `GET /api/admin/users/{id}`, `POST /ban`, `POST /unban`, `PATCH /role`, `DELETE /sessions/{id}` | `search` (email/name), `role`, `is_banned`, `skip`, `limit` | Inspect user sessions/logs, ban with reason, unban, promote to admin, revoke individual device sessions. | `USER_BANNED`, `USER_UNBANNED`, `USER_ROLE_CHANGED`, `ADMIN_SESSION_REVOKED` | 
| **Content Moderation** | `GET /api/events`, `GET /api/groups`, `POST /api/admin/events/bulk-delete`, `POST /api/admin/groups/bulk-delete` | `search`, `category`, `skip`, `limit` | Multi-select events or groups and execute bulk deletion; backend returns `{affected, skipped}`. | `ADMIN_BULK_DELETE_EVENTS`, `ADMIN_BULK_DELETE_GROUPS` | 
| **Activity Log** | `GET /api/admin/audit-logs`, `GET /api/admin/audit-logs/export` | `action`, `user_id`, `skip`, `limit` | Filter historical audit trail and download filtered records as `audit_logs.csv`. | `ADMIN_EXPORT_AUDIT_CSV` | 
| **Security View** | `GET /api/admin/security` | Top IPs & targeted accounts | Monitor failed login spikes, active lockouts, and recent `401`/`403` security events. | — | 

*Table 21: Admin dashboard capabilities, filters, and audit trail mapping.*

### C9. Security Design and Threats

| Threat | Mitigation / Defence | Implementing File / Module | 
| ----- | ----- | ----- | 
| **Password Database Leak** | Salted `bcrypt` hashing combined with a secret server-side `PASSWORD_PEPPER` from environment variables. | `backend/auth.py` (`hash_password`) | 
| **Stolen Access Token** | Short 15-minute expiration (`exp` claim) and in-memory storage (never `localStorage`). | `backend/auth.py`, `frontend/src/context/AuthContext.tsx` | 
| **Stolen Refresh Token** | Stored in `HttpOnly`, `Secure` cookie; SHA-256 hashed in DB; single-use rotation revokes all sessions on reuse. | `backend/main.py` (`/api/auth/refresh`), `backend/models.py` | 
| **Brute-Force Login** | Progressive account lockout after $5$ failed attempts (`429 Too Many Requests` for 15 minutes). | `backend/main.py` (`/api/auth/login`) | 
| **Privilege Escalation** | Server-side `require_admin` dependency; signup always forces `role="user"`; admins cannot self-demote or ban peer admins. | `backend/rbac.py`, `backend/main.py` | 
| **Unauthorized Record Access** | SQL-level `owner_id` and `group_id` filtering plus `verify_event_access` checks on every mutation. | `backend/rbac.py`, `backend/main.py` | 
| **Cross-Site Scripting (XSS)** | React automatic JSX escaping and `HttpOnly` cookie protection for refresh tokens. | `frontend/src/*`, `backend/main.py` | 
| **Cross-Site Request Forgery (CSRF)** | `SameSite=Lax` cookie policy paired with explicit `Authorization: Bearer` header requirement on mutations. | `backend/main.py`, `frontend/src/api/client.ts` | 
| **CORS Misuse** | Strict `CORSMiddleware` allowlist (`FRONTEND_URL` + localhost dev origin) with `allow_credentials=True`. | `backend/main.py` | 
| **Secrets in Repository** | `.env` excluded in `.gitignore`; `.env.example` holds placeholder names only; test credentials kept out of Git. | `.gitignore`, `.env.example` | 
| **SQL Injection** | Parameterized SQL queries generated exclusively via SQLModel / SQLAlchemy bound parameters. | `backend/database.py`, `backend/main.py` | 
| **Mass Assignment / Over-Posting** | Dedicated Pydantic request schemas (`EventCreate`, `EventUpdate`, `UserSignup`) ignoring `id`, `role`, or `is_banned`. | `backend/schemas.py` | 

*Table 22: Security threat model and defensive controls.*

### C10. Deployment on Vercel

```
flowchart LR
    GitHub["GitHub Repository (main branch)"] -- "Git Push Trigger" --> VercelBuild["Vercel CI/CD Build"]
    VercelBuild --> StaticBuild["@vercel/static-build (frontend/package.json -> frontend/dist)"]
    VercelBuild --> PythonBuild["@vercel/python (root requirements.txt -> backend/main.py)"]
    StaticBuild --> Domain["campus-event-management-system-2110.vercel.app"]
    PythonBuild --> Domain
    PythonBuild <-- "TLS Pooler (port 6543)" --> Supabase[("Supabase PostgreSQL")]

```

*Figure 7: Unified Vercel deployment pipeline and database connectivity.*

**Architecture & Routing Configuration:**

* **Single-Origin Deployment (`vercel.json`):** Both the React SPA and FastAPI backend deploy under `https://campus-event-management-system-2110.vercel.app/`. `vercel.json` routes `/api/(.*)` to `backend/main.py` using `@vercel/python` and serves all other paths from `frontend/dist` with SPA fallback to `index.html`.

* **Root Dependency Manifest:** A root `requirements.txt` ensures Vercel's Python runtime installs `fastapi`, `sqlmodel`, `pg8000`, `python-jose[cryptography]`, `passlib[bcrypt]`, and `bcrypt==4.0.1` into the serverless bundle.

* **Database Hosting:** Supabase PostgreSQL connected via the Transaction/Session Pooler (`...pooler.supabase.com:6543/postgres`) using the pure-Python `postgresql+pg8000://` SQLAlchemy dialect.

* **Redeployment:** Pushing to `main` on GitHub triggers an automatic build and atomic production promotion on Vercel; manual redeploys can also be triggered from **Vercel Dashboard** $\rightarrow$ **Deployments** $\rightarrow$ **Redeploy**.

| Environment Variable | Purpose | 
| ----- | ----- | 
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+pg8000://...`) pointing to Supabase. | 
| `JWT_SECRET_KEY` | Cryptographic secret key used to sign and verify HS256 JWT access tokens. | 
| `PASSWORD_PEPPER` | Server-side secret appended to passwords prior to `bcrypt` hashing. | 
| `FRONTEND_URL` | Production origin URL (`https://campus-event-management-system-2110.vercel.app`) allowed by CORS. | 
| `ENVIRONMENT` | Set to `production` to enforce `Secure` cookie attributes over HTTPS. | 

*Table 23: Production environment variables configured in Vercel (values omitted).*

### C11. Testing

The project uses a two-tier testing strategy:

1. **Automated Integration Tests (`pytest`):** Located in `backend/tests/`, running against an isolated test database via FastAPI `TestClient` to verify token expiration, signature tampering, refresh rotation reuse detection, cross-user ownership isolation, group permission flags, admin self-protection, and brute-force lockout.

2. **Live Production End-to-End Verification:** Executed directly on `https://campus-event-management-system-2110.vercel.app/` across multiple browser sessions (`admin1`, `alice`, `bob`, `charlie`) to confirm real cookie behavior, Supabase persistence, and RBAC UI error handling.

**Command to Run Automated Tests:**

```
cd backend
pytest -v

```

| Test Case Name | Requirement Checked | Expected Outcome | Result | 
| ----- | ----- | ----- | ----- | 
| `test_signup_and_login_flow` | `FR-AUTH-01`, `FR-AUTH-03` | Registers user, stores peppered hash, returns JWT + `httpOnly` cookie (`200`). | PASS | 
| `test_expired_and_tampered_jwt_rejected` | `FR-AUTH-03` | Expired or modified JWT returns `401 Unauthorized`. | PASS | 
| `test_refresh_rotation_and_reuse_revocation` | `FR-AUTH-05` | Rotates refresh token; reusing old token revokes all user sessions (`401`). | PASS | 
| `test_brute_force_login_lockout` | `FR-AUTH-08` | 6th consecutive failed login returns `429 Too Many Requests`. | PASS | 
| `test_personal_event_ownership_isolation` | `FR-RBAC-02` | User B cannot read, edit, or delete User A's personal event (`403`). | PASS | 
| `test_group_mixed_permissions_matrix` | `FR-RBAC-03`, `FR-RBAC-04` | `create` allows creation; `edit` allows full edit; `assign` allows `assigned_to` only and rejects venue edit (`403`). | PASS | 
| `test_banned_user_immediate_rejection` | `FR-RBAC-07` | Banned user's next request is rejected with `403 Forbidden`. | PASS | 
| `test_admin_self_and_peer_protection` | `FR-RBAC-06` | Admin cannot ban another admin or demote self (`403 Forbidden`). | PASS | 
| `test_admin_bulk_delete_and_csv_export` | `FR-ADM-06`, `FR-ADM-07` | Returns `{affected, skipped}` counts and valid CSV matching filters (`200`). | PASS | 

*Table 24: Automated and live verification test matrix.*

## Part D. Evidence: Screenshots of the Running Application

*(Instructions for PDF Export: Capture each screenshot on `https://campus-event-management-system-2110.vercel.app/` with the browser address bar and logged-in user visible, mask any sensitive tokens/passwords, and insert the images below each caption before exporting to PDF.)*

### D1. User Side

* **\[Insert Screenshot S1\]**

  **Caption S1 (`FR-AUTH-01`):** Registration and login page on Vercel showing client/server validation feedback when submitting an invalid input.

* **\[Insert Screenshot S2\]**

  **Caption S2 (`FR-DOMAIN-03`, `FR-RBAC-02`):** Logged-in user dashboard (`alice@campus.edu`) displaying only events owned by Alice or shared with her groups.

* **\[Insert Screenshot S3\]**

  **Caption S3 (`FR-AUTH-09`):** Profile & Sessions tab demonstrating password change rejection when an incorrect current password is entered.

* **\[Insert Screenshot S4\]**

  **Caption S4 (`FR-AUTH-07`):** Active device sessions list displaying IP address, user-agent, and the **Revoke** button removing a session.

* **\[Insert Screenshot S5\]**

  **Caption S5 (`FR-RBAC-03`):** Shared Groups view for *IUB Computer Club Committee* showing `alice@campus.edu` (Owner), `bob@campus.edu` (`create`, `edit`), and `charlie@campus.edu` (`assign` only).

* **\[Insert Screenshot S6\]**

  **Caption S6 (`FR-RBAC-04`):** Action denied by RBAC when `charlie@campus.edu` attempts to edit a group event's venue, showing the red `403` banner in the UI and the `403 Forbidden` response in DevTools Network tab.

### D2. Security Behaviour

* **\[Insert Screenshot S7\]**

  **Caption S7 (`FR-AUTH-03`):** Browser DevTools Network tab showing the `Authorization: Bearer <masked>` header and an expired JWT returning `401 Unauthorized`.

* **\[Insert Screenshot S8\]**

  **Caption S8 (`FR-AUTH-05`):** `POST /api/auth/refresh` returning a fresh `200 OK` access token alongside the `HttpOnly` `refresh_token` cookie visible in the Application tab.

* **\[Insert Screenshot S9\]**

  **Caption S9 (`FR-RBAC-07`):** A banned user account immediately rejected with `403 Forbidden` upon attempting their next request.

### D3. Admin Dashboard

* **\[Insert Screenshot S10\]**

  **Caption S10 (`FR-ADM-01`):** Admin Dashboard overview cards displaying real user, banned account, active session, event, and group statistics.

* **\[Insert Screenshot S11\]**

  **Caption S11 (`FR-ADM-02`):** Admin Users directory with search bar, role/status filters, and pagination controls.

* **\[Insert Screenshot S12\]**

  **Caption S12 (`FR-ADM-03`):** Admin User Detail view showing the target user's active sessions and recent audit log entries.

* **\[Insert Screenshot S13\]**

  **Caption S13 (`FR-ADM-04`):** Ban user dialog with a mandatory reason entered and the resulting banned badge state in the users table.

* **\[Insert Screenshot S14\]**

  **Caption S14 (`FR-ADM-06`):** Admin content moderation view showing bulk event selection and the `{affected, skipped}` confirmation result.

* **\[Insert Screenshot S15\]**

  **Caption S15 (`FR-ADM-07`):** Filterable Activity Log recording the login, RBAC denial, ban, and bulk moderation actions performed above.

* **\[Insert Screenshot S16\]**

  **Caption S16 (`FR-AUTH-08`, `FR-ADM-07`):** Admin Security View summarizing failed login attempts grouped by IP address and targeted email account.

* **\[Insert Screenshot S17\]**

  **Caption S17 (`FR-ADM-07`):** Filtered `audit_logs.csv` exported from the Admin Dashboard and opened in a spreadsheet viewer.

### D4. Deployment

* **\[Insert Screenshot S18\]**

  **Caption S18 (`NFR-REL-01`):** Vercel project overview showing the **Ready** production deployment and active domain `campus-event-management-system-2110.vercel.app`.

* **\[Insert Screenshot S19\]**

  **Caption S19 (`NFR-SEC-01`):** Vercel Project Settings $\rightarrow$ Environment Variables displaying `DATABASE_URL`, `JWT_SECRET_KEY`, `PASSWORD_PEPPER`, `FRONTEND_URL`, and `ENVIRONMENT` with values hidden.

* **\[Insert Screenshot S20\]**

  **Caption S20 (`FR-DOMAIN-01`):** Live interactive FastAPI Swagger UI documentation loaded at `https://campus-event-management-system-2110.vercel.app/api/docs`.

### D5. Tests

* **\[Insert Screenshot S21\]**

  **Caption S21 (`NFR-MNT-01`):** Terminal output of `pytest -v` showing all automated authentication, RBAC, ownership, and admin rule tests passing.

## Part E. Project Management and Conclusion

### E1. How to Run and Test Locally

#### Prerequisites

* Python 3.11+

* Node.js 20+ and `npm`

* Git

#### 1. Clone and Configure Environment Variables

```
git clone https://github.com/Jim-007/Campus-Event-Management-System-2110508.git
cd Campus-Event-Management-System-2110508
cp .env.example .env

```

Edit `.env` with local or Supabase values (never commit `.env`):

```
DATABASE_URL=sqlite:///./backend/campusconnect.db
JWT_SECRET_KEY=replace-with-local-random-secret-key
PASSWORD_PEPPER=replace-with-local-pepper-string
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development

```

#### 2. Start the Backend API

```
cd backend
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

```

The API will be available at `http://localhost:8000` and Swagger UI at `http://localhost:8000/api/docs`.

#### 3. Start the Frontend Application

Open a second terminal:

```
cd frontend
npm install
npm run dev

```

Open `http://localhost:5173` in your browser.

#### 4. Run Automated Tests & Seed Demo Accounts

```
cd backend
pytest -v

```

To populate the demo dataset (`2` admin accounts, `3` normal user accounts, and the mixed-permission group *IUB Computer Club Committee*), execute `POST /api/seed` via `/api/docs`. Test account user IDs and passwords are provided in the **PDF Report Appendix** and the course submission form (omitted from this repository file for security).

### E2. GitHub Work

Development was organized iteratively into feature branches and pull requests on `https://github.com/Jim-007/Campus-Event-Management-System-2110508`:

| Feature Area | Branch / PR Reference | Deliverable Summary | 
| ----- | ----- | ----- | 
| **Core Domain & Schema** | `main` (`a5cda5b`) | Normalized SQLModel schema (`users`, `events`, `groups`, `group_members`) and initial FastAPI + React scaffolding. | 
| **JWT Auth & Session Security** | `feature/jwt-auth` (`PR #4`) | Implemented peppered `bcrypt` hashing, 15m JWT access tokens, 7d `httpOnly` refresh rotation, reuse detection, and device session revocation. | 
| **RBAC & Mixed Group Permissions** | `main` (`3c2220e`) | Centralized `backend/rbac.py` ownership and `can_create` / `can_edit` / `can_assign` enforcement and frontend API retry interceptor. | 
| **Admin Dashboard & Audit Trail** | `main` (`0835881`) | Built `/admin` dashboard tabs, user ban/role controls, bulk event/group moderation, security metrics, audit logging, and CSV export. | 
| **Vercel Serverless Production** | `main` (`5a3ea44`) | Configured `vercel.json` rewrites, root `requirements.txt` with `pg8000`, Supabase PostgreSQL pooler connection, and production runtime fixes. | 

*Table 25: Summary of GitHub branches, pull requests, and delivered milestones.*

### E3. Limitations

1. **Stateless Lockout Persistence Across Cold Starts:** While failed login attempts are tracked in the `users` table (`failed_login_attempts`, `locked_until`), IP-level rate limiting relies on database queries rather than an in-memory Redis cache, adding slight latency under heavy traffic.

2. **No Email Verification or Password Reset Flow:** New registrations are activated immediately without sending an SMTP verification link, and forgotten passwords currently require an administrator to reset or recreate the account.

3. **Single-Tenant Campus Scope:** All groups and events share one global campus namespace rather than supporting multi-university tenant isolation.

### E4. Future Work

1. **Transactional Email Notifications & Verification:** Integrate Resend or SendGrid to verify `@iub.edu.bd` email addresses upon signup and notify assigned coordinators when added to an event.

2. **Calendar Export (`.ics`) & Conflict Detection:** Add automatic room/venue overlap detection so two committees cannot book the same auditorium at the same time, plus one-click `.ics` calendar downloads.

3. **Redis-Backed Sliding Window Rate Limiter:** Introduce Upstash Redis on Vercel Edge to block abusive IPs before requests reach Python serverless functions.

### E5. Sources, Libraries and Tools

| Name | Version / Link | Purpose | 
| ----- | ----- | ----- | 
| **FastAPI** | `0.115+` (`fastapi.tiangolo.com`) | Backend REST API framework and OpenAPI schema generation. | 
| **SQLModel** | `0.0.22+` (`sqlmodel.tiangolo.com`) | ORM models and database query layer. | 
| **React & Vite** | `React 19` / `Vite 6` (`react.dev`) | Frontend single-page application UI and bundler. | 
| **Tailwind CSS** | `3.x` (`tailwindcss.com`) | Utility-first responsive styling for dashboards and forms. | 
| **python-jose & passlib** | `3.3+` / `1.7.4` | HS256 JWT signing/verification and `bcrypt` password hashing. | 
| **Supabase & pg8000** | `PostgreSQL 15` (`supabase.com`) | Cloud PostgreSQL database and pure-Python SSL database driver. | 
| **Vercel** | `vercel.com` | Serverless backend and static frontend hosting platform. | 
| **Google Gemini (AI Assistant)** | Web Assistant | Used for troubleshooting Vercel serverless runtime/import errors (`sys.path`, `pg8000` dialect, `typing`/`datetime` imports) and structuring documentation; all generated code and SQL queries were manually verified against the live deployment and database schema. | 

*Table 26: External libraries, infrastructure platforms, and development tools used.*