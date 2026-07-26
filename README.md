# Pipyrit — AI-Powered Immigration Assistant · Backend API

> **Production-ready REST API** built with Django 5 & Django REST Framework.
> Powering an end-to-end US Immigration platform with AI-generated practice flows, case tracking, video streaming, and multi-tier subscription management.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Environment Variables](#environment-variables)
   - [Running with Docker](#running-with-docker)
   - [Local Development (without Docker)](#local-development-without-docker)
6. [API Reference](#api-reference)
7. [Authentication Flow](#authentication-flow)
8. [Security](#security)
9. [Design Decisions](#design-decisions)
10. [License](#license)

---

## Overview

Pipyrit's backend is a stateless REST API that serves a mobile/web immigration assistant. It handles:

- **Identity & Access** — JWT auth with OTP email verification and token refresh
- **AI Quiz & Interview Engine** — OpenAI GPT-4o-mini generates 25-question practice sets on demand, complete with gTTS audio
- **Immigration Case Tracking** — document uploads, status updates, admin oversight
- **Content Streaming** — HTTP Range Request video streaming (seek/skip support)
- **Subscription & Payments** — Stripe webhook processing, IAP verification (App Store / Play Store)
- **Admin Analytics** — dashboard with monthly revenue charts and user management

---

## Architecture

```
Client (Mobile / Web)
        │
        ▼
  [ Nginx / Proxy ]
        │
        ▼
  [ Gunicorn + Django ]
        │
   ┌────┴────────────────────────────┐
   │         Django Apps             │
   │  user · cases · quizzes         │
   │  content · payment · core       │
   └────┬───────────────┬────────────┘
        │               │
        ▼               ▼
  [ PostgreSQL ]   [ OpenAI API ]
                   [ Stripe API ]
                   [ gTTS / Email ]
```

The API follows a **resource-oriented** REST design. All responses conform to a single envelope format, and all list endpoints return a standard pagination object.

---

## Tech Stack

| Layer            | Technology                                          | Version   |
|------------------|-----------------------------------------------------|-----------|
| Language         | Python                                              | 3.11      |
| Framework        | Django + Django REST Framework                      | 5.2 / 3.17|
| Database         | PostgreSQL (psycopg2-binary)                        | Latest    |
| Authentication   | SimpleJWT                                           | 5.5       |
| AI Engine        | OpenAI API (GPT-4o-mini)                            | Latest    |
| Text-to-Speech   | Google Text-to-Speech (gTTS)                        | 2.5       |
| Payments         | Stripe                                              | Latest    |
| API Docs         | drf-yasg (Swagger UI)                               | 1.21      |
| i18n             | django-modeltranslation (EN / ES / HT)              | 0.20      |
| Containerization | Docker + Docker Compose                             | —         |
| Image Processing | Pillow                                              | 12.x      |

---

## Project Structure

```
pipyrit-backend/
│
├── pipyrit/                  # Django project root
│   ├── settings.py           # All configuration (env-driven)
│   ├── urls.py               # Root URL dispatcher
│   └── wsgi.py
│
├── user/                     # Auth, profile, notifications
│   ├── models.py             # Custom User, Profile, Notification, DeviceToken
│   ├── serializers.py
│   ├── views.py              # Register, Login, OTP, Password Reset, Admin
│   ├── signals.py            # Post-save hooks (profile creation, notifications)
│   └── utils.py
│
├── quizzes/                  # Quiz & AI Interview engine
│   ├── ai_engine.py          # OpenAI GPT integration (model auto-selection, caching)
│   ├── models.py             # QuizQuestion, InterviewQuestion, Results
│   ├── views.py              # Submit, save-score, Q&A history
│   └── serializers.py
│
├── cases/                    # Immigration case management
│   ├── models.py             # ImmigrationCase, CaseDocument, CaseType
│   └── views.py
│
├── content/                  # Video streaming & legal content
│   └── views.py              # HTTP Range Request streaming
│
├── payment/                  # Subscriptions & billing
│   ├── models.py             # SubscriptionPlan, UserSubscription, Transaction
│   └── views.py              # Stripe webhooks, IAP verification
│
├── core/                     # Shared utilities & base classes
│
├── locale/                   # i18n translation files (en, es, ht)
├── media/                    # User uploads (videos, thumbnails, audio, docs)
├── Dockerfile
├── docker-compose.yml
├── example.env               # Environment variable template
├── requirements.txt
└── manage.py
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose **or** Python 3.11 + PostgreSQL
- An `.env` file (see [Environment Variables](#environment-variables))
- OpenAI API key (required for Quiz & Interview features)
- Stripe account (required for payment features)

---

### Environment Variables

Copy `example.env` to `.env` and fill in your values:

```bash
cp example.env .env
```

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | `True` for dev, `False` for production | ✅ |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | ✅ |
| `DB_NAME` | PostgreSQL database name | ✅ |
| `DB_USER` | PostgreSQL user | ✅ |
| `DB_PASSWORD` | PostgreSQL password | ✅ |
| `DB_HOST` | PostgreSQL host | ✅ |
| `DB_PORT` | PostgreSQL port (default: `5432`) | ✅ |
| `OPENAI_API_KEY` | OpenAI API key (Quiz & Interview AI) | ✅ |
| `STRIPE_SECRET_KEY` | Stripe secret key | ✅ |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | ✅ |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | ✅ |
| `EMAIL_HOST` | SMTP host | ✅ |
| `EMAIL_HOST_USER` | SMTP user | ✅ |
| `EMAIL_HOST_PASSWORD` | SMTP password | ✅ |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins | ✅ |
| `DOCS_USERNAME` | Swagger UI basic-auth username | optional |
| `DOCS_PASSWORD` | Swagger UI basic-auth password | optional |
| `SECURE_SSL_REDIRECT` | Redirect HTTP→HTTPS (`True` in production) | prod |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie (`True` in production) | prod |
| `SESSION_COOKIE_SECURE` | Secure session cookie (`True` in production) | prod |

---

### Running with Docker

```bash
# 1. Build and start all services
docker compose up --build -d

# 2. Run database migrations
docker compose exec web python manage.py migrate

# 3. Create an admin superuser
docker compose exec web python manage.py createsuperuser

# 4. Collect static files (for production)
docker compose exec web python manage.py collectstatic --noinput
```

The API will be available at **`http://localhost:8000`**

Swagger UI: **`http://localhost:8000/swagger/`**

---

### Local Development (without Docker)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up .env
cp example.env .env
# Edit .env with your local DB and API credentials

# 4. Run migrations
python manage.py migrate

# 5. Start development server
python manage.py runserver
```

---

## API Reference

All endpoints require a `Bearer` token in the `Authorization` header unless marked **[public]**.

### Standard Response Envelope

Every response — success or error — follows this format:

```json
{
  "code": 200,
  "success": true,
  "message": "Operation successful",
  "timestamp": 1721999999,
  "data": {}
}
```

### Standard Pagination Object

All list endpoints return:

```json
{
  "code": 200,
  "success": true,
  "data": {
    "count": 100,
    "total_pages": 10,
    "current_page": 1,
    "next": "http://api/endpoint/?page=2",
    "previous": null,
    "results": []
  }
}
```

---

### 1. Authentication `[public]`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/register/` | Register a new user. Account is inactive until OTP verified. |
| `POST` | `/api/users/verify-otp/` | Verify email OTP and activate account |
| `POST` | `/api/users/login/` | Authenticate and receive `access` + `refresh` JWT tokens |
| `POST` | `/api/users/resend-otp/` | Resend OTP to email |
| `POST` | `/api/users/token/refresh/` | Rotate access token using a valid refresh token |

---

### 2. Password Recovery `[public]`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/forgot-password/` | Request a password reset OTP |
| `POST` | `/api/users/forgot-password/verify/` | Verify OTP and receive a temporary access token |
| `POST` | `/api/users/forgot-password/set-password/` | Set a new password using the temporary token |

---

### 3. User Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/profile/` | Retrieve authenticated user's profile |
| `PATCH` | `/api/users/profile/` | Update profile fields (name, avatar, etc.) |
| `POST` | `/api/users/change-password/` | Change password (requires current password) |

---

### 4. Case Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cases/my-cases/` | List authenticated user's immigration cases |
| `POST` | `/api/cases/my-cases/` | Submit a new immigration case with documents |
| `GET` | `/api/cases/my-cases/{id}/` | Retrieve a specific case detail |
| `GET` | `/api/cases/types/` | List all available case categories |

---

### 5. AI Quiz & Interview (Prep Hub)

> All quiz and interview questions are generated on-demand by GPT-4o-mini and include gTTS audio links.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/quizzes/quick-quiz/` | Generate 25 AI quiz questions for a given `case_type` |
| `POST` | `/api/quizzes/quick-quiz/submit/` | Submit answers and receive instant score |
| `POST` | `/api/quizzes/quick-quiz/save-score/` | Persist score from client-side evaluation |
| `GET` | `/api/quizzes/results/` | List the user's quiz result history |
| `GET` | `/api/quizzes/results/{id}/questions-answers/` | Get correct answers for a past quiz |
| `GET` | `/api/quizzes/interview-process/` | Generate 25 AI interview questions (by category & level) |
| `POST` | `/api/quizzes/interview-process/submit/` | Submit interview answers and receive confidence score |
| `POST` | `/api/quizzes/interview-process/save-score/` | Persist interview score |
| `GET` | `/api/quizzes/interview-results/` | List the user's interview result history |
| `GET` | `/api/quizzes/categories/` | List all interview categories |

---

### 6. Content & Video Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/system/frames/` | List available video content |
| `GET` | `/api/system/stream/{id}/` | Stream video with **HTTP Range Request** support (seek/skip enabled) |

---

### 7. Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/notifications/` | List in-app notifications with unread count |
| `POST` | `/api/users/notifications/{id}/read/` | Mark a notification as read |
| `POST` | `/api/users/notifications/read-all/` | Mark all notifications as read |

---

### 8. Payments & Subscriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/payment/plans/` | List available subscription plans |
| `POST` | `/api/payment/subscribe/` | Create or update a subscription |
| `POST` | `/api/payment/webhook/` | Stripe webhook endpoint `[public · Stripe-signed]` |
| `GET` | `/api/payment/my-subscription/` | Get current subscription status |

---

### 9. Admin Dashboard `[IsAdminUser]`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/admin/dashboard-home/` | Combined KPIs, monthly user/revenue chart, user list |
| `GET` | `/api/payment/admin/earnings/` | Detailed transaction history and weekly revenue breakdown |
| `GET/POST` | `/api/payment/admin/plans/` | Manage subscription packages |
| `GET` | `/api/users/admin/users/` | Full user list with filters and search |

---

## Authentication Flow

```
Register ──► Receive OTP ──► verify-otp ──► Account Active
                                                  │
                                                  ▼
                                             Login ──► Access Token (60 min)
                                                  │    Refresh Token (30 days)
                                                  │
                                    (Access expired) ──► /token/refresh/ ──► New Access Token
```

---

## Security

| Control | Implementation |
|---|---|
| **Secret Key** | Loaded from `SECRET_KEY` env variable — never hardcoded |
| **JWT Tokens** | Access: 60 min · Refresh: 30 days · Signed with `SECRET_KEY` |
| **Password Hashing** | Django's PBKDF2-SHA256 (4 validators enforced) |
| **Rate Limiting** | DRF throttling: `1000/day` (auth), `100/day` (anonymous) |
| **CORS** | `CORS_ALLOW_ALL_ORIGINS = False` by default; whitelist via env |
| **CSRF** | `CSRF_COOKIE_SECURE` env-controlled; enforced in production |
| **HTTPS** | `SECURE_SSL_REDIRECT`, `HSTS`, `SESSION_COOKIE_SECURE` all env-controlled |
| **XSS / Sniffing** | `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF` enabled |
| **Clickjacking** | `X_FRAME_OPTIONS = DENY` |
| **Object-level auth** | All user-scoped endpoints filter by `request.user` |
| **Admin isolation** | Admin endpoints require `IsAdminUser` permission class |

---

## Design Decisions

### Standardized Response Envelope
Every endpoint — including errors — returns the same JSON structure. This removes parsing ambiguity on the client side and enables a single SDK-level error handler.

### AI Model Auto-Selection
`ai_engine.py` queries the OpenAI models list at startup, selects the best available model from a preference list (`gpt-4o-mini → gpt-4o → gpt-4 → gpt-3.5-turbo`), and caches the result in memory per worker process. This avoids per-request model discovery overhead.

### Bulk Notification Dispatch
Admin notifications use `bulk_create()` instead of per-admin `save()` calls, keeping DB writes O(1) regardless of admin count.

### i18n Ready
All user-facing strings use `gettext_lazy(_(...))`. The platform supports English, Spanish, and Haitian Creole via `django-modeltranslation`.

### gTTS Audio on Save
Quiz and Interview question models auto-generate MP3 audio via gTTS on `save()` if no audio file exists. This happens synchronously in the admin panel.

### HTTP Range Streaming
The video streaming endpoint reads the `Range` request header and responds with `206 Partial Content`, enabling native seek and skip on mobile video players.

---

## License

This project is proprietary. All rights reserved. Unauthorized copying, distribution, or modification is strictly prohibited.