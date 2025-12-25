# Database Persistence Guide

This guide explains how to ensure your Secret Santa database persists across container restarts and updates.

## Current Setup

The application uses SQLite database stored at `/app/data/santa.db` inside the container.

## Docker Volume Configuration

### Option 1: Named Volume (Recommended for Docker)

The `docker-compose.yml` already includes a named volume:

```yaml
volumes:
  - santa_data:/app/data
```

This creates a Docker-managed volume that persists even if you remove the container.

**Benefits:**
- ✅ Managed by Docker
- ✅ Survives container removal
- ✅ Easy to backup
- ✅ Works across Docker hosts

**To use:**
```bash
docker-compose up -d
```

**To backup:**
```bash
# Create backup
docker run --rm -v secret_santa_santa_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/santa-db-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore from backup
docker run --rm -v secret_santa_santa_data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/santa-db-backup-YYYYMMDD.tar.gz"
```

### Option 2: Bind Mount (Recommended for Development)

Mount a local directory directly:

```yaml
volumes:
  - ./data:/app/data  # Local directory
```

**Benefits:**
- ✅ Easy access to database files
- ✅ Can edit/view database directly
- ✅ Easy to backup (just copy the directory)

**To use, modify docker-compose.yml:**
```yaml
volumes:
  - ./data:/app/data  # Change this line
```

**Note:** Make sure the `data/` directory exists:
```bash
mkdir -p data
chmod 755 data
```

### Option 3: External Volume (Recommended for Production)

Create a named volume explicitly:

```bash
# Create volume
docker volume create secret_santa_data

# Use in docker-compose.yml
volumes:
  - secret_santa_data:/app/data

volumes:
  secret_santa_data:
    external: true
```

## Verification

**Check if volume is working:**
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect secret_santa_santa_data

# Check volume contents
docker run --rm -v secret_santa_santa_data:/data alpine ls -la /data
```

**Test persistence:**
1. Start container and create some data
2. Stop container: `docker-compose down`
3. Start again: `docker-compose up -d`
4. Verify data is still there

## Backup Strategies

### Automated Backup Script

Create `backup-db.sh`:
```bash
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

docker run --rm \
  -v secret_santa_santa_data:/data \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine tar czf /backup/santa-db-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

echo "Backup created in $BACKUP_DIR"
```

### Cron Job for Regular Backups

Add to crontab:
```bash
# Backup every day at 2 AM
0 2 * * * /path/to/backup-db.sh
```

## Migration to External Database (Optional)

For production, consider migrating to PostgreSQL or MySQL:

### PostgreSQL Example

**docker-compose.yml:**
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: secretsanta
      POSTGRES_USER: santa
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    environment:
      DATABASE_URL: postgresql+asyncpg://santa:your_password@db/secretsanta

volumes:
  postgres_data:
```

**Update app/core/config.py:**
```python
database_url: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/santa.db"
)
```

## Troubleshooting

### Database not persisting?

1. **Check volume mount:**
   ```bash
   docker inspect secret_santa_web | grep -A 10 Mounts
   ```

2. **Verify volume exists:**
   ```bash
   docker volume ls | grep santa
   ```

3. **Check permissions:**
   ```bash
   docker exec secret_santa_web ls -la /app/data
   ```

### Permission Issues

If you see permission errors:
```bash
# Fix ownership
docker exec secret_santa_web chown -R $(id -u):$(id -g) /app/data

# Or run container with your user ID
# Add to docker-compose.yml:
user: "${UID}:${GID}"
```

## Current Configuration

Your current `docker-compose.yml` uses:
- **Named volume:** `santa_data:/app/data`
- **Database path:** `sqlite+aiosqlite:///./data/santa.db`

This means:
- ✅ Database persists in Docker volume
- ✅ Survives container restarts
- ✅ Survives container removal (unless you use `docker-compose down -v`)

## Important Notes

⚠️ **Never use `docker-compose down -v`** - This removes volumes and deletes your database!

⚠️ **Always backup before updates** - Create a backup before pulling new images

✅ **Use named volumes for production** - More reliable than bind mounts

✅ **Test backups regularly** - Ensure you can restore from backups

