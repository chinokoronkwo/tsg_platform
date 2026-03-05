# WordPress to PostgreSQL Migration Scripts

Migrate data from WordPress MySQL (table prefix `agh_`) to the Snob Group PostgreSQL schema.

## Prerequisites

```bash
pip install -r scripts/requirements.txt
```

## Environment Variables

- `SOURCE_MYSQL_URL` - MySQL connection string (e.g. `mysql://user:pass@host:3306/dbname`)
- `DATABASE_URL` - PostgreSQL connection string (e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`)

## Usage

From the `backend/` directory:

```bash
# Run all migrations in order
python scripts/migrate_data.py

# Re-run all migrations (ignore completion tracking)
python scripts/migrate_data.py --force

# Run individual migrations
python scripts/migrate_users.py
python scripts/migrate_products.py
python scripts/migrate_orders.py
# etc.
```

## Migration Order

1. **users** - Roles, users, social accounts
2. **products** - Categories, products, product media
3. **orders** - Orders, order items
4. **subscriptions** - Subscriptions, membership plans, memberships
5. **wallet** - Wallet accounts, transactions
6. **media** - Media library, download list
7. **bookings** - (stub)
8. **redirects** - URL redirect mapping

## Output Files

- `media_download_list.json` - Source URLs for batch media download
- `media_url_mapping.json` - Old WP URL → new S3/R2 URL mapping

## Schema Note

The User model includes `must_reset_password` for migrated users (WordPress hashes). Run Alembic migrations to add this column if not present.
