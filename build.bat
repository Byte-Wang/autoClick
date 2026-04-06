@echo off

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 删除旧的exe文件
if exist dist\main.exe (
    echo 删除旧的main.exe...
    del dist\main.exe
)
if exist dist\auto_tool.exe (
    echo 删除旧的auto_tool.exe...
    del dist\auto_tool.exe
)

REM 执行打包指令
echo 开始打包...
pyinstaller --onedir --windowed --icon=icon.png --name auto_tool --clean --noconfirm main.py

echo 打包完成！
pause