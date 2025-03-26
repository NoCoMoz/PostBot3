# Script to download CSV backups from the droplet
param(
    [switch]$Latest,
    [switch]$All,
    [string]$Date
)

$dropletHost = "64.23.176.81"
$dropletUser = "root"
$backupPath = "/root/voices-ignited-bot/local_backups"
$localBackupDir = Join-Path $PSScriptRoot "downloaded_backups"

# Create local backup directory if it doesn't exist
if (-not (Test-Path $localBackupDir)) {
    New-Item -ItemType Directory -Path $localBackupDir | Out-Null
    Write-Host "Created local backup directory: $localBackupDir"
}

# Function to download files using SCP
function Download-File {
    param($remotePath, $localPath)
    $scpCommand = "scp ${dropletUser}@${dropletHost}:`"$remotePath`" `"$localPath`""
    Write-Host "Downloading: $remotePath"
    Invoke-Expression $scpCommand
}

if ($Latest) {
    # Download only the latest_responses.csv
    $localPath = Join-Path $localBackupDir "latest_responses.csv"
    Download-File "$backupPath/latest_responses.csv" $localPath
    Write-Host "Latest responses downloaded to: $localPath"
}
elseif ($All) {
    # Download all backup files
    $tempFile = New-TemporaryFile
    $listCommand = "ssh ${dropletUser}@${dropletHost} `"ls -1 $backupPath`""
    Invoke-Expression $listCommand | Out-File $tempFile
    
    Get-Content $tempFile | ForEach-Object {
        $fileName = $_.Trim()
        if ($fileName) {
            $localPath = Join-Path $localBackupDir $fileName
            Download-File "$backupPath/$fileName" $localPath
        }
    }
    Remove-Item $tempFile
    Write-Host "All backups downloaded to: $localBackupDir"
}
elseif ($Date) {
    # Download backups from specific date (format: YYYYMMDD)
    $tempFile = New-TemporaryFile
    $listCommand = "ssh ${dropletUser}@${dropletHost} `"ls -1 $backupPath/responses_${Date}*.csv`""
    Invoke-Expression $listCommand | Out-File $tempFile
    
    $found = $false
    Get-Content $tempFile | ForEach-Object {
        $fileName = $_.Trim()
        if ($fileName) {
            $found = $true
            $localPath = Join-Path $localBackupDir $fileName
            Download-File "$backupPath/$fileName" $localPath
        }
    }
    Remove-Item $tempFile
    
    if (-not $found) {
        Write-Host "No backups found for date: $Date"
    }
    else {
        Write-Host "Backups for $Date downloaded to: $localBackupDir"
    }
}
else {
    Write-Host "Please specify one of the following options:"
    Write-Host "-Latest : Download only the latest responses"
    Write-Host "-All    : Download all backup files"
    Write-Host "-Date   : Download backups from a specific date (format: YYYYMMDD)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host ".\download_backups.ps1 -Latest"
    Write-Host ".\download_backups.ps1 -All"
    Write-Host ".\download_backups.ps1 -Date 20250214"
}
