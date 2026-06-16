# setup_github.ps1
# Publishes agent-linkedin-candidate to GitHub using conventional commits
# Usage: .\setup_github.ps1 -Token "ghp_YOUR_TOKEN_HERE"
# Get token at: https://github.com/settings/tokens/new  (scope: repo)

param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

$ErrorActionPreference = "Stop"
$RepoDir = "C:\Dev\agent-linkedin-candidate"
$RepoName = "agent-linkedin-candidate"
$GitHubUser = "silveiraSoft"
$RepoDesc = "Autonomous LinkedIn job application agent - AI-era resume personalization, Easy Apply automation, retry logic, preflight checks, weekly email digest"

Write-Host "=== Agent LinkedIn Candidate - GitHub Setup ===" -ForegroundColor Cyan
Set-Location $RepoDir

# Step 1: Re-initialize clean git repo
Write-Host "[1/5] Initializing git repository..." -ForegroundColor Yellow
if (Test-Path ".git") { Remove-Item -Recurse -Force ".git" }
git init -b main
git config user.email "adalbertosn1982@gmail.com"
git config user.name "Adalberto Silveira"

# Step 2: .gitignore
Write-Host "[2/5] Writing .gitignore..." -ForegroundColor Yellow
$gitignoreContent = @"
# Generated resumes (personal data)
resume-personalized/*.docx

# Dynamic inputs (generated per-run)
jobs_input.json

# Logs (except run_history.json which we keep)
logs/*.log
logs/*.log.*

# Python
__pycache__/
*.pyc
*.pyo
.env
*.env
*.egg-info/
dist/
build/
.venv/
venv/

# OS
Thumbs.db
desktop.ini
"@
$gitignoreContent | Out-File -Encoding UTF8 .gitignore

# Step 3: Conventional commits
Write-Host "[3/5] Creating conventional commits..." -ForegroundColor Yellow

# commit 1 - project scaffold
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Force logs | Out-Null }
if (-not (Test-Path "logs\.gitkeep")) { New-Item -ItemType File "logs\.gitkeep" | Out-Null }
git add .gitignore
if (Test-Path "README.md") { git add README.md }
if (Test-Path "README-ADALBERTO.txt") { git add "README-ADALBERTO.txt" }
if (Test-Path "setup_github.ps1") { git add setup_github.ps1 }
git add "logs\.gitkeep"
git commit -m "chore: initial project structure, .gitignore, and setup scripts"

# commit 2 - core modules
$modules = @("agent_logger.py", "ats_updater.py", "ats_techniques_cache.json")
foreach ($f in $modules) { if (Test-Path $f) { git add $f } }
git commit -m "feat(modules): add agent_logger, ats_updater, ATS techniques cache"

# commit 3 - docs & operation guides
$docs = @("AGENT_TASK_PROMPT.md", "INSTRUCCIONES_OPERACION.md")
foreach ($f in $docs) { if (Test-Path $f) { git add $f } }
git commit -m "docs: agent task prompt (4-phase + preflight) and operation guide"

# commit 4 - main agent v3
git add linkedin_agent.py
if (Test-Path "applications_log.json") { git add applications_log.json }
if (Test-Path "logs\run_history.json") { git add "logs\run_history.json" }
if (Test-Path "SilveiraNapoles-Adalberto-Resume-2026-ATS.docx") { git add "SilveiraNapoles-Adalberto-Resume-2026-ATS.docx" }
if (Test-Path "SilveiraNapoles-Adalberto-Resume-2026-General-ATS.docx") { git add "SilveiraNapoles-Adalberto-Resume-2026-General-ATS.docx" }
git commit -m "feat(agent): linkedin_agent.py v3 - autonomous pipeline with retry logic, preflight, error visibility, AI-era resume personalization (Amazon Bedrock + Claude API)"

Write-Host "Commits created:" -ForegroundColor Green
git log --oneline

# Step 4: Create GitHub repository
Write-Host "[4/5] Creating GitHub repository..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "token $Token"
    "Accept"        = "application/vnd.github.v3+json"
    "Content-Type"  = "application/json"
}
$bodyObj = @{
    "name"        = $RepoName
    "description" = $RepoDesc
    "private"     = $false
    "auto_init"   = $false
}
$body = $bodyObj | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body
    Write-Host "Repository created: $($response.html_url)" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 422) {
        Write-Host "Repository already exists - continuing to push." -ForegroundColor Yellow
    } else {
        Write-Host "Error creating repo: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Step 5: Push
Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
$RemoteUrl = "https://$Token@github.com/$GitHubUser/$RepoName.git"
$existingRemotes = & git remote 2>$null
if ($existingRemotes -contains "origin") {
    git remote set-url origin $RemoteUrl
} else {
    git remote add origin $RemoteUrl
}
git push -u origin main --force

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Repository: https://github.com/$GitHubUser/$RepoName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Remove token from remote URL after push:" -ForegroundColor Yellow
Write-Host "  git remote set-url origin https://github.com/$GitHubUser/$RepoName.git"
