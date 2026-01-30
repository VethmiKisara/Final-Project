# RTMD Database Runbook

This runbook provides step-by-step operational procedures for deploying, operating, backing up, restoring, monitoring, and maintaining the Real-Time Multimodal Disaster Detection (RTMD) PostgreSQL database.

---

## 1. Overview ✅
- Primary DB: PostgreSQL (recommended v13+ or 15).
- Key responsibilities: ingest processed social posts, store credibility results, record detection outputs, record alerts.
- Important artifacts in this repo: `docker-compose.yml`, `migrations/`, `scripts/`, `monitoring/`, `schema.sql`, `README.md`.

---

## 2. Preconditions & Prerequisites ⚙️
- Host: Windows or Linux with Docker (Desktop or Engine) and Git installed for CI.
- Local tooling: PowerShell (Windows) or Bash (Linux), psql CLI optional but recommended.
- Environment variables (or `.env`): DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS.
- Required binaries for ops: `psql`, `pg_dump`, `pg_restore`, `gzip`.

---

## 3. Development Quickstart (local) 🐳
1. Copy `.env.example` -> `.env` and update values.
2. Start DB:
   - Windows: `docker compose up -d` (run from repo root).
3. Wait for DB readiness (use `docker logs rtmd_db` or `docker exec -i rtmd_db pg_isready -U rtmd_user`).
4. Apply migrations (PowerShell):
   - `.\scripts\apply_migrations.ps1 -DbHost localhost -DbName rtmd -DbUser rtmd_user -DbPassword change_me`
   - Or inside container: `docker exec -i rtmd_db psql -U rtmd_user -d rtmd -f /docker-entrypoint-initdb.d/migrations/V1__create_schema.sql`
5. Optionally create month partitions: `.\scripts\create_month_partitions.ps1 -MonthsAhead 3`.
6. Seed demo: `psql -h localhost -U rtmd_user -d rtmd -f migrations/seed_dev_data.sql` or run `python python\connect_and_demo.py`.

---

## 4. Apply Migrations (production-safe) 🔧
- Use Flyway, Liquibase, or your CI pipeline to run migrations.
- Migrations are in `migrations/`. Use transactional, idempotent SQL when possible.
- Run migration in maintenance window where feasible.
- Example (local psql):
  - `PGPASSWORD=change_me psql -h db_host -U rtmd_user -d rtmd -f migrations/V1__create_schema.sql`

---

## 5. Partition Management 📆
- Tables: `social_posts`, `disaster_detection`, `credibility_assessment` are range-partitioned by timestamp.
- Create partitions in advance (monthly) to avoid DDL during high load.
- Use provided helper or `scripts/create_month_partitions.ps1` (Windows) or call the SQL function directly:
  - `SELECT create_month_partition('social_posts', 2026, 02);`
- Automate via scheduled task (Windows Task Scheduler or cron) on 1st of each month.

---

## 6. Backup & Restore 🗄️
### Backup (recommended daily/full + WAL retention)
- Full (custom format, compressed):
  - PowerShell helper: `.\scripts\backup_restore.ps1 -Action backup -OutDir .\backups -RetentionDays 30`
- Or CLI:
  - `PGPASSWORD=change_me pg_dump -h db_host -p 5432 -U rtmd_user -F c rtmd | gzip > backups/rtmd_$(date -u +%Y-%m-%d_%H-%M-%S).sql.gz`

### Restore
- Test restores regularly in a dev environment.
- Use: `.\scripts\backup_restore.ps1 -Action restore -BackupFile .\backups\rtmd_2026-01-30.sql.gz`
- Or CLI:
  - `gunzip -c backup.sql.gz | pg_restore -h db_host -p 5432 -U rtmd_user -d rtmd --clean --if-exists`

### Validation
- After restore, run smoke checks: counts of rows, integrity checks, and sample queries such as `SELECT count(*) FROM social_posts;` and `SELECT * FROM alerts WHERE alert_status='pending' LIMIT 10;`.

---

## 7. Monitoring & Alerts 📈
### Components
- `postgres-exporter` (Prometheus exporter), `prometheus`, `grafana` compose files provided in `monitoring/`.

### Prometheus scrape config
- `monitoring/prometheus.yml` scrapes `postgres-exporter:9187`.

### Example alert rules (Prometheus style)
- High pending alerts rate:
  - alert: HighPendingAlerts
    expr: increase(pg_stat_activity_count[10m]) > 100
    for: 5m
    labels: { severity: "critical" }
    annotations: { summary: "High pending alerts rate" }

- Low insert rate (ingestion pipeline may be down):
  - alert: LowIngestionRate
    expr: rate(rtmd_post_ingest_total[5m]) < 1
    for: 10m
    labels: { severity: "warning" }

- High autovacuum backlog or long-running vacuum:
  - alert: AutovacuumBacklog
    expr: pg_stat_activity_count > 50

> Note: Add or tune rules according to your monitoring metrics and environment.

### Grafana dashboards
- Add dashboards for: ingestion rate, insert latency, table sizes (by partition), pending alerts over time, top disaster types, credibility distribution.

---

## 8. Synthetic Load Testing & Benchmarks ⚡
- Use `python/generate_synthetic.py --count 10000` to load synthetic posts and evaluate ingestion performance.
- Monitor p99 insert latency, WAL growth, and CPU/I/O during tests.
- Use batch inserts (COPY) for higher throughput.

---

## 9. Maintenance & Tuning 🛠️
- Autovacuum: tune `autovacuum_vacuum_scale_factor`, `autovacuum_vacuum_threshold` for insert-heavy tables.
- WAL settings: increase `max_wal_size` and tune `checkpoint_timeout` to reduce checkpoint overhead.
- Index maintenance: schedule `REINDEX` if bloat is high; maintain `pg_stat_all_tables` for bloat monitoring.
- Partition maintenance: drop or archive old partitions beyond retention period (e.g., 6-24 months).
- Analyze: run `VACUUM ANALYZE` on big tables periodically.

---

## 10. Security & Access 🔐
- Use least privilege DB users: separate ingestion, read-only analytics, and admin users.
- Enforce TLS for production DB connections, rotate credentials, and store secrets in a secrets manager (AWS Secrets Manager, Azure Key Vault, or GitHub Secrets for CI).
- Ensure backups are encrypted at rest.

---

## 11. Disaster Recovery & Testing 🚨
- Keep at least one copy of backups offsite.
- Test restore monthly in a staging environment and verify data integrity.
- Document RTO/RPO targets and ensure backup cadence satisfies them.

---

## 12. Troubleshooting Quick Tips 🩺
- DB unreachable: check Docker container logs (`docker logs rtmd_db`) or `psql` connectivity and firewall rules.
- Migration failures: inspect SQL for non-idempotent statements, check order, and run in a test DB first.
- Slow queries: check `pg_stat_statements`, add missing indexes, or rewrite queries to use partitions/time filters.
- Excessive bloat: tune autovacuum and check long-running transactions with `SELECT * FROM pg_stat_activity`.

---

## 13. Operational Playbooks (common recipes)
- Emergency restore: Stop ingestion, restore backup to replica cluster, run smoke tests, switch traffic to restored DB.
- Archiving old data: create a script to COPY partition to archive storage (S3), then DROP partition.

---

## 14. Contacts & Escalation
- On-call DBA or SRE (add your contact list) — replace this line with real contacts (Pager, Slack channel, email).
- For critical incidents (data loss, downtime > 15 mins) escalate to the infrastructure team.

---

## 15. Useful Commands (cheat sheet) 🧾
- Apply migrations locally: `.\scripts\apply_migrations.ps1`
- Create partitions: `.\scripts\create_month_partitions.ps1 -MonthsAhead 3`
- Backup: `.\scripts\backup_restore.ps1 -Action backup -OutDir .\backups -RetentionDays 30`
- Restore: `.\scripts\backup_restore.ps1 -Action restore -BackupFile .\backups\<file>.sql.gz`
- Run demo: `python python\connect_and_demo.py`
- Generate synthetic data: `python python\generate_synthetic.py --count 5000`

---

If you want, I can now:
1. Add scheduled GitHub Actions to run backups nightly and upload artifacts to a secure storage. ✅
2. Add Prometheus alert rule files and example Grafana dashboards to the `monitoring/` folder. 📊
3. Create a ready-to-run Task Scheduler registration script or Kubernetes CronJob for partition creation/backups. 🕒

Which of the above would you like me to implement next? (Reply with the option number.)
