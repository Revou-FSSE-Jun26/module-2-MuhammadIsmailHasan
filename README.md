# Revoshop
Revoshop is a simple e-commerce application built for learning backend development and PostgreSQL.
This project demonstrates basic CRUD operations and database relationships.

## Features

- User Management
- Product Management
- Product Categories
- Orders
- Order Items

## Tech Stack

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Reactjs and Typescript

## Database

This project uses **PostgreSQL** as the database.

### Tables

| Table | Description |
|--------|-------------|
| users | Store user information |
| product_categories | Store product categories |
| products | Store product information |
| orders | Store customer orders |
| order_items | Store products inside an order |

### Diagram Schema
![Diagram Schema](./diagram.png)

## PostgreSQL Installation

### macOS (Homebrew)

1. Install PostgreSQL.

   ```
   brew install postgresql@18
   ```

2. Start the PostgreSQL service.

   ```
   brew services start postgresql@18
   ```

3. Verify the service is running.

   ```
   brew services list
   ```

   Example output:

   ```
    Name          Status  User   File 
    postgresql@18 started ismail ~/Library/LaunchAgents/homebrew.mxcl.postgresql@18.plist
   ```

4. Verify the installation.

   ```
   pgsql --version
   ```

5. Connect to PostgreSQL.

   ```
   psql postgres
   ```

   Example output:

   ```
    psql (18.4 (Homebrew))
    Type "help" for help.

    postgres=# 
   ```


---

### Windows

1. Download PostgreSQL from the [Official Website](https://www.postgresql.org/download/windows/).

2. Run the installer and follow the installation wizard.

3. During installation, configure:
   - **Password** for the `postgres` user
   - **Port:** `5432` (default)

4. After installation, open your terminal and verify the installation with:

   ```
   psql --version
   ```

---