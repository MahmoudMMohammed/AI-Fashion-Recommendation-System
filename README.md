# Style Recommendation System

This is a fashion style recommendation system built with Django, PostgreSQL, Redis, and Celery.

## 🚀 Features

* Admin and test user setup
* Celery-based background task processing
* Postman collection for API testing
* Easy-to-seed development environment

---

## 🛠️ Setup Instructions

### 1. Install PostgreSQL 17

* Download: [PostgreSQL 17 Installer](https://sbp.enterprisedb.com/getfile.jsp?fileid=1259622)
* During installation, set a password for the `postgres` user.

* Download vector extension for style embeddings [pgvector v0.8.0](https://github.com/andreiramani/pgvector_pgsql_windows/releases/tag/0.8.0_17.3)
* Download the zip file and see README for installation

After installation, open **Command Prompt** and run:

```bash
psql -U postgres
```

Enter the password you set during installation, then run:

```sql
CREATE USER style_recommender WITH PASSWORD 'style_recommender';
ALTER USER style_recommender WITH SUPERUSER;
CREATE DATABASE "style_recommendation_system";
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 2. Install Redis

* For Windows: [Redis Releases](https://github.com/tporadowski/redis/releases)

---

### 3. Set Up the Django Project

Open the project directory in your terminal and run:

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_db
```

---

## 🧪 Running the Project

### Terminal 1: Start Django Development Server

```bash
python manage.py runserver
```

### Terminal 2: Start Celery Worker

```bash
celery -A fashionRecommendationSystem worker --loglevel=info --pool=solo
```

---

## 🔐 Admin & Test Accounts

### Admin Panel

* URL: [http://localhost:8000/admin/](http://localhost:8000/admin/)
* **Username**: `admin`
* **Password**: `password123`

### Test User (for Postman)

* **Username**: `Test`
* **Password**: `password123`

---

## 📫 Postman Collection

A Postman collection is included in the project directory with all available endpoints and example responses.
