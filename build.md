# Auto Tool 打包指南

本文档详细说明如何将 Python 自动点击工具打包成可执行文件。

## 快速开始

### 方法一：使用批处理文件（推荐）
```bash
# 运行优化版打包脚本
build_optimized.bat

# 或运行简化版打包脚本
build_simple.bat
```

### 方法二：手动执行 PyInstaller 命令
```bash
pyinstaller --onedir --windowed --icon=icon.png --name auto_tool --add-data "icon.png;." --add-data "config.json;." --add-data "git-download.html;." --hidden-import=cv2 --hidden-import=numpy --hidden-import=pyautogui --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageGrab --clean --noconfirm main.py
```

### 方法三：使用 spec 文件
```bash
pyinstaller auto_tool.spec --clean --noconfirm
```

## 环境要求

### 必需软件
- Python 3.7+
- PyInstaller 6.0+
- 项目依赖包（requirements.txt）

### 安装依赖
```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 详细打包流程

### 1. 准备工作
确保项目目录包含以下文件：
- `main.py` - 主程序文件
- `requirements.txt` - 依赖包列表
- `icon.png` - 程序图标
- `config.json` - 配置文件
- `auto_tool.spec` - PyInstaller 配置文件

### 2. 清理旧构建文件
```bash
# 删除旧的构建目录
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
```

### 3. 执行打包
选择以下任一方法：

#### 方法一：批处理文件（推荐）
双击运行 `build_optimized.bat` 或 `build_simple.bat`

#### 方法二：命令行打包
```bash
# 基本打包命令
pyinstaller --onedir --windowed --icon=icon.png --name auto_tool main.py

# 完整打包命令（包含所有依赖）
pyinstaller --onedir --windowed --icon=icon.png --name auto_tool --add-data "icon.png;." --add-data "config.json;." --add-data "git-download.html;." --hidden-import=cv2 --hidden-import=numpy --hidden-import=pyautogui --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageGrab --clean --noconfirm main.py
```

#### 方法三：使用 spec 文件
```bash
pyinstaller auto_tool.spec --clean --noconfirm
```

### 4. 验证打包结果
打包完成后，检查以下内容：
- `dist/auto_tool/auto_tool.exe` 是否存在
- `dist/auto_tool/_internal/` 目录是否包含必要的 DLL 文件
- 资源文件（图标、配置）是否已正确包含

## 打包参数说明

### 关键参数
- `--onedir` - 创建单目录可执行文件（推荐）
- `--windowed` - 不显示控制台窗口（GUI程序）
- `--icon=icon.png` - 设置程序图标
- `--name auto_tool` - 指定输出文件名
- `--add-data` - 添加额外数据文件
- `--hidden-import` - 显式导入隐藏的依赖模块
- `--clean` - 清理临时文件
- `--noconfirm` - 不询问确认

### 依赖模块说明
项目使用以下关键模块，需要显式包含：
- `cv2` - OpenCV 计算机视觉库
- `numpy` - 数值计算库
- `pyautogui` - 自动化控制库
- `PIL` / `PIL.Image` / `PIL.ImageGrab` - 图像处理库

## 修改代码后的打包流程

### 常规修改流程
1. 修改源代码文件（如 `main.py`, `auto_click.py` 等）
2. 测试代码功能正常
3. 运行打包命令
4. 验证新版本可执行文件

### 添加新依赖
如果添加了新的 Python 包：
1. 更新 `requirements.txt` 文件
2. 安装新依赖：`pip install -r requirements.txt`
3. 在打包命令中添加 `--hidden-import` 参数
4. 或更新 `auto_tool.spec` 文件中的 `hiddenimports` 列表

### 添加新资源文件
如果添加了新的图片、配置文件等：
1. 将文件放在项目根目录
2. 在打包命令中添加 `--add-data "文件名;."` 参数
3. 或更新 `auto_tool.spec` 文件中的 `datas` 列表

## 输出文件说明

### 生成的文件结构
```
dist/auto_tool/
├── auto_tool.exe          # 主程序可执行文件
├── icon.png               # 程序图标
├── config.json            # 配置文件
├── git-download.html      # 相关文件
└── _internal/             # 内部依赖目录
    ├── VCRUNTIME140.dll   # Visual C++ 运行时库
    ├── cv2/               # OpenCV 相关文件
    ├── numpy/             # NumPy 相关文件
    └── ...                # 其他依赖文件
```

### 分发说明
- 将整个 `dist/auto_tool` 目录复制到目标电脑
- 双击 `auto_tool.exe` 即可运行
- 无需在目标电脑安装 Python 或任何依赖

## 常见问题与解决方案

### 问题1：打包失败，提示模块找不到
**解决方案：**
- 检查 `requirements.txt` 是否包含所有依赖
- 使用 `--hidden-import` 显式导入模块
- 确保所有依赖已正确安装

### 问题2：可执行文件在其他电脑无法运行
**解决方案：**
- 确保目标电脑安装了 Visual C++ 运行时库
- 尝试以管理员身份运行
- 检查防火墙或杀毒软件是否阻止程序运行

### 问题3：程序运行时缺少资源文件
**解决方案：**
- 检查 `--add-data` 参数是否正确设置
- 确保资源文件路径正确
- 验证 spec 文件中的 `datas` 配置

### 问题4：打包文件过大
**解决方案：**
- 使用 `--exclude-module` 排除不必要的模块
- 启用 UPX 压缩：添加 `--upx-dir` 参数
- 优化 spec 文件中的排除列表

## 高级配置

### 自定义 spec 文件
`auto_tool.spec` 文件包含完整的打包配置，可以手动编辑以下部分：

```python
# 添加数据文件
datas=[('icon.png', '.'), ('config.json', '.'), ('git-download.html', '.')]

# 添加隐藏导入
hiddenimports=['cv2', 'numpy', 'pyautogui', 'PIL', 'PIL.Image', 'PIL.ImageGrab']

# 排除不必要的模块（减小文件大小）
excludes=['matplotlib', 'scipy', 'pandas', 'test', 'unittest']
```

### 优化打包大小
```bash
# 使用 UPX 压缩（需要先安装 UPX）
pyinstaller --upx-dir "path/to/upx" --onedir --windowed main.py

# 排除不必要的模块
pyinstaller --exclude-module matplotlib --exclude-module scipy main.py
```

## 版本管理建议

### 推荐的工作流程
1. 在修改代码前创建 Git 分支
2. 完成修改并测试功能
3. 打包生成可执行文件
4. 提交代码更改
5. 将可执行文件添加到发布版本

### 文件版本控制
- 将源代码文件添加到版本控制
- 忽略构建生成的文件：
```gitignore
build/
dist/
__pycache__/
*.spec
```

## 联系方式

如有问题或建议，请参考项目文档或联系开发团队。

---
*最后更新：2026-04-19*