# Script to set up daily backup task
$taskName = "VoicesIgnitedBackup"
$scriptPath = Join-Path $PSScriptRoot "download_backups.ps1"
$workingDir = $PSScriptRoot

# Create the action to run the backup script
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -Latest" `
    -WorkingDirectory $workingDir

# Create trigger for daily run at 3 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 3AM

# Get current user for task principal
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Create the task settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

try {
    # Register the task
    Register-ScheduledTask -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -User $currentUser `
        -RunLevel Highest `
        -Force

    Write-Host "Successfully created scheduled task '$taskName'"
    Write-Host "The task will run daily at 3 AM to download the latest survey responses"
    Write-Host "Downloads will be saved to: $workingDir\downloaded_backups"
}
catch {
    Write-Host "Error creating scheduled task: $_"
    exit 1
}

# Create a log directory if it doesn't exist
$logDir = Join-Path $workingDir "backup_logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
    Write-Host "Created log directory: $logDir"
}
