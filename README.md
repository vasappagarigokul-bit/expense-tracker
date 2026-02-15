# Expense Tracker Full-Stack Application

This is a full-stack Expense Tracker application built with __React (Vite)__ on the frontend and __FastAPI__ on the backend.
<br>
<br>
The system allows users to __register__, __login__, __add expenses__, __and view their expense list__, leveraging __MySQL__ for persistent storage and __Redis__ for caching to improve performance. JWT-based authentication ensures secure access for each user.

## Tech Stack

- __Frontend__: React, Vite, JavaScript
- __Backend__: Python, FastAPI, Uvicorn
- __Database__: MySQL
- __Cache__: Redis
- __Authentication__: JWT
- __ORM__: SQLAlchemy
- __Environent__: Python dotenv

## How It Works

### User Flow

1. __Registration/Login__

- Users register with an email and password
- Passwords are securely hshed using bcrypt
- On login, a JWT token is returned

2. __Adding Expenses__

- Users can add expenses with a title and amount
- Expenses are stored in __MySQL__ for persistence
- Redis cache is cleared for that user to ensure updated data

3. __Viewing Expenses__

- The app first checks __Redis cache__ for expenses.
- If not found, it fetches data from __MySQL__ and caches it.
- This reduces database load and improves response time.

## Setup Instructions

### 1. Clone the Repository
git https://github.com/vasappagarigokul-bit/expense-tracker
<br>
cd expense-tracker

### 2. Backend Setup
cd backend
<br>
python -m venv venv
<br>
<br>
__Windows__:
<br>
venv\Scripts\activate
<br>
<br>
__Mac/Linux__
<br>
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Configure environment variables
Create a __.env__ file:
<br>
<br>
DATABASE_URL=mysql+pymysql://root:password@localhost/expense_tracker
<br>
SECRET_KEY=your_super_secret_key
<br>
ALGORITHM=HS256
<br>
REDIS_HOST=localhost
<br>
REDIS_PORT=6379

### 5. Run Redis using Docker
docker run -d -p 6379:6379 --name redis redis

### 6. Start Backend
uvicorn main:app --reload
<br>
<br>
Open in browser:
<br>
http://127.0.0.1:8000/docs

### 7. Frontend Setup
cd frontend
<br>
npm install
<br>
npm run dev
<br>
<br>
Open in browser:
<br>
http://localhost:5173

## API Endpoints

__POST__ /register
<br>
Register a new user.
<br>
<br>
__POST__ /login
<br>
Login and recieve JWT token.
<br>
<br>
__POST__ /expenses
<br>
Add a new expense (JWT required)
<br>
<br>
__GET__ /expenses
<br>
List user expenses (JWT required)
<br>
<br>
__Authorization Header__
<br>
Authorization: Bearer <JWT_TOKEN>

## Project Structure

expense-tracker/
<br>
|
<br>
|- backend/
<br>
| &nbsp;&nbsp;|- main.py
<br>
| &nbsp;&nbsp;|- database.py
<br>
| &nbsp;&nbsp;|- models.py
<br>
| &nbsp;&nbsp;|- schemas.py
<br>
| &nbsp;&nbsp;|- auth.py
<br>
| &nbsp;&nbsp;|- .env
<br>
|
<br>
|- frontend/
<br>
| &nbsp;&nbsp;|- index.html
<br>
| &nbsp;&nbsp;|- package.json
<br>
| &nbsp;&nbsp;|- src/
<br>
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|- main.jsx
<br>
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|- App.jsx
<br>
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|- api.js
<br>
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|- Login.jsx
<br>
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|_ Dashboard.jsx
<br>
|
<br>
|_ README.md

## Features

- User registration and login with secure password hashing
- JWT authentication for protected routes
- Add, view, and list expenses per user
- Redis caching for faster expense retrieval
- Responsive React frontend
- Clean separation of backend and frontend
