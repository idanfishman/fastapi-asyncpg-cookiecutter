#!/bin/bash

# set bash fail on errors or unset varraibles
set -o errexit
set -o pipefail
set -o nounset

# dependent services health check (postgres)
is_postgres_alive() {
    python << END
import asyncio
import sys

import asyncpg


async def main():
    try:
        conn = await asyncpg.connect(
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            database="${POSTGRES_DB}",
        )
    except OSError:
        sys.exit(-1)


asyncio.run(main())
END
}

until is_postgres_alive; do
    >&2 echo "Waiting for PostgreSQL to become available..."
    sleep 2
done
>&2 echo "PostgreSQL is available"

# run migrations
alembic upgrade head

exec "$@"
