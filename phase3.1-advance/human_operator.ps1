Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          AI AUTO OPERATOR - ROBOTIC MODE (PS)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Build
Write-Host "[1/6] Building program..." -ForegroundColor Yellow
$mvnResult = Start-Process -FilePath ".\mvnw.cmd" -ArgumentList "clean package -DskipTests -U" -Wait -NoNewWindow -PassThru
if ($mvnResult.ExitCode -ne 0) {
    Write-Error "Build failed with exit code $($mvnResult.ExitCode)"
    exit $mvnResult.ExitCode
}

# 2. Start services
Write-Host "[2/6] Starting services..." -ForegroundColor Yellow
Get-Process -Name java -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process -FilePath "java" -ArgumentList "-jar target\ai-code-helper-0.0.1-SNAPSHOT.jar" -RedirectStandardOutput "backend.log" -RedirectStandardError "backend_err.log"
Write-Host "  - [OK] Backend launched." -ForegroundColor Green

# 3. Wait and Inject
Write-Host "[3/6] Monitoring Engine..." -ForegroundColor Yellow
$portActive = $false
$retry = 0
while (-not $portActive -and $retry -lt 30) {
    $check = netstat -ano | findstr :8081
    if ($check) { 
        $portActive = $true 
    } else {
        Write-Host "Waiting for port 8081 (Attempt $retry/30)..."
        Start-Sleep -s 2
        $retry++
    }
}

if (-not $portActive) {
    Write-Error "Backend failed to start on 8081"
    exit 1
}

Write-Host "[OK] Engine ready. Injecting d5 data..." -ForegroundColor Green
if (-not (Test-Path "outputs")) { New-Item -ItemType Directory -Path "outputs" }
Copy-Item -Path "c:\Users\weiyi\Desktop\student-camp-data\raw\d5\*" -Destination "outputs" -Force

# 4. Monitor Cleaning
Write-Host "[4/6] Monitoring for success (3 files)..." -ForegroundColor Yellow
$success = 0
$timeout = 0
while ($success -lt 3 -and $timeout -lt 24) {
    $success = 0
    if (Test-Path "outputs\cleaned\cleaned_conflict_candidates_raw.txt") { $success++ }
    if (Test-Path "outputs\cleaned\cleaned_memory_events_raw.jsonl") { $success++ }
    if (Test-Path "outputs\cleaned\cleaned_user_memory_snapshots_raw.csv") { $success++ }
    Write-Host "Progress: $success/3..."
    if ($success -lt 3) {
        Start-Sleep -s 10
        $timeout++
    }
}

if ($success -eq 3) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "🏆 TASK ACCOMPLISHED! 100% CLEANED." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Error "Timeout waiting for cleaning results. Check backend.log"
    exit 1
}
