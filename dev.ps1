# Runs the backend (FastAPI via uv/uvicorn) and frontend (Next.js via pnpm) together for local dev.
# Each runs in its own job so Ctrl+C on this script stops both.
#
# ErrorActionPreference stays at its default (Continue): uvicorn/next write routine startup info
# to stderr, and Start-Job surfaces that as the job's error stream. Under "Stop" that would turn
# each such line into a terminating error and kill the polling loop below.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load .env into the current process so child jobs inherit it (uv/pnpm don't read .env themselves).
$envFile = Join-Path $root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $name, $value = $line.Split("=", 2)
            [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
        }
    }
} else {
    Write-Warning ".env not found at $envFile -- copy .env.example first"
}

$port = if ($env:PORT) { $env:PORT } else { "8000" }

$backendJob = Start-Job -Name "s2w-backend" -ScriptBlock {
    param($backendDir, $port)
    Set-Location $backendDir
    uv run uvicorn app.main:app --reload --port $port
} -ArgumentList (Join-Path $root "backend"), $port

$frontendJob = Start-Job -Name "s2w-frontend" -ScriptBlock {
    param($frontendDir)
    Set-Location $frontendDir
    pnpm dev
} -ArgumentList (Join-Path $root "frontend")

Write-Host "Backend running on port $port (job: $($backendJob.Id)), frontend job: $($frontendJob.Id)"
Write-Host "Press Ctrl+C to stop both."

try {
    while ($true) {
        Receive-Job -Job $backendJob, $frontendJob
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
}
