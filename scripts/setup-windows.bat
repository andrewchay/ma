@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   Flow 复楼 MA Agent - Windows 安装向导
echo ========================================
echo.

set "TARGET_DIR=%USERPROFILE%\MA-Agent"
set "EXE_NAME=ma-agent.exe"
set "ZIP_NAME=ma-agent-windows.zip"

:: Determine source path (same folder as this script)
set "SOURCE_DIR=%~dp0"
if "%SOURCE_DIR:~-1%"=="\" set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"

:: Look for zip in same folder, then parent (dist), then current dir
set "ZIP_PATH="
if exist "%SOURCE_DIR%\%ZIP_NAME%" set "ZIP_PATH=%SOURCE_DIR%\%ZIP_NAME%"
if not defined ZIP_PATH if exist "%SOURCE_DIR%\..\%ZIP_NAME%" set "ZIP_PATH=%SOURCE_DIR%\..\%ZIP_NAME%"
if not defined ZIP_PATH if exist "%CD%\%ZIP_NAME%" set "ZIP_PATH=%CD%\%ZIP_NAME%"

if not defined ZIP_PATH (
    echo [错误] 找不到 %ZIP_NAME%
    echo 请确保安装包和此脚本放在同一目录下。
    pause
    exit /b 1
)

:: Unzip to target directory
echo [1/5] 正在解压到 %TARGET_DIR% ...
if exist "%TARGET_DIR%" (
    echo        目录已存在，将覆盖旧文件...
    rmdir /s /q "%TARGET_DIR%" 2>nul
)
powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%TARGET_DIR%' -Force"
if errorlevel 1 (
    echo [错误] 解压失败。
    pause
    exit /b 1
)

echo [2/5] 解压完成。
echo.

:: Check if .env exists, if not copy from .env.example
set "ENV_PATH=%TARGET_DIR%\.env"
set "ENV_EXAMPLE=%TARGET_DIR%\.env.example"

if not exist "%ENV_PATH%" (
    if exist "%ENV_EXAMPLE%" (
        copy /y "%ENV_EXAMPLE%" "%ENV_PATH%" >nul
    )
)

:: Interactive .env configuration
echo [3/5] 配置 API 密钥（按回车跳过不想填的项）
echo        至少需要配置一个 LLM 提供商和一个搜索 API。
echo.

set "LLM_PROVIDER="
set "KIMI_KEY="
set "OPENAI_KEY="
set "METASO_KEY="
set "TAVILY_KEY="

set /p LLM_PROVIDER="选择默认 LLM 提供商 [kimi/openai/claude/minimax/mock] (默认: mock): "
if "!LLM_PROVIDER!"=="" set "LLM_PROVIDER=mock"

if /i "!LLM_PROVIDER!"=="kimi" (
    set /p KIMI_KEY="请输入 KIMI_API_KEY: "
)
if /i "!LLM_PROVIDER!"=="openai" (
    set /p OPENAI_KEY="请输入 OPENAI_API_KEY: "
)

set /p METASO_KEY="请输入 METASO_API_KEY (秘塔搜索，推荐): "
set /p TAVILY_KEY="请输入 TAVILY_API_KEY (可选): "

:: Write to .env using PowerShell to handle UTF-8 and special chars safely
powershell -NoProfile -Command "
$envPath = '%ENV_PATH%';
$llm = '%LLM_PROVIDER%';
$kimi = '%KIMI_KEY%';
$openai = '%OPENAI_KEY%';
$metaso = '%METASO_KEY%';
$tavily = '%TAVILY_KEY%';

$content = Get-Content $envPath -Raw -Encoding UTF8;
$content = $content -replace 'LLM_PROVIDER=.*', \"LLM_PROVIDER=$llm\";
if ($kimi) { $content = $content -replace 'KIMI_API_KEY=.*', \"KIMI_API_KEY=$kimi\"; }
if ($openai) { $content = $content -replace 'OPENAI_API_KEY=.*', \"OPENAI_API_KEY=$openai\"; }
if ($metaso) { $content = $content -replace 'METASO_API_KEY=.*', \"METASO_API_KEY=$metaso\"; }
if ($tavily) { $content = $content -replace 'TAVILY_API_KEY=.*', \"TAVILY_API_KEY=$tavily\"; }
Set-Content -Path $envPath -Value $content -Encoding UTF8 -NoNewline;
"

echo.
echo [4/5] 配置已保存到 %ENV_PATH%

:: Create desktop shortcut
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\MA-Agent.lnk"
powershell -NoProfile -Command "
$WshShell = New-Object -comObject WScript.Shell;
$Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%');
$Shortcut.TargetPath = '%TARGET_DIR%\ma-agent.exe';
$Shortcut.WorkingDirectory = '%TARGET_DIR%';
$Shortcut.IconLocation = '%TARGET_DIR%\ma-agent.exe,0';
$Shortcut.Save();
"
echo [5/5] 已在桌面创建快捷方式。
echo.

echo ========================================
echo   安装完成！
echo   安装目录: %TARGET_DIR%
echo   启动方式: 双击桌面 MA-Agent 快捷方式
echo   或直接运行: %TARGET_DIR%\ma-agent.exe
echo ========================================
echo.
pause
