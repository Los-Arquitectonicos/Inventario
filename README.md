# Inventario

A Django web application for inventory management with PostgreSQL database support.

## Features

- Django 5.2.6 framework
- PostgreSQL database integration
- Environment-based configuration
- Ready-to-deploy structure

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Inventario
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your database credentials:
   ```
   DB_NAME=inventario_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Create PostgreSQL database:**
   ```sql
   CREATE DATABASE inventario_db;
   CREATE USER inventario_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE inventario_db TO inventario_user;
   ```

6. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000`

## Configuration

### Database Settings

The application uses PostgreSQL as the default database. Configuration is handled through environment variables:

- `DB_NAME`: Database name (default: inventario_db)
- `DB_USER`: Database user (default: inventario_user)
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)

### Security Settings

- `SECRET_KEY`: Django secret key for security
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Project Structure

```
inventario/
├── inventario/         # Main Django project directory
│   ├── __init__.py
│   ├── asgi.py        # ASGI configuration
│   ├── settings.py    # Django settings with PostgreSQL config
│   ├── urls.py        # URL configuration
│   └── wsgi.py        # WSGI configuration
├── manage.py          # Django management script
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── .gitignore        # Git ignore rules
└── README.md         # This file
```

## Development

### Running Tests

```bash
python manage.py test
```

### Checking Code Quality

```bash
python manage.py check
```

### Database Operations

```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Django shell
python manage.py shell
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Configure proper `SECRET_KEY` and `ALLOWED_HOSTS`
3. Use a production-grade WSGI server like Gunicorn
4. Configure static files serving
5. Set up proper PostgreSQL security

## License

[Add your license information here]