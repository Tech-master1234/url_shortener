# URL Shortener

A simple URL shortener web application built with Flask.

## Features

- Shorten long URLs to a 6-character hash.
- User registration and login.
- Authenticated users can see a list of their shortened URLs.
- Set a usage limit for a shortened URL.
- Protect a shortened URL with a password.
- Delete shortened URLs.

## Technologies Used

- **Backend:** Python, Flask
- **Database:** SQLite
- **Authentication:** Flask-Login
- **Password Hashing:** Werkzeug

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Tech-master1234/url_shortener.git
    ```

2.  **Create a virtual environment and activate it:Windows**
    ```bash
    python -m venv env
    env\Scripts\activate
    ```
    **Linux/Mac**
        ```bash
    python3 -m venv env
    env/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python url_shortener.py
    ```

    The application will be running at `http://0.0.0.0:5000`.

## Database Schema

The application uses a SQLite database with the following schema:

### `users` table

| Column   | Type    | Constraints |
| :------- | :------ | :---------- |
| id       | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT    | NOT NULL UNIQUE |
| password | TEXT    | NOT NULL        |

### `url_mapping` table

| Column      | Type    | Constraints |
| :---------- | :------ | :---------- |
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT |
| long_url    | TEXT    | NOT NULL    |
| short_url   | TEXT    | NOT NULL UNIQUE |
| clicks      | INTEGER | DEFAULT 0   |
| user_id     | INTEGER | FOREIGN KEY (user_id) REFERENCES users (id) |
| usage_limit | INTEGER |             |
| password    | TEXT    |             |