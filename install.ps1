# PAMHoYA Backend Installation Script
# Run this script to set up the complete backend environment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PAMHoYA Backend Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".venv") {
    Write-Host "`nVirtual environment already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/n)"
    if ($response -eq "y") {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
        Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
    }
} else {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install backend requirements
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installing Backend Requirements" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
python -m pip install -r requirements.txt

# Install harmony library
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installing Harmony Library" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Set-Location harmony
python -m pip install -e .
Set-Location ..

# Verify installation
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verifying Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Testing harmony import..." -ForegroundColor Yellow
$testImport = python -c "import harmony; print('SUCCESS')" 2>&1
if ($testImport -like "*SUCCESS*") {
    Write-Host "✅ Harmony library installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Error importing harmony library" -ForegroundColor Red
    Write-Host $testImport -ForegroundColor Red
}

Write-Host "`nTesting harmony version..." -ForegroundColor Yellow
python -c "import harmony; print(f'Harmony version: {harmony.__version__}')"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run validation: cd harmony\tests; python validate_similarity_fix.py" -ForegroundColor White
Write-Host "2. Run tests: cd harmony; python -m pytest tests/ -v" -ForegroundColor White
Write-Host "3. Start API: python main.py" -ForegroundColor White
Write-Host "`n"

# Keep terminal open
Read-Host "Press Enter to exit"
