<#
PowerShell helper to create monthly partitions ahead of time using the stored function create_month_partition(parent_table, year, month)
Usage: .\create_month_partitions.ps1 -MonthsAhead 3
#>
param(
  [int]$MonthsAhead = 3,
  [string]$DbHost = 'localhost',
  [int]$DbPort = 5432,
  [string]$DbName = 'rtmd',
  [string]$DbUser = 'rtmd_user',
  [string]$DbPassword = 'change_me'
)

$env:PGPASSWORD = $DbPassword

$start = Get-Date
for ($i = 0; $i -lt $MonthsAhead; $i++) {
    $dt = $start.AddMonths($i)
    $year = $dt.Year
    $month = $dt.Month
    $tables = @('social_posts','disaster_detection','credibility_assessment')

    foreach ($t in $tables) {
        $sql = "SELECT create_month_partition('$t', $year, $month);"
        Write-Host "Creating partition for $t -> $year-$month"
        & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c $sql
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create partition for $t $year-$month" }
    }
}

Write-Host "Partition creation complete."
