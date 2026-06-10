@echo off
REM NITRO STARTUP (Target < 500ms)
cd /d "%~dp0"

REM 1. Instant Browser Launch
start http://localhost:3000

REM 2. Parallel Background Process Kill (Fast Image Name Kill)
taskkill /F /IM java.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

REM 3. Fire-and-Forget Services
start /B java -jar target\ai-code-helper-0.0.1-SNAPSHOT.jar > backend.log 2>&1
cd ai-code-helper-frontend && start /B npm run dev > ..\frontend.log 2>&1

exit
