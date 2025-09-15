@echo off
REM Installation script for OmicsIntegrationSuite on Windows
REM Run this script as Administrator

echo ==================================
echo OmicsIntegrationSuite Installation
echo ==================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation:
    echo 1. Restart your computer
    echo 2. Start Docker Desktop
    echo 3. Run this script again
    pause
    exit /b 1
)

echo [INFO] Docker found: 
docker --version
echo.

REM Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running!
    echo.
    echo Please start Docker Desktop and wait for it to initialize.
    echo Then run this script again.
    pause
    exit /b 1
)

echo [INFO] Docker daemon is running
echo.

REM Offer build options
echo Select build option:
echo 1. Minimal (Python only, ~500MB, 2-3 min)
echo 2. Full (All tools, ~2GB, 10-15 min)
echo 3. Skip build (use existing images)
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo [INFO] Building minimal Docker image...
    echo This will take 2-3 minutes...
    docker build -f Dockerfile.minimal -t omics-suite:minimal .
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed!
        pause
        exit /b 1
    )
    set IMAGE_TAG=minimal
) else if "%choice%"=="2" (
    echo.
    echo [INFO] Building full Docker image...
    echo This will take 10-15 minutes and download ~2GB...
    docker build -t omics-suite:latest .
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed!
        pause
        exit /b 1
    )
    set IMAGE_TAG=latest
) else if "%choice%"=="3" (
    echo.
    echo [INFO] Skipping build, using existing images...
    set IMAGE_TAG=latest
) else (
    echo [ERROR] Invalid choice!
    pause
    exit /b 1
)

echo.
echo ==================================
echo Installation completed!
echo ==================================
echo.

REM Show available commands
echo Available commands:
echo.
echo 1. Test installation:
echo    docker run --rm omics-suite:%IMAGE_TAG% python -c "print('Hello from OmicsIntegrationSuite!')"
echo.
echo 2. Interactive shell:
echo    docker run -it --rm -v %cd%\data:/data omics-suite:%IMAGE_TAG% bash
echo.
echo 3. Process data:
echo    docker run --rm -v %cd%\data:/data omics-suite:%IMAGE_TAG% --input /data/input --output /data/output
echo.
echo 4. Start Jupyter:
echo    docker run -p 8888:8888 -v %cd%\notebooks:/notebooks omics-suite:%IMAGE_TAG% jupyter notebook --ip=0.0.0.0
echo.
echo 5. Check tools:
echo    docker run --rm omics-suite:%IMAGE_TAG% bash -c "samtools --version"
echo.

REM Test the installation
echo Testing installation...
docker run --rm omics-suite:%IMAGE_TAG% python -c "import pysam; print('pysam version:', pysam.__version__)"
if %errorlevel% eq 0 (
    echo [SUCCESS] Installation test passed!
) else (
    echo [WARNING] Installation test failed. Some features may not work.
)

echo.
pause