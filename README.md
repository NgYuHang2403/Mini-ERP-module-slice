# Mini ERP - Repair Work Order Tracker

## Overview
This project is a Django-based mini ERP module to track Parts and their Work Orders through repair steps and inspections.

It demonstrates:
- Django backend development
- Data modeling and validation
- Activity logging system
- Dockerized environment (PostgreSQL + MongoDB)

---

## Features
- Manage Parts and Work Orders
- Enforce business rules:
  - Only one OPEN work order per part
  - Work order can only close if all steps are DONE and PASS inspection exists
- Repair step tracking with ordered steps
- Inspection recording (PASS / FAIL)
- Append-only activity log
- Activity log viewing page

---

## Tech Stack
- Python / Django
- PostgreSQL (Docker)
- MongoDB (Docker)
- Docker Compose

---

## Setup Instructions

### 1. Clone repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

---

### 2. Create environment file
```bash
cp .env.example .env

---

### 3. Run with docker (need to have docker desktop installed)
docker compose up --build

---

### 4. Access the app
### App: http://127.0.0.1:8000/
### Admin: http://127.0.0.1:8000/admin/

---

### 5. Create superuser
```bash
docker compose exec web python manage.py createsuperuser

---

### 6. Run test (test can be found in test.py)
```bash
docker compose exec web python manage.py test

---

### 7. activity log viewing
```bash
/workorders/<id>/activity/
