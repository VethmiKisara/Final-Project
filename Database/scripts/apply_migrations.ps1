<#
Apply all SQL files in ./migrations in alphabetical order using psql.
Usage: .\apply_migrations.ps1 -DbHost localhost -DbName rtmd -DbUser rtmd_user
#>
param(
  [string]$DbHost = 'localhost',
  [int]$DbPort = 5432,
  [string]$DbName = 'rtmd',
  [string]$DbUser = 'rtmd_user',
  [string]$DbPassword = 'change_me'
)

$env:PGPASSWORD = $DbPassword

$migDir = Join-Path -Path $PSScriptRoot -ChildPath '..\migrations'
$migDir = Resolve-Path $migDir
$files = Get-ChildItem -Path $migDir -Filter '*.sql' | Sort-Object Name

foreach ($f in $files) {
    Write-Host "Applying migration: $($f.Name)"
    & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $f.FullName
    if ($LASTEXITCODE -ne 0) { throw "Migration failed: $($f.Name)" }
}

Write-Host "All migrations applied."