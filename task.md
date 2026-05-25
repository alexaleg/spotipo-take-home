# Spotipo Full Stack Developer Interview Task

## Overview

Create an external captive portal for UniFi systems that displays a login page when users connect to Wi-Fi. This task evaluates your ability to integrate with external APIs, handle user authentication flows, and build full-stack solutions with specific technology constraints.

**Time Allocation:** 3-4 hours
**Deliverables:** GitHub repository + 3-minute [Loom](https://www.loom.com/) video

## Task Description

### Objective

Build an external captive portal system that:

1. Shows a login page to users connecting to UniFi-managed Wi-Fi
2. Collects user email addresses and stores them in a database
3. Authorizes users in the UniFi system via the controller API
4. Provides a complete Docker-based deployment solution

### Reference Documentation

Please review this article for UniFi external portal concepts:
[**https://www.spotipo.com/post/what-is-an-unifi-external-portal-server-054d2**](https://www.spotipo.com/post/what-is-an-unifi-external-portal-server-054d2)

## Technical Requirements

### Technology Stack (Mandatory)

- **Backend:** Flask (Python)
- **Database:** MySQL with SQLAlchemy ORM
- **Frontend:**
    - HTML templates
    - Tailwind CSS for styling
    - Alpine.js for JavaScript functionality
    - HTMX for interactivity (optional)
- **Deployment:** Docker Compose setup

### Core Functionality

### 1. Captive Portal Flow

`User connects to WiFi → Redirected to portal → Enter email → 
Store in database → Call UniFi API → User authorized → Internet access`

### 2. Required Endpoints

- `GET /` - Main portal login page
- `POST /authenticate` - Handle email submission and UniFi authorization
- `GET /success` - Success page after authorization
- `GET /admin` - Simple admin panel to view collected emails (optional)

### 3. Database Schema

Design appropriate tables to store:

- User email addresses
- Session information
- Authorization timestamps
- Any other relevant data

### 4. UniFi Integration

- Integrate with UniFi Controller API
- Call the guest authentication method
- Handle API authentication (username/password or API key)
- Manage potential API errors gracefully

### Implementation Details

### Flask Application Structure

`unifi-captive-portal/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates/
│       ├── login.html
│       ├── success.html
│       └── base.html
├── static/
│   └── css/
├── config.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md`

### UniFi API Integration

You'll need to:

- Research UniFi Controller API documentation
- Implement guest authorization endpoint calls
- Handle authentication to the controller
- Manage session state between portal and UniFi system

### Expected Deliverables

### 1. GitHub Repository

Complete codebase including:

- All source code files
- Docker Compose configuration
- Requirements.txt with dependencies
- README.md with setup instructions
- Environment configuration examples

### 2. Docker Compose Setup

- Flask application container
- MySQL database container
- Proper networking between services
- Environment variable configuration
- Volume mounting for data persistence

### 3. Loom Video (3 minutes)

Record a screencast covering:

- **Architecture overview** (30 seconds)
- **Code walkthrough** - key components and UniFi integration (90 seconds)
- **Docker deployment demonstration** (60 seconds)
