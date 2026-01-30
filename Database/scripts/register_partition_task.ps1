<#
Register a scheduled task to run partition creation monthly using create_month_partitions.ps1
Usage: .\register_partition_task.ps1 -MonthsAhead 3
#>
param(
  [int]$MonthsAhead = 3,
  [string]$TaskName = 'RTMD_CreateMonthPartitions',
  [string]$ScriptPath = '$PSScriptRoot\\..\\scripts\\create_month_partitions.ps1'
)

$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`" -MonthsAhead $MonthsAhead"
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 3:00AM
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest

# Register or update
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal
Write-Host "Scheduled task registered: $TaskName (runs on 1st of month at 03:00)"
