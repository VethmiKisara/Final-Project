<#
Backup and restore helpers using pg_dump / pg_restore.
Usage:
  .\backup_restore.ps1 -Action backup -OutDir .\backups -RetentionDays 30
  .\backup_restore.ps1 -Action restore -BackupFile .\backups\rtmd_2026-01-30.sql.gz
#>
param(
  [Parameter(Mandatory=$true)] [ValidateSet('backup','restore')] [string]$Action,
  [string]$OutDir = '.\backups',
  [string]$BackupFile = '',
  [int]$RetentionDays = 30,
  [string]$DbHost = 'localhost',
  [int]$DbPort = 5432,
  [string]$DbName = 'rtmd',
  [string]$DbUser = 'rtmd_user',
  [string]$DbPassword = 'change_me'
)

$env:PGPASSWORD = $DbPassword

function Do-Backup {
  param($outDir,$dbHost,$dbPort,$dbName,$dbUser)
  if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
  $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $outfile = Join-Path $outDir "rtmd_$timestamp.sql.gz"
  Write-Host "Backing up DB to $outfile"
  pg_dump -h $dbHost -p $dbPort -U $dbUser -F c $dbName | gzip > $outfile
  Write-Host "Backup completed: $outfile"

  # Retention
  Get-ChildItem -Path $outDir -Filter 'rtmd_*.sql.gz' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } | Remove-Item -Force
}

function Do-Restore {
  param($backupFile,$dbHost,$dbPort,$dbName,$dbUser)
  if (-not (Test-Path $backupFile)) { throw "Backup file not found: $backupFile" }
  Write-Host "Restoring DB from $backupFile"
  gunzip -c $backupFile | pg_restore -h $dbHost -p $dbPort -U $dbUser -d $dbName --clean --if-exists
  Write-Host "Restore completed"
}

if ($Action -eq 'backup') { Do-Backup -outDir $OutDir -dbHost $DbHost -dbPort $DbPort -dbName $DbName -dbUser $DbUser }
else { Do-Restore -backupFile $BackupFile -dbHost $DbHost -dbPort $DbPort -dbName $DbName -dbUser $DbUser }
