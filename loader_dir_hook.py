import os
import sys

# 定义LOADER_DIR变量
if hasattr(sys, '_MEIPASS'):
    LOADER_DIR = os.path.dirname(sys.executable)
else:
    LOADER_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义BINARIES_PATHS变量
BINARIES_PATHS = []

# 将LOADER_DIR添加到系统变量中
os.environ['LOADER_DIR'] = LOADER_DIR

# 将LOADER_DIR和BINARIES_PATHS添加到全局命名空间，这样cv2的config.py可以直接引用
import builtins
builtins.LOADER_DIR = LOADER_DIR
builtins.BINARIES_PATHS = BINARIES_PATHS