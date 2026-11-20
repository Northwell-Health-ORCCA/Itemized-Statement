@echo off
:: sets up run variables
set FILE_PATH=%~dp0
set SCRIPT_PATH=%FILE_PATH%main.py
set VENV_PATH=%FILE_PATH%.venv
set "MAX_TRIES=4"  
set "ATTEMPT=1"

:: activate the virtual environment
call "%VENV_PATH%\Scripts\activate.bat"

:TRY_LOOP  
echo [%DATE% %TIME%] Attempt %ATTEMPT% of %MAX_TRIES%: Running itemized-statements...

uv run itemized-statements

:: Check if it succeeded (Exit code 0)  
IF %ERRORLEVEL% EQU 0 (  
    echo [%DATE% %TIME%] Success, Script completed.  
    goto END  
)

:: Check if it failed with exit code 1  
IF %ERRORLEVEL% EQU 1 (  
    echo [%DATE% %TIME%] Script failed with exit code 1.  
) else (  
    echo [%DATE% %TIME%] Script failed with unexpected exit code: %ERRORLEVEL%. Treating as retryable...  
)

:: Check if we have hit the maximum number of tries  
IF %ATTEMPT% GEQ %MAX_TRIES% (  
    echo [%DATE% %TIME%] Reached maximum attempts (%MAX_TRIES%). Giving up.  
    goto END  
)

:: Increment attempt counter  
set /a ATTEMPT+=1

echo Waiting 15 minutes before retry...  
:: 900 seconds = 15 minutes  
timeout /t 900 /nobreak >nul

:: Loop back to try again  
goto TRY_LOOP

:END  
exit /b %ERRORLEVEL% 