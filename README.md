# 🐦 Pipyrit - AI-Powered Immigration Assistant (Backend)

Pipyrit is a robust, production-ready backend built with **Django REST Framework (DRF)**. It serves as the engine for a modern immigration assistant platform, featuring AI-driven guided interviews, real-time case tracking, dynamic quizzes, and video streaming.

---

## 🚀 Key Features

- **Authentication:** Secure JWT-based auth with OTP verification and Password Recovery.
- **AI-Guided Interviews:** Dynamic, step-by-step interview flows with conditional logic.
- **Prep Hub (Quiz):** Real-time quizzes with difficulty-based scoring and automatic gTTS (Google Text-to-Speech) audio generation.
- **Smart Frames:** Professional video streaming with HTTP Range Request support (Seek/Skip enabled).
- **Case Management:** Detailed tracking of immigration cases (USCIS/EOIR) with document uploads.
- **Custom Admin Dashboard:** Real-time analytics, monthly earning charts, and comprehensive user management.
- **Payment & Subscriptions:** In-App Purchase (IAP) verification ready for Play Store and App Store.
- **Notifications:** Database-driven In-app notifications with unread count logic.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.x & Django REST Framework (DRF) |
| Database | PostgreSQL |
| Authentication | SimpleJWT (JSON Web Tokens) |
| Documentation | Swagger (drf-yasg) |
| Containerization | Docker & Docker Compose |
| Third-party | gTTS (Audio), RevenueCat (Subscription), ngrok (Tunnelling) |

---

## 📂 Project Structure

```
pipyrit-backend/
├── cases/          # Immigration case management logic
├── content/        # Video streaming, frames, and legal settings
├── payment/        # Subscription plans and IAP verification
├── quizzes/        # Quiz and Interview logic with audio generation
├── user/           # Custom User model, Profile, and Notifications
├── pipyrit/        # Core settings and project configuration
├── media/          # User-uploaded files (Videos, Thumbnails, Docs)
├── manage.py
├── Dockerfile
├── docker-compose.yml
└── .env            # Environment variables
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pipyrit-backend.git
cd pipyrit-backend
```

### 2. Configure Environment Variables

Create a `.env` file in the root and add your DB credentials, Secret Key, and Email settings.

### 3. Run with Docker

```bash
docker-compose up --build -d
```

### 4. Apply Migrations & Create Superuser

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## 📑 API Documentation

Once the server is running, access the full Swagger documentation at:

```
http://localhost:8000/swagger/
```

---

### 1. 🔐 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/register/` | Register a new user (Inactive by default) |
| `POST` | `/api/users/verify-otp/` | Verify email and activate account |
| `POST` | `/api/users/login/` | Get Access & Refresh JWT tokens |
| `POST` | `/api/users/resend-otp/` | Resend verification code |

---

### 2. 🔑 Password Recovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/forgot-password/` | Request reset OTP |
| `POST` | `/api/users/forgot-password/verify/` | Verify OTP & get temporary access token |
| `POST` | `/api/users/forgot-password/set-password/` | Set new password with token |

---

### 3. 📁 Case Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cases/my-cases/` | List all cases of the logged-in user |
| `POST` | `/api/cases/my-cases/` | Create a new immigration case |
| `GET` | `/api/cases/types/` | List dynamic case categories |

---

### 4. 📝 Prep Hub (Quiz & Interview)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/quizzes/quick-quiz/` | Get 25 random questions with audio links |
| `POST` | `/api/quizzes/quick-quiz/submit/` | Submit quiz and calculate points |
| `GET` | `/api/quizzes/interview-process/` | Filter questions by Category & Difficulty |
| `GET` | `/api/quizzes/results/{id}/` | Get detailed Q&A history with correct answers |

---

### 5. 🎬 Smart Frames & Video

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/system/frames/` | List available video clips |
| `GET` | `/api/system/stream/{id}/` | Stream video with Range Request support |

---

### 6. 🛡️ Admin Dashboard (Exclusive)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/admin/dashboard-home/` | Combined stats, Monthly Chart, and User List |
| `GET` | `/api/payment/admin/earnings/` | Detailed transaction history & Weekly revenue |
| `POST` | `/api/payment/admin/plans/` | Manage subscription packages |

---

## 🎖️ Senior Backend Implementation Notes

- **Custom Pagination:** All list endpoints return a detailed pagination object (`total_count`, `total_pages`, etc.) for easier frontend integration.
- **Standardized Response:** Every API follows the format:
  ```json
  {
    "code": 200,
    "success": true,
    "message": "...",
    "data": {}
  }
  ```
- **Automatic Audio:** Uses gTTS to convert Question text into MP3 automatically upon saving in the Admin panel.
- **Security:** Strict permission classes ensure Users can only access their own data, while Admins have full control over the Dashboard.

---

## 📄 License

This project is proprietary. All rights reserved.