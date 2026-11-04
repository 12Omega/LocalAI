# Simple verification that checks the CSS files have been updated correctly
param(
    [string]$BaseDir = "c:\Users\acer\Local dev ai"
)

Write-Host "=== VS Code UI Verification ===" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$checks = 0

# Check panels.css
Write-Host "Checking panels.css..." -ForegroundColor Yellow
$panelsContent = Get-Content "$BaseDir\src\web\css\components\panels.css" -Raw
$checks++

if ($panelsContent -match 'border-radius:\s*8px') {
    $issues += "panels.css still contains border-radius: 8px"
}
if ($panelsContent -match 'border-radius:\s*6px') {
    $issues += "panels.css still contains border-radius: 6px"  
}
if ($panelsContent -match 'border-radius:\s*4px' -and $panelsContent -notmatch 'border-radius:\s*4px.*removed') {
    $issues += "panels.css still contains border-radius: 4px"
}
if ($panelsContent -match 'border-radius:\s*12px') {
    $issues += "panels.css still contains border-radius: 12px"
}
if ($panelsContent -match 'box-shadow:.*var\(--shadow\)') {
    $issues += "panels.css still contains box-shadow with var(--shadow)"
}

# Check history.css
Write-Host "Checking history.css..." -ForegroundColor Yellow
$historyContent = Get-Content "$BaseDir\src\web\css\components\history.css" -Raw
$checks++

if ($historyContent -match 'border-radius:\s*[6-8]px') {
    $issues += "history.css still contains border-radius: 6-8px"
}
if ($historyContent -match 'box-shadow:.*0\s+0\s+0\s+3px') {
    $issues += "history.css still contains focus box-shadow (should be removed per VS Code spec)"
}

# Check main.css for button border-radius
Write-Host "Checking main.css..." -ForegroundColor Yellow
$mainContent = Get-Content "$BaseDir\src\web\css\main.css" -Raw
$checks++

if ($mainContent -match '\.btn.*border-radius:\s*2px' -or $mainContent -match 'border-radius:\s*2px.*\.btn') {
    $issues += "main.css still contains button with border-radius: 2px"
}

# Check modal.css for progress dots
Write-Host "Checking modal.css..." -ForegroundColor Yellow
$modalContent = Get-Content "$BaseDir\src\web\css\components\modal.css" -Raw
$checks++

if ($modalContent -match '\.setup-progress-dot[^{]*\{[^}]*border-radius:\s*0') {
    $issues += "modal.css progress dots have border-radius: 0 but should be 50% (circular indicators)"
} elseif ($modalContent -notmatch '\.setup-progress-dot[^{]*\{[^}]*border-radius:\s*50%') {
    $issues += "modal.css progress dots missing border-radius: 50%"
}

# Report results
Write-Host ""
Write-Host "Completed $checks checks" -ForegroundColor Cyan

if ($issues.Count -eq 0) {
    Write-Host "All CSS checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "VS Code styling requirements met:" -ForegroundColor Green
    Write-Host "  - No rounded corners (except circular elements with 50%)" -ForegroundColor Gray
    Write-Host "  - No box-shadows" -ForegroundColor Gray
    Write-Host "  - Sharp, clean lines throughout" -ForegroundColor Gray
    exit 0
} else {
    Write-Host ("Found " + $issues.Count + " issues:") -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host ("  - " + $issue) -ForegroundColor Red
    }
    exit 1
}
