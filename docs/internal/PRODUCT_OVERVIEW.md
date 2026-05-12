# Medical Booking Platform - Product Overview

## 1. Product Positioning

Medical Booking Platform is a full-stack healthcare scheduling and care-collaboration system designed for clinics and small-to-medium medical teams.

It unifies three core capabilities into one workflow:

- Appointment management
- Schedule and slot control
- Medical record completion and review

The platform supports role-based access for **Admin**, **Doctor**, and **Patient**, and provides a modern dashboard-driven experience for daily operations.

---

## 2. Target Users

### Admin

- Manage doctor and patient accounts
- Maintain platform operations and user lifecycle
- Access all appointments, records, and scheduling data

### Doctor

- Manage own schedule availability
- Confirm and complete appointments
- Record diagnosis and treatment details
- Upload medical attachments during completion (PostgreSQL mode)

### Patient

- Book appointments
- View own appointment status
- Access own completed medical records

---

## 3. Core Functional Modules

## 3.1 Authentication and Access Control

- JWT-based authentication (`login`, `refresh`, `logout`, `me`)
- Role-based authorization across all APIs and pages
- Login supports both **username** and **email**

## 3.2 Dashboard

- Real-time overview cards (doctors, patients, appointments, completion rate)
- Upcoming appointments and status distribution
- Quick actions for operational navigation

## 3.3 Appointments

- Create appointments with doctor/patient/date/time/reason
- Status flow:
  - `pending`
  - `confirmed`
  - `completed`
  - `cancelled`
- Confirm appointment with confirm info
- Complete appointment with diagnosis/treatment/advice
- Optional attachment upload in completion flow

## 3.4 Schedule (Time Slots)

- Calendar-based schedule management
- Daily slot availability settings (available/unavailable)
- Batch slot operations through card multi-select
- Per-day appointment counts and status stats in calendar cells

## 3.5 Medical Records

- Built from completed appointments
- Detail view includes reason, diagnosis, treatment plan, and advice
- Multi-dimensional filtering:
  - Date range
  - Patient
  - Doctor
- Server-side pagination for performance

## 3.6 Personal Center

- Update profile information
- Update contact details
- Avatar upload (PNG/JPG, <= 1MB)
- Secure password change with current password + confirmation

## 3.7 Content Portal

- Public department directory at `/portal/departments` and detail pages at `/portal/departments/<slug>`
- Public doctor list at `/portal/doctors` and detail at `/portal/doctors/<id>`
- Login page left panel shows a carousel of published departments with quick links to `Browse departments` and `Find a doctor`
- Admin manages department content directly (CRUD)
- Doctor introductions follow a draft → submit → admin approve/reject → publish workflow with status states `none` / `pending` / `approved` / `rejected`
- Rich text supports inline images served from MinIO (S3-compatible)
- `sitemap.xml` exposes published portal URLs for search engines

---

## 4. UX and Interaction Highlights

- Unified card/table/filter visual system
- Standardized dialog interactions for sensitive operations
- Drag-and-drop upload support for avatar and appointment attachments
- Required-field indicators and submit-time validation highlighting
- Pagination controls with page size selector (`10/20/50`) and clear range summary

---

## 5. Technical Architecture

## Backend

- **Framework**: Django 4.2 + Django REST Framework
- **Auth**: SimpleJWT
- **Docs**: drf-spectacular (OpenAPI + Swagger)
- **Database mode**:
  - Development: SQLite
  - Production: PostgreSQL

## Frontend

- **Framework**: Vue 3 + TypeScript + Vite
- **State**: Pinia
- **HTTP**: Axios with token interceptors and refresh flow

---

## 6. Data and Storage Strategy

- User avatars are stored as encoded image data in database fields
- Appointment completion attachments are accepted in UI and API
- Attachment persistence policy:
  - Enabled when backend DB is PostgreSQL
  - Rejected in SQLite mode by backend guard

---

## 7. API and Performance Design

- Core list endpoints support server-side filtering
- Appointment endpoint supports pagination (`page`, `page_size`, max `50`)
- Medical records and appointment lists use backend pagination to improve scalability

---

## 8. Security and Validation

- Role-constrained API operations
- Input validation for required fields and business rules
- Doctor account constraints:
  - Email required
  - Phone required
  - Phone uniqueness enforced
- Global uniqueness for email across platform users
- Password change follows secure flow with validator checks

---

## 9. Current Product Status

The platform is ready for day-to-day feature validation in development mode and is structured for production hardening with PostgreSQL, API docs, and role-based workflows already in place.

Key strengths at current stage:

- End-to-end appointment lifecycle
- Practical schedule tooling for doctors
- Medical record visibility and filtering
- Clean operational UX with modernized components

---

## 10. Recommended Next Product Steps

1. Add analytics and reporting module (doctor workload, completion KPI, cancellation trends)
2. Add notification center (appointment reminders and status updates)
3. Add audit trail for sensitive operations (user, timestamp, action logs)
4. Introduce patient-facing timeline view for historical records
5. Add full-text search optimization for large medical record datasets
