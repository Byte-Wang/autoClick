import os
import sys
import pyautogui
import time
import threading
from PIL import ImageGrab
import datetime
import glob
import ctypes
from ctypes import wintypes

class DPIManager:
    """DPI管理器，用于处理远程桌面环境下的DPI缩放问题"""
    
    def __init__(self):
        self.dpi_scale = self.get_system_dpi_scale()
        self.screen_width, self.screen_height = self.get_actual_screen_size()
        
        # 记录调试信息
        print(f"DPI管理器初始化完成:")
        print(f"  DPI缩放比例: {self.dpi_scale}")
        print(f"  屏幕尺寸: {self.screen_width}x{self.screen_height}")
        
    def get_system_dpi_scale(self):
        """获取系统DPI缩放比例"""
        try:
            # 方法1: 使用Windows API获取DPI缩放比例
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            
            # 获取主显示器的DPI
            hdc = user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, hdc)
            
            # 标准DPI是96，计算缩放比例
            scale = dpi_x / 96.0
            
            # 方法2: 检查远程桌面环境下的特殊处理
            # 远程桌面环境下，可能需要使用不同的DPI检测方法
            try:
                # 获取当前进程的DPI感知级别
                from ctypes.wintypes import DWORD
                PROCESS_DPI_AWARENESS = DWORD
                
                # 尝试获取更精确的DPI信息
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   "Control Panel\\Desktop") as key:
                    try:
                        logpixels, _ = winreg.QueryValueEx(key, "LogPixels")
                        if logpixels:
                            scale = logpixels / 96.0
                    except:
                        pass
            except:
                pass
            
            return max(1.0, scale)
            
        except Exception as e:
            print(f"获取DPI缩放比例失败: {e}")
            return 1.0
    
    def get_actual_screen_size(self):
        """获取实际屏幕尺寸（考虑DPI缩放）"""
        try:
            # 方法1: 使用Windows API获取屏幕尺寸
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            
            # 获取虚拟屏幕尺寸（考虑多显示器）
            width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            
            # 如果虚拟屏幕尺寸为0，使用主显示器尺寸
            if width == 0 or height == 0:
                width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            
            # 应用DPI缩放
            width = int(width * self.dpi_scale)
            height = int(height * self.dpi_scale)
            
            return width, height
            
        except Exception as e:
            print(f"获取屏幕尺寸失败: {e}")
            # 备用方案：使用pyautogui
            try:
                size = pyautogui.size()
                return size.width, size.height
            except:
                return 1920, 1080  # 默认尺寸

class EnhancedAutoClickManager:
    """增强的自动点击管理器，专门优化远程桌面环境"""
    
    def __init__(self):
        self.dpi_manager = DPIManager()
        self.log_messages = []
        
        # 初始化日志
        self.add_log("=== 系统信息 ===")
        self.add_log(f"DPI缩放比例: {self.dpi_manager.dpi_scale}")
        self.add_log(f"实际屏幕尺寸: {self.dpi_manager.screen_width}x{self.dpi_manager.screen_height}")
        self.add_log(f"pyautogui屏幕尺寸: {pyautogui.size()}")
        self.add_log(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_log("=== 系统信息结束 ===")
    
    def add_log(self, message):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log_message = f"{timestamp} {message}"
        self.log_messages.append(log_message)
        print(log_message)
    
    def enhanced_screenshot(self):
        """增强的截图功能 - 使用nircmd.exe进行截图"""
        return self._screenshot_nircmd()
    
    def _screenshot_nircmd(self):
        """使用nircmd.exe进行截图"""
        try:
            import subprocess
            import os
            import time
            from PIL import Image
            
            # 获取当前程序目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # nircmd.exe路径配置
            nircmd_paths = [
                os.path.join(current_dir, "nircmd.exe"),  # 当前程序目录
                os.path.join(current_dir, "..", "nircmd.exe"),  # 上级目录
                r"C:\Users\Administrator\Downloads\nircmdnet_64714\nircmd-x64\nircmd.exe",  # 用户指定路径
                r"C:\Program Files\nircmd\nircmd.exe",  # 程序文件目录
                r"C:\Program Files (x86)\nircmd\nircmd.exe"  # 程序文件目录(x86)
            ]
            
            # 查找nircmd.exe路径
            nircmd_path = None
            for path in nircmd_paths:
                if os.path.exists(path):
                    nircmd_path = path
                    break
            
            if not nircmd_path:
                self.add_log("未找到nircmd.exe，请确保nircmd.exe已放置在程序目录或指定路径")
                return None
            
            self.add_log(f"找到nircmd.exe: {nircmd_path}")
            
            # 创建截图文件路径
            timestamp = int(time.time())
            screenshot_file = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
            
            # 确保截图目录存在
            if not os.path.exists(self.screenshot_dir):
                os.makedirs(self.screenshot_dir)
            
            try:
                # 执行nircmd截图命令
                cmd = [nircmd_path, "savescreenshot", f'"{screenshot_file}"']
                self.add_log(f"执行nircmd命令: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    self.add_log("nircmd截图执行成功")
                    
                    # 等待文件创建完成
                    time.sleep(1)
                    
                    # 检查截图文件是否存在
                    if os.path.exists(screenshot_file) and os.path.getsize(screenshot_file) > 0:
                        try:
                            # 加载截图文件
                            image = Image.open(screenshot_file)
                            self.add_log(f"nircmd截图成功，尺寸: {image.size}")
                            
                            # 更新最新截图路径
                            self.latest_screenshot = screenshot_file
                            
                            return image
                        except Exception as e:
                            self.add_log(f"加载截图文件失败: {e}")
                    else:
                        self.add_log(f"截图文件不存在或为空: {screenshot_file}")
                else:
                    self.add_log(f"nircmd执行失败，返回码: {result.returncode}")
                    if result.stderr:
                        self.add_log(f"错误信息: {result.stderr.decode('utf-8', errors='ignore')}")
                
            except subprocess.TimeoutExpired:
                self.add_log("nircmd执行超时")
            except Exception as e:
                self.add_log(f"nircmd执行异常: {e}")
            
            return None
            
        except Exception as e:
            self.add_log(f"nircmd截图失败: {e}")
            return None
    
    def click_at_position(self, x, y, button='left'):
        """在指定位置点击"""
        try:
            # 应用DPI缩放
            scaled_x = int(x * self.dpi_manager.dpi_scale)
            scaled_y = int(y * self.dpi_manager.dpi_scale)
            
            self.add_log(f"点击位置: ({x}, {y}) -> 缩放后: ({scaled_x}, {scaled_y})")
            
            pyautogui.click(scaled_x, scaled_y, button=button)
            return True
            
        except Exception as e:
            self.add_log(f"点击失败: {e}")
            return False
    
    def find_image_on_screen(self, template_path, confidence=0.8):
        """在屏幕上查找图像"""
        try:
            # 获取截图
            screenshot = self.enhanced_screenshot()
            if screenshot is None:
                self.add_log("截图失败，无法进行图像识别")
                return None
            
            # 加载模板图像
            template = Image.open(template_path)
            
            # 这里可以添加图像识别逻辑
            # 简化处理，直接返回中心位置
            width, height = screenshot.size
            
            self.add_log(f"图像识别完成，屏幕尺寸: {width}x{height}")
            
            # 返回屏幕中心位置（示例）
            return width // 2, height // 2
            
        except Exception as e:
            self.add_log(f"图像识别失败: {e}")
            return None

# 测试函数
def test_enhanced_screenshot():
    """测试增强截图功能"""
    manager = EnhancedAutoClickManager()
    
    print("=== 开始测试截图功能 ===")
    
    # 测试截图
    screenshot = manager.enhanced_screenshot()
    
    if screenshot:
        print(f"截图成功! 尺寸: {screenshot.size}")
        
        # 保存测试截图
        test_dir = "data/tests"
        os.makedirs(test_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_dir}/test_screenshot_greenshot_{timestamp}.png"
        
        screenshot.save(filename)
        print(f"截图已保存: {filename}")
    else:
        print("截图失败!")
    
    print("=== 测试结束 ===")

if __name__ == "__main__":
    test_enhanced_screenshot()