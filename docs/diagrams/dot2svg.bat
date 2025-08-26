@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem dot2svg.bat - Convert Graphviz .dot -> .svg next to the input file(s)

rem --- Check Graphviz 'dot' availability ---
where /Q dot
if errorlevel 1 (
  echo [ERROR] Graphviz 'dot' not found in PATH.
  echo         Install Graphviz and ensure 'dot.exe' is in PATH.
  exit /b 2
)

if "%~1"=="" (
  echo Usage: dot2svg file1.dot [file2.dot ...]
  echo        dot2svg path\to\folder   ^(recursively converts all *.dot^)
  exit /b 1
)

set "ERR=0"

rem --- Process all arguments (files or folders) ---
for %%A in (%*) do (
  if exist "%%~A\NUL" (
    rem Argument is a folder: recurse and convert all *.dot
    for /R "%%~A" %%F in (*.dot) do (
      set "IN=%%~fF"
      set "OUT=%%~dpnF.svg"
      echo Converting "!IN!" ^> "!OUT!"
      dot -Tsvg "!IN!" -o "!OUT!"
      if errorlevel 1 (echo   [FAIL] "!IN!"& set "ERR=1") else echo   [OK]
    )
  ) else (
    rem Argument is a file
    if /I "%%~xA" NEQ ".dot" (
      echo Skipping "%%~fA" ^(not a .dot file^)
    ) else (
      set "IN=%%~fA"
      set "OUT=%%~dpnA.svg"
      echo Converting "!IN!" ^> "!OUT!"
      dot -Tsvg "!IN!" -o "!OUT!"
      if errorlevel 1 (echo   [FAIL] "!IN!"& set "ERR=1") else echo   [OK]
    )
  )
)

exit /b %ERR%

