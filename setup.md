# Setup Instructions (Rough)

## Create Python Virtual Environment at Custom Location

To create a virtual environment named `smart_queue` at `/opt/grv` using mkvirtualenv:

```bash
# export WORKON_HOME=/opt/grv
mkvirtualenv smart_queue
```

To activate the environment:

```bash
workon smart_queue
```

To install dependencies:

```bash
pip install -r /home/vast/repos/smart_tasks_queue/requirements.txt
```

## Database Setup (PostgreSQL)

- The database connection for migrations and the app is configured using environment variables in `alembic.ini`:

```
# Example usage:
export DB_USER=vast
export DB_PASSWORD=yourpassword
export DB_NAME=your_db_name
export DB_HOST=localhost
export DB_PORT=5432
```

- Before running Alembic migrations, make sure to export these variables in your shell.
- The connection string in `alembic.ini` is:
  ```
  sqlalchemy.url = postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
  ```
- Ensure the PostgreSQL user and database exist before running migrations.

- Alembic migrations are initialized inside the `app/migrations` folder. To set up migrations for the first time, run:
  ```bash
  cd app
  workon smart_queue
  alembic init migrations
  ```
  All subsequent migration commands should be run from the `app` directory, and migration scripts will be created in `app/migrations/versions`.

- Example commands to generate and apply migrations:
  ```bash
  alembic revision --autogenerate -m "initial migration"
  alembic upgrade head
  ```

- Make sure your environment variables are set and the database is created before running these commands.

## Applying Migrations

To apply existing migrations to your database, run the following commands from the `app` directory:

```bash
cd app
workon smart_queue
alembic upgrade head
```

Make sure your environment variables are set and the database is created before running these commands.


