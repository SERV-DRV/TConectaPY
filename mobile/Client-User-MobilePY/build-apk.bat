@echo off
echo === T-Conecta APK Builder ===
echo.

echo [1/3] Building Docker image...
docker build -t tconecta-builder .

echo.
echo [2/3] Compiling APK (first time takes 10-15 min)...
docker run --rm -v "%cd%\bin:/home/builder/app/bin" tconecta-builder bash -c "buildozer android debug"

echo.
echo [3/3] Done!
echo APK ubicado en: %cd%\bin\
dir /b %cd%\bin\*.apk 2>nul
