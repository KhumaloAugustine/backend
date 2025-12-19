# PAMHoYA Backend Installation Script (Non-Interactive)
# Automatically installs all dependencies

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PAMHoYA Backend Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Remove existing virtual environment if it exists
if (Test-Path ".venv") {
    Write-Host "`nRemoving existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
}

# Create new virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install backend requirements
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installing Backend Requirements" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
python -m pip install -r requirements.txt

# Install harmony library
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installing Harmony Library" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Push-Location harmony
python -m pip install -e .
Pop-Location

# Verify installation
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verifying Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Testing harmony import..." -ForegroundColor Yellow
$testImport = python -c "import harmony; print('SUCCESS')" 2>&1
if ($testImport -like "*SUCCESS*") {
    Write-Host "✅ Harmony library installed successfully!" -ForegroundColor Green
    python -c "import harmony; print(f'Harmony version: {harmony.__version__}')"
} else {
    Write-Host "❌ Error importing harmony library" -ForegroundColor Red
    Write-Host $testImport -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Activate venv: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run validation: .\test_fix.ps1" -ForegroundColor White
Write-Host "3. Start API: python main.py" -ForegroundColor White
Write-Host "`n"
