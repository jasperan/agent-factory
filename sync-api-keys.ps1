# Sync API Keys from .env to GitHub Secrets
# Usage: .\sync-api-keys.ps1

param(
    [switch]$Test = $false  # Set to $true to test @claude after sync
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "API Key Sync to GitHub Secrets" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found in current directory" -ForegroundColor Red
    exit 1
}
Write-Host "  + Found .env file" -ForegroundColor Green

# Check if gh CLI is installed
try {
    $null = gh --version
    Write-Host "  + GitHub CLI (gh) is installed" -ForegroundColor Green
} catch {
    Write-Host "ERROR: GitHub CLI (gh) not found. Install from: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# Check if authenticated
try {
    $ghStatus = gh auth status 2>&1 | Out-String
    if ($ghStatus -notmatch "Logged in") {
        Write-Host "ERROR: Not logged in to GitHub CLI. Run: gh auth login" -ForegroundColor Red
        exit 1
    }
    Write-Host "  + GitHub CLI is authenticated" -ForegroundColor Green
} catch {
    Write-Host "ERROR: GitHub authentication check failed. Run: gh auth login" -ForegroundColor Red
    exit 1
}

# Step 2: Read .env and extract ANTHROPIC_API_KEY
Write-Host ""
Write-Host "[2/6] Reading .env file..." -ForegroundColor Yellow

$envContent = Get-Content ".env" -Raw
$apiKeyMatch = [regex]::Match($envContent, 'ANTHROPIC_API_KEY=([^\r\n]+)')

if (-not $apiKeyMatch.Success) {
    Write-Host "ERROR: ANTHROPIC_API_KEY not found in .env file" -ForegroundColor Red
    exit 1
}

$apiKey = $apiKeyMatch.Groups[1].Value.Trim()

if ($apiKey.Length -eq 0) {
    Write-Host "ERROR: ANTHROPIC_API_KEY is empty in .env file" -ForegroundColor Red
    exit 1
}

# Validate format
if ($apiKey -notmatch '^sk-ant-') {
    Write-Host "ERROR: ANTHROPIC_API_KEY has invalid format (should start with 'sk-ant-')" -ForegroundColor Red
    exit 1
}

$maskedKey = $apiKey.Substring(0, 20) + "..." + $apiKey.Substring($apiKey.Length - 4)
Write-Host "  + Found API key: $maskedKey" -ForegroundColor Green

# Step 3: Test API key with Anthropic API
Write-Host ""
Write-Host "[3/6] Testing API key validity..." -ForegroundColor Yellow

try {
    $testBody = @{
        model = "claude-3-5-sonnet-20241022"
        max_tokens = 10
        messages = @(
            @{
                role = "user"
                content = "Hi"
            }
        )
    } | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "https://api.anthropic.com/v1/messages" `
        -Method Post `
        -Headers @{
            "x-api-key" = $apiKey
            "anthropic-version" = "2023-06-01"
            "content-type" = "application/json"
        } `
        -Body $testBody `
        -ErrorAction Stop

    Write-Host "  + API key is VALID" -ForegroundColor Green

} catch {
    $errorMessage = $_.Exception.Message
    if ($errorMessage -match "authentication") {
        Write-Host "ERROR: API key is INVALID (authentication failed)" -ForegroundColor Red
        exit 1
    } elseif ($errorMessage -match "model") {
        # Model error means authentication worked
        Write-Host "  + API key is VALID (authentication succeeded)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Could not fully validate API key: $errorMessage" -ForegroundColor Yellow
        Write-Host "  Continuing anyway..." -ForegroundColor Yellow
    }
}

# Step 4: Get repository info
Write-Host ""
Write-Host "[4/6] Getting repository info..." -ForegroundColor Yellow

try {
    $repoInfo = gh repo view --json nameWithOwner | ConvertFrom-Json
    $repoFullName = $repoInfo.nameWithOwner
    Write-Host "  + Repository: $repoFullName" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not get repository info. Make sure you're in a git repository." -ForegroundColor Red
    exit 1
}

# Step 5: Update GitHub Secret
Write-Host ""
Write-Host "[5/6] Updating GitHub Secret..." -ForegroundColor Yellow

try {
    # Use echo to pipe the secret value to gh
    $apiKey | gh secret set ANTHROPIC_API_KEY --repo $repoFullName
    Write-Host "  + Successfully set ANTHROPIC_API_KEY in GitHub Secrets" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to update GitHub Secret: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 6: Verify secret exists
Write-Host ""
Write-Host "[6/6] Verifying GitHub Secret..." -ForegroundColor Yellow

try {
    $secrets = gh secret list --repo $repoFullName | Out-String
    if ($secrets -match "ANTHROPIC_API_KEY") {
        Write-Host "  + Verified ANTHROPIC_API_KEY exists in GitHub Secrets" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Could not verify secret (but it was likely created)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Could not verify secret (but it was likely created)" -ForegroundColor Yellow
}

# Success!
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your API key has been synced to GitHub Secrets." -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Go to any GitHub issue in your repo" -ForegroundColor White
Write-Host "  2. Comment: @claude hello" -ForegroundColor White
Write-Host "  3. Wait 30 seconds and Claude should respond!" -ForegroundColor White
Write-Host ""
Write-Host "Check Action runs at:" -ForegroundColor Cyan
Write-Host "  https://github.com/$repoFullName/actions" -ForegroundColor White
Write-Host ""

if ($Test) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Running Test (Optional)" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To test, you can manually comment '@claude hello' on an issue," -ForegroundColor White
    Write-Host "or run this command to create a test issue:" -ForegroundColor White
    Write-Host ""
    Write-Host '  gh issue create --title "Test Claude" --body "@claude Please confirm you are working"' -ForegroundColor Yellow
    Write-Host ""
}
