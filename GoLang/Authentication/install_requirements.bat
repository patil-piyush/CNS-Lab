@echo off
echo Installing project dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Requirements installed successfully!
pause
  