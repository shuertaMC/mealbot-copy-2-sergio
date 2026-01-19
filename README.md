# Mealbot

Mealbot is an automated meal pairing application that helps organizations organize lunch pairings among members. The application intelligently pairs members for meals, considering past pairings and organizational preferences.

This is a Python port of the original Go application, built with FastAPI, SQLAlchemy, and modern Python best practices.

## Features

- Multi-tenant organization management
- Intelligent pairing algorithm that avoids recent repeat pairings
- Scheduled automatic pairing rounds
- Email notifications via Mailgun
- Auth0-based JWT authentication
- RESTful API for managing members, organizations, and rounds

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Poetry (Python dependency management tool)

## Getting Started

### 1. Install Poetry

If you don't have Poetry installed, install it using the official installer:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or via pip:

```bash
pip install poetry
```

For more installation options, see the [official Poetry documentation](https://python-poetry.org/docs/#installation).

### 2. Clone and Setup

Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd mealbot-copy-2-sergio
```

### 3. Install Dependencies

Install all project dependencies using Poetry:

```bash
poetry install
```

This creates a virtual environment and installs all required packages.

### 4. Database Setup

#### Install PostgreSQL

Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/).

#### Create Database

Create a PostgreSQL database for Mealbot:

```bash
createdb mealbot
```

Or using psql:

```sql
CREATE DATABASE mealbot;
```

#### Setup Schema

The database schema will be managed by Alembic migrations (configured in a later milestone). For now, if you have a `schema.sql` file, you can apply it:

```bash
psql -d mealbot -f schema.sql
```

### 5. Configure Environment Variables

Copy the example environment file and edit it with your configuration:

```bash
cp .env.example .env
```

Edit `.env` and set the required values:

- `DATABASE_URL`: Your PostgreSQL connection string
- `MAILGUN_DOMAIN`: Your Mailgun domain
- `MAILGUN_API_KEY`: Your Mailgun API key
- Other settings as needed

**Important:** Never commit the `.env` file to version control. It is already included in `.gitignore`.

### 6. Run the Application

#### Development Mode

Run the application with auto-reload enabled:

```bash
poetry run uvicorn app.main:app --reload --port 8080
```

The API will be available at `http://localhost:8080`.

#### Production Mode

For production deployment (e.g., on Heroku), the `Procfile` is configured to run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

### 7. Verify Installation

Once the application is running, you can verify it's working by accessing:

- API documentation (Swagger UI): `http://localhost:8080/docs`
- Alternative API documentation (ReDoc): `http://localhost:8080/redoc`

## Development

### Code Formatting

Format code with Black:

```bash
poetry run black app/ tests/
```

### Linting

Lint code with Ruff:

```bash
poetry run ruff check app/ tests/
```

### Running Tests

Run tests with pytest:

```bash
poetry run pytest
```

Run tests with coverage:

```bash
poetry run pytest --cov=app --cov-report=html
```

### Database Migrations

Alembic is used for database migrations (will be configured in a later milestone):

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## Project Structure

```
mealbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and ASGI entrypoint
│   ├── config.py            # Pydantic settings
│   ├── database.py          # SQLAlchemy engine/session setup
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routers
│   ├── services/            # Business logic
│   └── middleware/          # Authentication and CORS
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── static/                  # Static files
├── alembic/                 # Database migrations
├── pyproject.toml           # Poetry configuration
├── .env.example             # Example environment variables
└── README.md
```

## Deployment

### Heroku

The application is configured for Heroku deployment via the `Procfile`.

1. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```

2. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. Set environment variables:
   ```bash
   heroku config:set MAILGUN_DOMAIN=your-domain
   heroku config:set MAILGUN_API_KEY=your-key
   # ... other variables
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

5. Run migrations:
   ```bash
   heroku run alembic upgrade head
   ```

## API Documentation

Once the application is running, interactive API documentation is available at:

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This project is a modernization of the original Go application. For contribution guidelines and development practices, please refer to the project documentation.
