# PowerShell script to capture screenshots using Chrome DevTools Protocol
param(
    [int]$Port = 8080,
    [string]$OutputDir = "c:\Users\acer\Local dev ai\.agents\tasks"
)

# Function to capture screenshot
function Capture-Screenshot {
    param([string]$Url, [string]$OutputFile)
    
    # Use chrome --headless with --screenshot flag
    $chromeExe = "chrome.exe"
    $args = @(
        "--headless=new"
        "--disable-gpu"
        "--window-size=1200,800"
        "--screenshot=$OutputFile"
        $Url
    )
    
    Start-Process -FilePath $chromeExe -ArgumentList $args -Wait -NoNewWindow
}

Write-Host "Waiting for application to be ready..."
Start-Sleep -Seconds 3

# Try to capture main view
Write-Host "Capturing Task view..."
Capture-Screenshot -Url "http://localhost:$Port" -OutputFile "$OutputDir\ui-shot-1.png"
Write-Host "Screenshot 1 saved"

Start-Sleep -Seconds 1

# For now, just capture the same page multiple times
# (In a real scenario, we'd navigate via URL params or JS execution)
Capture-Screenshot -Url "http://localhost:$Port" -OutputFile "$OutputDir\ui-shot-2.png"
Write-Host "Screenshot 2 saved"

Capture-Screenshot -Url "http://localhost:$Port" -OutputFile "$OutputDir\ui-shot-3.png"
Write-Host "Screenshot 3 saved"

Write-Host "`nAll screenshots captured!"
