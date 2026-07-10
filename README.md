# Palawan Operative Transportation Multi-Purpose Cooperative IMS

An undergraduate thesis project built with Django for managing cooperative operations, member records, vehicle information, documents, payments, renewals, announcements, QR login, and audit logs.

## Overview

This system is designed for a transportation cooperative that needs a centralized information management platform for staff, managers, and members. It supports administrative workflows such as account approval, batch and member tracking, document processing, payment monitoring, car wash compliance, renewal reminders, notifications, and email-based reporting.

## Key Features

- User registration and admin approval workflow
- Role-based accounts for superadmin, admin, manager, and client member users
- Member, vehicle, and batch management
- Document upload, review, approval, and renewal tracking
- Payment management for member-based and other payment categories
- Car wash compliance tracking and public customer records
- QR-based login utilities
- Announcement and notification system
- PDF exports and email delivery for reports
- Payment logs, car wash logs, and email audit history
- Member profile, vehicle, payment, and document dashboards for users

## Technology Stack

- Python 3
- Django 5.2
- SQLite for local development
- Django Crispy Forms and Widget Tweaks
- Django REST Framework for API endpoints
- WhiteNoise for static file serving
- QR code and image-processing libraries for QR login and document workflows

## Project Structure

- coopims/ - Django project configuration
- coop/ - Main application containing models, views, forms, signals, notifications, and management commands
- templates/ - HTML templates for admin and user interfaces
- static/ - CSS, JavaScript, fonts, images, and SASS assets
- media/ - Uploaded files and generated documents
- db.sqlite3 - Default local database

## Setup Instructions

1. Create and activate a virtual environment.
2. Install the dependencies from requirements.txt.
3. Run migrations.
4. Create an administrative account.
5. Start the development server.

Example commands:

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## Optional Seed Commands

The repository includes management commands that can be used to populate sample data:

- python manage.py populatemembers
- python manage.py populatevehicles
- python manage.py createsupergtx

## Configuration Notes

- Database defaults to SQLite through db.sqlite3.
- Static files are served with WhiteNoise.
- Media uploads are stored in the media directory.
- Update the secret key and email credentials in coopims/settings.py before any production use.
- The project is configured for a custom user model defined in coop.models.User.

## Application Modules

- Member and vehicle lifecycle management
- Document submission and approval workflows
- Payment years, payment types, and payment entries
- Car wash services and compliance monitoring
- Renewal reminders and renewal detail tracking
- Notifications and announcement broadcasting
- QR login and password reset verification flows
- Payment, car wash, and member log reporting

## Notes for Thesis Defense or Demonstration

This project is suitable for demonstrating a cooperative information system focused on reducing manual record keeping, improving accountability, and consolidating member-facing services into one platform.

If you plan to present it as part of an undergraduate thesis, you may want to replace this README title with your final thesis title and add the names of the researchers, adviser, institution, and deployment details.