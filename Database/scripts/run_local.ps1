<#
Run local end-to-end: start docker-compose, wait for DB, apply migrations, create partitions, seed sample data.
Usage: .\run_local.ps1
#>
Write-Host "Running local setup..."

# 1) Try to start Docker Compose
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Starting docker compose..."
    docker compose up -d
    Start-Sleep -Seconds 5
} else {
    Write-Warning "Docker not found on host. Please install Docker Desktop or run migrations against a remote DB."
}

# 2) Wait for DB to be ready (attempt via docker exec if container exists)
$tries = 0
while ($tries -lt 30) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $status = docker exec -i rtmd_db pg_isready -U rtmd_user 2>$null
        if ($LASTEXITCODE -eq 0) { break }
    } else {
        # Try host psql if available
        if (Get-Command psql -ErrorAction SilentlyContinue) {
            psql -h localhost -U rtmd_user -d rtmd -c '\q' 2>$null
            if ($LASTEXITCODE -eq 0) { break }
        }
    }
    Start-Sleep -Seconds 2
    $tries++
}

if ($tries -ge 30) { Write-Error "Database did not become available. Check Docker or connection settings."; exit 1 }

# 3) Apply migrations (inside container if possible)
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Applying migrations inside container..."
    # copy migrations into container path and execute via psql
    docker exec -i rtmd_db psql -U rtmd_user -d rtmd -f /docker-entrypoint-initdb.d/migrations/V1__create_schema.sql
} elseif (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "Applying migrations using local psql..."
    .\scripts\apply_migrations.ps1
} else { Write-Warning "Unable to apply migrations automatically (no Docker and no psql)." }

# 4) Create partitions and seed demo
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker exec -i rtmd_db psql -U rtmd_user -d rtmd -c "SELECT create_month_partition('social_posts', $(Get-Date).Year, $(Get-Date).Month);"
}
.
Write-Host "Local setup finished. Run scripts\apply_migrations.ps1 or python\connect_and_demo.py as needed."