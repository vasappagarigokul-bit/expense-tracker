<p align="center">
  <img src="https://github.com/vasappagarigokul-bit/readme-images/blob/main/expense-tracker/b1d1906722b334d8674254682068c0b9_fgraphic1.png">
</p>

The Expense Tracker is a backend application designed to help users securely manage, track, and analyze their personal financial expenses. It provides a complete system for account management, expense recording, analytics, and account recovery, built with a focus on structured data handling and API-driven interactions.
<br>
<br>
Users can create an account using their email, password, and mobile number. The system ensures strong password policies and validates email and phone number formats before registration. Once registered, users can log in to receive an access token for authenticated interactions and a refresh token for maintaining sessions securely.
<br>
<br>
After authentication, users can create, view, update, and delete their expenses. Each expense includes a title and a monetary amount, allowing users to organize and track their spending efficiently. The system also caches expense data to improve performance and reduce repeated database queries.
<br>
<br>
The application provides analytical insights into user spending. Users can specify a date range to retrieve aggregated data such as total spending, average expense, minimum and maximum expenses, and the total number of transactions. Additionally, item-level analytics allow users to analyze spending patterns for individual expense titles.
<br>
<br>
For account management, users can update their email, password, and mobile number. Security measures such as password verification and rate limiting are applied to sensitive operations to prevent abuse and unauthorized access.
<br>
<br>
The system also includes an account recovery mechanism. If a user forgets their password, they can request a one-time password (OTP) sent to their registered mobile number. After verifying the OTP, the user can reset their password securely. OTPs are time-bound and stored temporarily to ensure safety.
<br>
<br>
Administrative health-check endpoints are provided to monitor the status of the database, cache systems, rate limiter, OTP storage, and messaging service. These endpoints help ensure that all system components are functioning correctly.
<br>
<br>
Overall, the Expense Tracker is a RESTful API-based backend system that combines authentication, data management, caching, rate limiting, and external messaging integration to deliver a structured and scalable expense management solution.

# Local Setup
## Prerequisites
- Python 3.9+
- MySQL database
- Dockerized Redis
- Twilio Messaging Account

## Clone the Repository
git clone https://github.com/vasappagarigokul-bit/expense-tracker
<br>
cd expense-tracker

## Create a Virtual Environment
python -m venv venv
- __Linux / Mac__: venv/bin/activate
- __Windows__: venv\Scripts\activate

## Install Dependencies
pip install -r requirements.txt

## Environment Configuration
Create a `.env` file in the root directory:
- __DATABASE_URL__=mysql+pymysql://[user]:[password]@localhost:3306/<db_name>
- __SECRET_KEY__=<secret_key>
- __REDIS_CACHE_URL__=redis://localhost:6379/<db_number_0-15>
- __REDIS_RATE_LIMITER_URL__=redis://localhost:6379/<db_number_0-15>
- __REDIS_OTP_STORAGE_URL__=redis://localhost:6379/<db_number_0-15>
- __TWILIO_ACCOUNT_SID__=<twilio_account_sid>
- __TWILIO_AUTH_TOKEN__=<twilio_auth_token>
- __TWILIO_PHONE__=<twilio_phone>
- __ADMIN__=[username]
- __PASSWORD__=<admin_password>
- __PHONE_NUMBER__=+[COUNTRY CODE][MOBILE NUMBER]

__Note 1__: Remove `SSL/CA` certificate arguments from the `create_engine` call in `database.py` file.
<br>
__Note 2__: Set `secure=False` within the `response.delete_cookie` call in `crud.py` file and `response.set_cookie` call in `main.py` file to allow the browser to process cookies over a HTTP connection.

## Run the application
uvicorn app.main:app --reload
<br>
<br>
API will be available at: `http://localhost:8000`
<br>
Access the interactive Swagger documentation at: `http://localhost:8000/docs`
