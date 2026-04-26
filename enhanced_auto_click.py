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
                        log_pixels, _ = winreg.QueryValueEx(key, "LogPixels")
                        if log_pixels:
                            scale = log_pixels / 96.0
                    except:
                        pass
            except:
                pass
                
            return max(1.0, scale)  # 确保最小缩放为1.0
        except:
            # 如果获取失败，默认返回1.0
            return 1.0
    
    def get_actual_screen_size(self):
        """获取实际屏幕尺寸（专门处理远程桌面缩放问题）"""
        try:
            user32 = ctypes.windll.user32
            
            # 方法1: 尝试获取物理分辨率（适用于远程桌面）
            try:
                # 使用GetDeviceCaps获取物理分辨率
                hdc = user32.GetDC(0)
                physical_width = ctypes.windll.gdi32.GetDeviceCaps(hdc, 118)  # HORZRES
                physical_height = ctypes.windll.gdi32.GetDeviceCaps(hdc, 117)  # VERTRES
                user32.ReleaseDC(0, hdc)
                
                if physical_width > 0 and physical_height > 0:
                    print(f"检测到物理分辨率: {physical_width}x{physical_height}")
                    return physical_width, physical_height
            except:
                pass
            
            # 方法2: 获取虚拟屏幕尺寸（考虑多显示器）
            virtual_width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            virtual_height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            
            if virtual_width > 0 and virtual_height > 0:
                print(f"检测到虚拟屏幕尺寸: {virtual_width}x{virtual_height}")
                
                # 检查是否为高分辨率远程桌面
                logical_width = user32.GetSystemMetrics(0)  # 逻辑宽度
                logical_height = user32.GetSystemMetrics(1)  # 逻辑高度
                
                # 如果虚拟尺寸远大于逻辑尺寸，说明是远程桌面高分辨率
                if virtual_width > logical_width * 1.5 or virtual_height > logical_height * 1.5:
                    print(f"检测到远程桌面高分辨率环境: 逻辑{logical_width}x{logical_height}, 虚拟{virtual_width}x{virtual_height}")
                    return virtual_width, virtual_height
                else:
                    return virtual_width, virtual_height
            
            # 方法3: 使用主显示器逻辑尺寸
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            print(f"使用逻辑分辨率: {width}x{height}")
            return width, height
            
        except:
            # 方法4: 使用pyautogui的尺寸
            try:
                size = pyautogui.size()
                print(f"使用pyautogui分辨率: {size.width}x{size.height}")
                return size.width, size.height
            except:
                # 最终备用方案
                print("使用备用分辨率: 2560x1600")
                return 2560, 1600
    
    def scale_coordinate(self, x, y):
        """将坐标按DPI缩放比例进行转换"""
        scaled_x = int(x / self.dpi_scale)
        scaled_y = int(y / self.dpi_scale)
        return scaled_x, scaled_y
    
    def unscale_coordinate(self, x, y):
        """将坐标按DPI缩放比例进行反向转换"""
        unscaled_x = int(x * self.dpi_scale)
        unscaled_y = int(y * self.dpi_scale)
        return unscaled_x, unscaled_y

class EnhancedAutoClickManager:
    """增强的自动化点击管理器，支持远程桌面环境"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tasks = {}
        self.listen_freq = int(self.config_manager.get_config("auto_click", "listen_freq", "30"))
        
        # DPI管理器
        self.dpi_manager = DPIManager()
        
        self.load_tasks()
        self.executing = False
        self.logs = []
        self.latest_screenshot = None
        self.file_lock = threading.Lock()
        
        # 创建日志和截图目录
        self.log_dir = os.path.join(os.getcwd(), "data", "logs")
        self.screenshot_dir = os.path.join(os.getcwd(), "data", "screenshots")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
        # 记录系统信息
        self.log_system_info()
    
    def log_system_info(self):
        """记录系统信息用于调试"""
        info = f"""
=== 系统信息 ===
DPI缩放比例: {self.dpi_manager.dpi_scale}
实际屏幕尺寸: {self.dpi_manager.screen_width}x{self.dpi_manager.screen_height}
pyautogui屏幕尺寸: {pyautogui.size()}
当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=== 系统信息结束 ===
"""
        self.add_log(info)
    
    def load_tasks(self):
        tasks_config = self.config_manager.get_config("auto_click", "tasks", {})
        self.tasks = tasks_config
    
    def save_tasks(self):
        self.config_manager.set_config("auto_click", "tasks", self.tasks)
    
    def add_task(self, name, image_path, actions):
        task_id = str(int(time.time()))
        
        self.tasks[task_id] = {
            "name": name,
            "image_path": image_path,
            "actions": actions,
            "status": True
        }
        
        self.save_tasks()
        return task_id
    
    def update_task_actions(self, task_id, actions):
        if task_id in self.tasks:
            self.tasks[task_id]["actions"] = actions
            self.save_tasks()
    
    def update_task(self, task_id, name, image_path, actions):
        if task_id in self.tasks:
            self.tasks[task_id]["name"] = name
            self.tasks[task_id]["image_path"] = image_path
            self.tasks[task_id]["actions"] = actions
            self.save_tasks()
    
    def start_task(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = True
            self.save_tasks()
    
    def pause_task(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = False
            self.save_tasks()
    
    def remove_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
    
    def set_listen_freq(self, freq):
        self.listen_freq = freq
    
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
                cmd = [nircmd_path, "savescreenshot", screenshot_file]
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
    
    def _screenshot_external_tool(self):
        """使用外部截图工具进行截图"""
        try:
            import subprocess
            import tempfile
            import os
            import time
            from PIL import Image
            
            # 外部工具配置
            external_tools = [
                {
                    'name': 'Greenshot',
                    'paths': [
                        r"C:\Program Files\Greenshot\Greenshot.exe",
                        r"C:\Program Files (x86)\Greenshot\Greenshot.exe",
                        r"%PROGRAMFILES%\Greenshot\Greenshot.exe",
                        r"%PROGRAMFILES(X86)%\Greenshot\Greenshot.exe"
                    ],
                    'args': ['-clipboard'],
                    'timeout': 15
                },
                {
                    'name': 'ShareX',
                    'paths': [
                        r"C:\Program Files\ShareX\ShareX.exe",
                        r"C:\Program Files (x86)\ShareX\ShareX.exe",
                        r"%PROGRAMFILES%\ShareX\ShareX.exe",
                        r"%PROGRAMFILES(X86)%\ShareX\ShareX.exe"
                    ],
                    'args': ['-clipboard', '-silent'],
                    'timeout': 15
                },
                {
                    'name': 'LightShot',
                    'paths': [
                        r"C:\Program Files\LightShot\LightShot.exe",
                        r"C:\Program Files (x86)\LightShot\LightShot.exe"
                    ],
                    'args': ['-clipboard'],
                    'timeout': 10
                },
                {
                    'name': 'PicPick',
                    'paths': [
                        r"C:\Program Files\PicPick\PicPick.exe",
                        r"C:\Program Files (x86)\PicPick\PicPick.exe"
                    ],
                    'args': ['/clipboard'],
                    'timeout': 10
                }
            ]
            
            # 尝试每个外部工具
            for tool in external_tools:
                self.add_log(f"尝试使用外部工具: {tool['name']}")
                
                # 查找工具路径
                tool_path = None
                for path_template in tool['paths']:
                    # 展开环境变量
                    path = os.path.expandvars(path_template)
                    if os.path.exists(path):
                        tool_path = path
                        break
                
                if not tool_path:
                    self.add_log(f"未找到 {tool['name']} 工具")
                    continue
                
                self.add_log(f"找到 {tool['name']}: {tool_path}")
                
                try:
                    # 创建临时文件用于保存截图
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_file.close()
                    
                    # 构建命令
                    cmd = [tool_path] + tool['args']
                    
                    # 运行外部工具
                    self.add_log(f"执行命令: {' '.join(cmd)}")
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=tool['timeout'])
                    
                    if result.returncode == 0:
                        self.add_log(f"{tool['name']} 执行成功")
                        
                        # 方法1: 尝试从剪贴板读取图像
                        try:
                            import win32clipboard
                            from io import BytesIO
                            
                            win32clipboard.OpenClipboard()
                            
                            # 尝试不同的剪贴板格式
                            formats_to_try = [
                                win32clipboard.CF_DIB,      # 设备无关位图
                                win32clipboard.CF_BITMAP,   # 位图句柄
                                14,                         # CF_ENHMETAFILE
                                15                          # CF_METAFILEPICT
                            ]
                            
                            for format_id in formats_to_try:
                                if win32clipboard.IsClipboardFormatAvailable(format_id):
                                    try:
                                        if format_id == win32clipboard.CF_DIB:
                                            data = win32clipboard.GetClipboardData(format_id)
                                            image = Image.open(BytesIO(data))
                                            win32clipboard.CloseClipboard()
                                            
                                            self.add_log(f"从剪贴板读取 {tool['name']} 截图成功")
                                            return image
                                        elif format_id == win32clipboard.CF_BITMAP:
                                            # 处理位图句柄
                                            bitmap_handle = win32clipboard.GetClipboardData(format_id)
                                            # 需要将位图句柄转换为图像数据
                                            # 这里简化处理，直接跳过
                                            pass
                                    except Exception as e:
                                        self.add_log(f"剪贴板格式 {format_id} 读取失败: {e}")
                            
                            win32clipboard.CloseClipboard()
                        except Exception as e:
                            self.add_log(f"剪贴板读取失败: {e}")
                        
                        # 方法2: 检查临时文件是否被创建
                        time.sleep(2)  # 给工具一些时间保存文件
                        
                        if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                            try:
                                image = Image.open(temp_file.name)
                                self.add_log(f"从文件读取 {tool['name']} 截图成功")
                                return image
                            except Exception as e:
                                self.add_log(f"文件读取失败: {e}")
                        
                        # 方法3: 检查默认截图目录
                        screenshot_dirs = [
                            os.path.expanduser("~\\Pictures\\Screenshots"),
                            os.path.expanduser("~\\Desktop"),
                            os.path.expanduser("~\\Documents"),
                            os.path.join(os.getcwd(), "screenshots")
                        ]
                        
                        for screenshot_dir in screenshot_dirs:
                            if os.path.exists(screenshot_dir):
                                # 查找最新的截图文件
                                png_files = [f for f in os.listdir(screenshot_dir) 
                                           if f.lower().endswith('.png')]
                                
                                if png_files:
                                    # 按修改时间排序
                                    png_files.sort(key=lambda x: os.path.getmtime(os.path.join(screenshot_dir, x)), reverse=True)
                                    latest_file = os.path.join(screenshot_dir, png_files[0])
                                    
                                    # 检查文件是否是新创建的（最近30秒内）
                                    if time.time() - os.path.getmtime(latest_file) < 30:
                                        try:
                                            image = Image.open(latest_file)
                                            self.add_log(f"从目录读取 {tool['name']} 截图成功: {latest_file}")
                                            return image
                                        except Exception as e:
                                            self.add_log(f"目录文件读取失败: {e}")
                    
                    else:
                        self.add_log(f"{tool['name']} 执行失败，返回码: {result.returncode}")
                        if result.stderr:
                            self.add_log(f"错误信息: {result.stderr.decode('utf-8', errors='ignore')}")
                    
                    # 清理临时文件
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                        
                except subprocess.TimeoutExpired:
                    self.add_log(f"{tool['name']} 执行超时")
                except Exception as e:
                    self.add_log(f"{tool['name']} 执行异常: {e}")
            
            self.add_log("所有外部工具都失败了")
            return None
            
        except Exception as e:
            self.add_log(f"外部工具截图失败: {e}")
            return None
    
    def _screenshot_termsrv(self):
        """使用远程桌面服务(termsrv.dll)专用API截图"""
        try:
            import ctypes
            from ctypes import wintypes, Structure
            
            # 尝试加载termsrv.dll
            try:
                termsrv = ctypes.windll.LoadLibrary("termsrv.dll")
                
                # 尝试使用远程桌面特定的API
                # 这些API通常不公开，但我们可以尝试一些已知的函数
                
                # 方法1: 尝试使用WTSQuerySessionInformation
                wtsapi32 = ctypes.windll.wtsapi32
                
                # 获取当前会话ID
                session_id = wintypes.DWORD()
                wtsapi32.WTSGetActiveConsoleSessionId(ctypes.byref(session_id))
                
                # 查询会话信息
                buffer = ctypes.c_void_p()
                bytes_returned = wintypes.DWORD()
                
                result = wtsapi32.WTSQuerySessionInformationW(
                    wtsapi32.WTS_CURRENT_SERVER_HANDLE,
                    session_id,
                    wtsapi32.WTSClientDisplay,  # 获取显示信息
                    ctypes.byref(buffer),
                    ctypes.byref(bytes_returned)
                )
                
                if result:
                    # 解析显示信息
                    # 这里可以获取远程桌面的显示设置
                    pass
                
            except Exception as e:
                self.add_log(f"termsrv API失败: {e}")
            
            # 如果专用API失败，回退到系统工具方法
            return self._screenshot_system_tool()
            
        except Exception as e:
            self.add_log(f"远程桌面服务API截图失败: {e}")
            return None
    
    def _screenshot_wtsapi(self):
        """使用Windows终端服务(WTS) API截图"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # 加载wtsapi32.dll
            wtsapi32 = ctypes.windll.wtsapi32
            
            # 获取当前会话ID
            session_id = wtsapi32.WTSGetActiveConsoleSessionId()
            
            # 尝试使用虚拟通道API
            # 远程桌面使用虚拟通道进行数据传输
            
            # 方法1: 尝试使用WTSVirtualChannel API
            try:
                # 打开虚拟通道
                channel_handle = wtsapi32.WTSVirtualChannelOpen(
                    wtsapi32.WTS_CURRENT_SERVER_HANDLE,
                    session_id,
                    "RDPDR"  # 远程桌面设备重定向通道
                )
                
                if channel_handle:
                    # 这里可以尝试通过虚拟通道获取屏幕数据
                    # 但需要深入了解RDP协议
                    wtsapi32.WTSVirtualChannelClose(channel_handle)
            except:
                pass
            
            # 方法2: 尝试使用其他WTS API
            # 获取会话显示信息
            buffer = ctypes.c_void_p()
            bytes_returned = wintypes.DWORD()
            
            result = wtsapi32.WTSQuerySessionInformationW(
                wtsapi32.WTS_CURRENT_SERVER_HANDLE,
                session_id,
                15,  # WTSClientDisplay
                ctypes.byref(buffer),
                ctypes.byref(bytes_returned)
            )
            
            if result and bytes_returned.value > 0:
                # 解析显示信息结构
                display_info = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD))
                
                # 这里可以获取显示设置，但无法直接截图
                wtsapi32.WTSFreeMemory(buffer)
            
            # 如果WTS API失败，回退到系统工具方法
            return self._screenshot_system_tool()
            
        except Exception as e:
            self.add_log(f"WTS API截图失败: {e}")
            return None
    
    def _screenshot_system_tool(self):
        """使用系统级截图工具（最后的备用方案）"""
        try:
            import subprocess
            import tempfile
            import os
            from PIL import Image
            
            # 方法1: 尝试使用Windows自带的snippingtool（截图工具）
            try:
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_file.close()
                
                # 尝试使用snippingtool
                # 注意：这需要用户交互，可能不适用于自动化
                result = subprocess.run([
                    'snippingtool', '/clip'
                ], capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    # 从剪贴板读取图像
                    try:
                        import win32clipboard
                        from io import BytesIO
                        
                        win32clipboard.OpenClipboard()
                        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                            image = Image.open(BytesIO(data))
                            win32clipboard.CloseClipboard()
                            return image
                        win32clipboard.CloseClipboard()
                    except:
                        pass
                
                os.unlink(temp_file.name)
            except:
                pass
            
            # 方法2: 使用PowerShell截图命令
            try:
                ps_script = '''
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $bounds = $screen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
                
                $memoryStream = New-Object System.IO.MemoryStream
                $bitmap.Save($memoryStream, [System.Drawing.Imaging.ImageFormat]::Png)
                $bytes = $memoryStream.ToArray()
                
                [System.Convert]::ToBase64String($bytes)
                '''
                
                result = subprocess.run([
                    'powershell', '-Command', ps_script
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and result.stdout:
                    import base64
                    from io import BytesIO
                    
                    image_data = base64.b64decode(result.stdout.strip())
                    image = Image.open(BytesIO(image_data))
                    return image
                    
            except:
                pass
            
            # 方法3: 最后的备用方案 - 使用现有的增强方法
            self.add_log("系统工具方法失败，回退到增强截图方法")
            return self._screenshot_directx()
            
        except Exception as e:
            self.add_log(f"系统工具截图失败: {e}")
            return None
    
    def _screenshot_directx(self):
        """使用DirectX API进行截图（绕过远程桌面限制）"""
        try:
            import ctypes
            from ctypes import wintypes, Structure
            
            # 尝试使用DirectX 9 API
            try:
                import comtypes
                import comtypes.client
                
                # 创建DirectX设备
                d3d9 = comtypes.client.GetModule("d3d9.dll")
                d3d = comtypes.CoCreateInstance(d3d9.CLSID_Direct3D9, None, comtypes.CLSCTX_ALL, d3d9.IID_IDirect3D9)
                
                # 创建设备
                hwnd = ctypes.windll.user32.GetDesktopWindow()
                
                # 获取显示模式
                mode = d3d9.D3DDISPLAYMODE()
                d3d.GetAdapterDisplayMode(d3d9.D3DADAPTER_DEFAULT, ctypes.byref(mode))
                
                # 创建设备参数
                d3dpp = d3d9.D3DPRESENT_PARAMETERS()
                d3dpp.Windowed = True
                d3dpp.SwapEffect = d3d9.D3DSWAPEFFECT_DISCARD
                d3dpp.BackBufferFormat = mode.Format
                
                # 创建设备
                device = ctypes.POINTER(d3d9.IDirect3DDevice9)()
                result = d3d.CreateDevice(d3d9.D3DADAPTER_DEFAULT, d3d9.D3DDEVTYPE_HAL, hwnd, 
                                         d3d9.D3DCREATE_SOFTWARE_VERTEXPROCESSING, 
                                         ctypes.byref(d3dpp), ctypes.byref(device))
                
                if result == d3d9.D3D_OK:
                    # 创建表面
                    surface = ctypes.POINTER(d3d9.IDirect3DSurface9)()
                    result = device.CreateOffscreenPlainSurface(mode.Width, mode.Height, 
                                                               d3d9.D3DFMT_A8R8G8B8, 
                                                               d3d9.D3DPOOL_SYSTEMMEM, 
                                                               ctypes.byref(surface), None)
                    
                    if result == d3d9.D3D_OK:
                        # 获取前端缓冲区
                        result = device.GetFrontBufferData(0, surface)
                        
                        if result == d3d9.D3D_OK:
                            # 锁定表面并获取数据
                            locked_rect = d3d9.D3DLOCKED_RECT()
                            result = surface.LockRect(ctypes.byref(locked_rect), None, 0)
                            
                            if result == d3d9.D3D_OK:
                                from PIL import Image
                                
                                # 创建图像
                                image = Image.frombuffer("RGB", (mode.Width, mode.Height), 
                                                        ctypes.string_at(locked_rect.pBits, mode.Width * mode.Height * 4), 
                                                        "raw", "BGRX", 0, 1)
                                
                                surface.UnlockRect()
                                surface.Release()
                                device.Release()
                                d3d.Release()
                                
                                return image
            except:
                pass
            
            # 如果DirectX 9失败，尝试其他方法
            return self._screenshot_opengl()
            
        except Exception as e:
            self.add_log(f"DirectX截图失败: {e}")
            return None
    
    def _screenshot_opengl(self):
        """使用OpenGL API进行截图（绕过远程桌面限制）"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # 尝试使用OpenGL
            try:
                # 加载OpenGL库
                opengl32 = ctypes.windll.opengl32
                
                # 获取桌面窗口
                hwnd = ctypes.windll.user32.GetDesktopWindow()
                
                # 获取窗口DC
                hdc = ctypes.windll.user32.GetDC(hwnd)
                
                # 设置像素格式
                pfd = wintypes.PIXELFORMATDESCRIPTOR()
                pfd.nSize = ctypes.sizeof(wintypes.PIXELFORMATDESCRIPTOR)
                pfd.nVersion = 1
                pfd.dwFlags = 0x25  # PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER
                pfd.iPixelType = 0  # PFD_TYPE_RGBA
                pfd.cColorBits = 32
                pfd.cDepthBits = 24
                pfd.cStencilBits = 8
                pfd.iLayerType = 0  # PFD_MAIN_PLANE
                
                pixel_format = opengl32.ChoosePixelFormat(hdc, ctypes.byref(pfd))
                opengl32.SetPixelFormat(hdc, pixel_format, ctypes.byref(pfd))
                
                # 创建OpenGL上下文
                hglrc = opengl32.wglCreateContext(hdc)
                opengl32.wglMakeCurrent(hdc, hglrc)
                
                # 获取窗口尺寸
                rect = wintypes.RECT()
                ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                
                # 读取像素数据
                from PIL import Image
                
                # 分配缓冲区
                buffer_size = width * height * 4
                buffer = (ctypes.c_ubyte * buffer_size)()
                
                # 使用glReadPixels读取屏幕内容
                opengl32.glReadPixels(0, 0, width, height, 0x80E1, 0x1401, buffer)  # GL_BGRA, GL_UNSIGNED_BYTE
                
                # 创建图像（需要翻转Y轴）
                image = Image.frombuffer("RGB", (width, height), buffer, "raw", "BGR", 0, -1)
                
                # 清理资源
                opengl32.wglMakeCurrent(None, None)
                opengl32.wglDeleteContext(hglrc)
                ctypes.windll.user32.ReleaseDC(hwnd, hdc)
                
                return image
                
            except:
                pass
            
            # 如果OpenGL失败，回退到其他方法
            return self._screenshot_rdp_direct()
            
        except Exception as e:
            self.add_log(f"OpenGL截图失败: {e}")
            return None
    
    def _screenshot_rdp_direct(self):
        """使用远程桌面专用API直接获取屏幕内容"""
        try:
            # 方法1: 尝试使用远程桌面服务API
            import ctypes
            from ctypes import wintypes, Structure, POINTER
            
            # 定义远程桌面相关的API
            try:
                # 尝试加载termsrv.dll（终端服务DLL）
                termsrv = ctypes.windll.LoadLibrary("termsrv.dll")
                
                # 尝试使用远程桌面特定的截图方法
                # 这里使用更底层的API来绕过限制
                
            except:
                pass
            
            # 方法2: 使用桌面组合API（DWM）
            return self._screenshot_dwm()
            
        except Exception as e:
            self.add_log(f"远程桌面直接API截图失败: {e}")
            return None
    
    def _screenshot_gdi_plus(self):
        """使用GDI+ API进行高级截图"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # 加载gdiplus.dll
            gdiplus = ctypes.windll.gdiplus
            
            # 初始化GDI+
            startup = wintypes.DWORD()
            token = wintypes.GdiplusStartupInput()
            token.GdiplusVersion = 1
            
            gdiplus.GdiplusStartup(ctypes.byref(startup), ctypes.byref(token), None)
            
            # 获取桌面窗口
            hwnd = ctypes.windll.user32.GetDesktopWindow()
            
            # 获取窗口DC
            hdc = ctypes.windll.user32.GetDC(hwnd)
            
            # 创建内存DC
            memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
            
            # 获取窗口尺寸
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # 创建位图
            bitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, width, height)
            
            # 选择位图到内存DC
            old_bitmap = ctypes.windll.gdi32.SelectObject(memdc, bitmap)
            
            # 使用BitBlt复制屏幕（尝试不同的参数组合）
            # 尝试SRCCOPY（标准复制）
            result = ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x00CC0020)
            
            if result == 0:
                # 如果SRCCOPY失败，尝试CAPTUREBLT（捕获分层窗口）
                result = ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x40000000 | 0x00CC0020)
            
            if result != 0:
                # 获取位图数据
                from PIL import Image
                
                bitmap_info = ctypes.create_string_buffer(40)
                bitmap_info_header = ctypes.cast(bitmap_info, ctypes.POINTER(ctypes.c_uint32))
                bitmap_info_header[0] = 40  # biSize
                bitmap_info_header[1] = width  # biWidth
                bitmap_info_header[2] = -height  # biHeight
                bitmap_info_header[3] = 1  # biPlanes
                bitmap_info_header[4] = 32  # biBitCount
                
                image_data = ctypes.create_string_buffer(width * height * 4)
                ctypes.windll.gdi32.GetDIBits(hdc, bitmap, 0, height, image_data, bitmap_info, 0)
                
                image = Image.frombuffer("RGB", (width, height), image_data, "raw", "BGRX", 0, 1)
                
                # 清理资源
                ctypes.windll.gdi32.SelectObject(memdc, old_bitmap)
                ctypes.windll.gdi32.DeleteObject(bitmap)
                ctypes.windll.gdi32.DeleteDC(memdc)
                ctypes.windll.user32.ReleaseDC(hwnd, hdc)
                gdiplus.GdiplusShutdown(startup)
                
                return image
            
            # 清理资源
            ctypes.windll.gdi32.SelectObject(memdc, old_bitmap)
            ctypes.windll.gdi32.DeleteObject(bitmap)
            ctypes.windll.gdi32.DeleteDC(memdc)
            ctypes.windll.user32.ReleaseDC(hwnd, hdc)
            gdiplus.GdiplusShutdown(startup)
            
            return None
            
        except Exception as e:
            self.add_log(f"GDI+截图失败: {e}")
            return None
    
    def _screenshot_dwm(self):
        """使用桌面窗口管理器(DWM) API截图"""
        try:
            import ctypes
            from ctypes import wintypes, Structure, POINTER
            
            # 定义DWM相关的结构体
            class DWM_THUMBNAIL_PROPERTIES(Structure):
                _fields_ = [
                    ("dwFlags", wintypes.DWORD),
                    ("rcDestination", wintypes.RECT),
                    ("rcSource", wintypes.RECT),
                    ("opacity", wintypes.BYTE),
                    ("fVisible", wintypes.BOOL),
                    ("fSourceClientAreaOnly", wintypes.BOOL)
                ]
            
            # 尝试使用DWM API
            dwmapi = ctypes.windll.dwmapi
            
            # 获取桌面窗口
            hwnd = ctypes.windll.user32.GetDesktopWindow()
            
            # 获取窗口尺寸
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # 创建内存DC和位图
            hdc = ctypes.windll.user32.GetDC(hwnd)
            memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
            bitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, width, height)
            old_bitmap = ctypes.windll.gdi32.SelectObject(memdc, bitmap)
            
            # 尝试使用DWM打印窗口
            try:
                # 使用DwmGetWindowAttribute获取窗口缩略图
                thumbnail = wintypes.HANDLE()
                result = dwmapi.DwmRegisterThumbnail(hwnd, hwnd, ctypes.byref(thumbnail))
                
                if result == 0:  # S_OK
                    props = DWM_THUMBNAIL_PROPERTIES()
                    props.dwFlags = 0x1 | 0x2  # 设置目标矩形和源矩形
                    props.rcDestination = rect
                    props.rcSource = rect
                    props.opacity = 255
                    props.fVisible = True
                    props.fSourceClientAreaOnly = False
                    
                    result = dwmapi.DwmUpdateThumbnailProperties(thumbnail, ctypes.byref(props))
                    
                    if result == 0:
                        # 使用BitBlt复制内容
                        ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x00CC0020)
            except:
                # 如果DWM方法失败，回退到标准BitBlt
                ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x40000000 | 0x00CC0020)
            
            # 获取位图数据
            from PIL import Image
            
            bitmap_info = ctypes.create_string_buffer(40)
            bitmap_info_header = ctypes.cast(bitmap_info, ctypes.POINTER(ctypes.c_uint32))
            bitmap_info_header[0] = 40  # biSize
            bitmap_info_header[1] = width  # biWidth
            bitmap_info_header[2] = -height  # biHeight
            bitmap_info_header[3] = 1  # biPlanes
            bitmap_info_header[4] = 32  # biBitCount
            
            image_data = ctypes.create_string_buffer(width * height * 4)
            ctypes.windll.gdi32.GetDIBits(hdc, bitmap, 0, height, image_data, bitmap_info, 0)
            
            image = Image.frombuffer("RGB", (width, height), image_data, "raw", "BGRX", 0, 1)
            
            # 清理资源
            ctypes.windll.gdi32.SelectObject(memdc, old_bitmap)
            ctypes.windll.gdi32.DeleteObject(bitmap)
            ctypes.windll.gdi32.DeleteDC(memdc)
            ctypes.windll.user32.ReleaseDC(hwnd, hdc)
            
            return image
            
        except Exception as e:
            self.add_log(f"DWM截图失败: {e}")
            return None
    
    def _screenshot_rdp_special(self):
        """专门针对远程桌面的截图方法"""
        try:
            # 方法1: 尝试使用不同的DPI感知设置
            import ctypes
            
            # 设置不同的DPI感知级别
            dpi_awareness_levels = [0, 1, 2]  # 不感知, 系统感知, 每显示器感知
            
            for level in dpi_awareness_levels:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(level)
                    
                    # 尝试截图
                    screenshot = ImageGrab.grab()
                    if screenshot and self._validate_screenshot(screenshot):
                        self.add_log(f"DPI感知级别 {level} 截图成功")
                        
                        # 检查是否需要缩放处理
                        if self._needs_rdp_scaling(screenshot):
                            self.add_log("检测到远程桌面缩放问题，进行缩放处理")
                            return self._scale_rdp_screenshot(screenshot)
                        
                        return screenshot
                except:
                    continue
            
            # 方法2: 尝试使用pyautogui的特定参数
            try:
                import pyautogui
                # 尝试使用pyautogui的截图，可能绕过某些限制
                screenshot = pyautogui.screenshot()
                if screenshot and self._validate_screenshot(screenshot):
                    if self._needs_rdp_scaling(screenshot):
                        self.add_log("检测到远程桌面缩放问题，进行缩放处理")
                        return self._scale_rdp_screenshot(screenshot)
                    return screenshot
            except:
                pass
            
            # 方法3: 使用Windows API直接截图
            return self._screenshot_windows_api()
            
        except Exception as e:
            self.add_log(f"远程桌面专用截图失败: {e}")
            return None
    
    def _needs_rdp_scaling(self, screenshot):
        """检查是否需要远程桌面缩放处理"""
        try:
            # 如果截图尺寸与检测到的物理分辨率不匹配，可能需要缩放
            if screenshot.size[0] != self.dpi_manager.screen_width or screenshot.size[1] != self.dpi_manager.screen_height:
                # 检查是否是远程桌面典型的缩放比例（2倍）
                scale_x = self.dpi_manager.screen_width / screenshot.size[0]
                scale_y = self.dpi_manager.screen_height / screenshot.size[1]
                
                # 如果是典型的2倍缩放，需要处理
                if 1.9 <= scale_x <= 2.1 and 1.9 <= scale_y <= 2.1:
                    self.add_log(f"检测到远程桌面缩放: {scale_x:.1f}x{scale_y:.1f}")
                    return True
            
            return False
        except:
            return False
    
    def _scale_rdp_screenshot(self, screenshot):
        """缩放远程桌面截图到正确尺寸"""
        try:
            from PIL import Image
            
            # 计算缩放比例
            scale_x = self.dpi_manager.screen_width / screenshot.size[0]
            scale_y = self.dpi_manager.screen_height / screenshot.size[1]
            
            self.add_log(f"缩放截图: {screenshot.size} -> {self.dpi_manager.screen_width}x{self.dpi_manager.screen_height}")
            self.add_log(f"缩放比例: {scale_x:.2f}x{scale_y:.2f}")
            
            # 使用高质量缩放算法
            scaled_screenshot = screenshot.resize(
                (self.dpi_manager.screen_width, self.dpi_manager.screen_height),
                Image.Resampling.LANCZOS
            )
            
            return scaled_screenshot
            
        except Exception as e:
            self.add_log(f"截图缩放失败: {e}")
            return screenshot
    
    def _screenshot_windows_api(self):
        """使用Windows API直接截图"""
        try:
            import ctypes
            from ctypes import wintypes
            from PIL import Image
            
            # 获取桌面窗口句柄
            hwnd = ctypes.windll.user32.GetDesktopWindow()
            
            # 获取窗口DC
            hdc = ctypes.windll.user32.GetDC(hwnd)
            
            # 获取窗口尺寸
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # 创建内存DC
            memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
            
            # 创建位图
            bitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, width, height)
            
            # 选择位图到内存DC
            old_bitmap = ctypes.windll.gdi32.SelectObject(memdc, bitmap)
            
            # 复制屏幕内容
            ctypes.windll.gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x00CC0020)
            
            # 获取位图数据
            bitmap_info = ctypes.create_string_buffer(40)
            bitmap_info_header = ctypes.cast(bitmap_info, ctypes.POINTER(ctypes.c_uint32))
            bitmap_info_header[0] = 40  # biSize
            bitmap_info_header[1] = width  # biWidth
            bitmap_info_header[2] = -height  # biHeight (负值表示从上到下)
            bitmap_info_header[3] = 1  # biPlanes
            bitmap_info_header[4] = 32  # biBitCount
            
            # 创建PIL图像
            image_data = ctypes.create_string_buffer(width * height * 4)
            ctypes.windll.gdi32.GetDIBits(hdc, bitmap, 0, height, image_data, bitmap_info, 0)
            
            image = Image.frombuffer("RGB", (width, height), image_data, "raw", "BGRX", 0, 1)
            
            # 清理资源
            ctypes.windll.gdi32.SelectObject(memdc, old_bitmap)
            ctypes.windll.gdi32.DeleteObject(bitmap)
            ctypes.windll.gdi32.DeleteDC(memdc)
            ctypes.windll.user32.ReleaseDC(hwnd, hdc)
            
            return image
            
        except Exception as e:
            self.add_log(f"Windows API截图失败: {e}")
            return None
    
    def _check_screenshot_completeness(self, screenshot):
        """检查截图是否包含完整内容（不是黑屏或白屏）"""
        try:
            # 检查截图尺寸是否合理
            if screenshot.size[0] < 100 or screenshot.size[1] < 100:
                return False
            
            # 检查多个采样点的颜色分布
            sample_points = [
                (screenshot.size[0] // 4, screenshot.size[1] // 4),
                (screenshot.size[0] // 2, screenshot.size[1] // 2),
                (screenshot.size[0] * 3 // 4, screenshot.size[1] * 3 // 4),
                (screenshot.size[0] // 4, screenshot.size[1] * 3 // 4),
                (screenshot.size[0] * 3 // 4, screenshot.size[1] // 4)
            ]
            
            colors = []
            for point in sample_points:
                if 0 <= point[0] < screenshot.size[0] and 0 <= point[1] < screenshot.size[1]:
                    color = screenshot.getpixel(point)
                    colors.append(color)
            
            # 检查颜色是否过于单一（可能是黑屏或白屏）
            if len(colors) < 3:
                return False
            
            # 计算颜色差异
            color_variance = 0
            for i in range(len(colors)):
                for j in range(i+1, len(colors)):
                    # 计算颜色差异（RGB空间的距离）
                    diff = sum((colors[i][k] - colors[j][k]) ** 2 for k in range(3))
                    color_variance += diff
            
            # 如果颜色差异太小，可能是无效截图
            if color_variance < 1000:
                return False
            
            return True
            
        except:
            return False
    
    def _screenshot_imagegrab_bbox(self):
        """使用ImageGrab带bbox参数截图"""
        try:
            # 使用实际屏幕尺寸进行截图
            return ImageGrab.grab(bbox=(0, 0, self.dpi_manager.screen_width, self.dpi_manager.screen_height))
        except Exception as e:
            # 如果bbox方式失败，尝试全屏截图
            self.add_log(f"bbox截图失败: {e}")
            return ImageGrab.grab()
    
    def _screenshot_imagegrab_full(self):
        """使用ImageGrab全屏截图"""
        try:
            # 尝试使用all_screens参数
            return ImageGrab.grab(all_screens=True)
        except:
            # 如果失败，尝试不带参数的全屏截图
            return ImageGrab.grab()
    
    def _screenshot_imagegrab_large_bbox(self):
        """使用ImageGrab带大尺寸bbox参数截图（适用于高分辨率远程桌面）"""
        try:
            # 对于高分辨率远程桌面，尝试更大的bbox范围
            return ImageGrab.grab(bbox=(0, 0, self.dpi_manager.screen_width, self.dpi_manager.screen_height))
        except Exception as e:
            self.add_log(f"大尺寸bbox截图失败: {e}")
            # 备用方案：尝试全屏截图
            return self._screenshot_imagegrab_full()
    
    def _screenshot_pyautogui(self):
        """使用pyautogui截图"""
        return pyautogui.screenshot()
    
    def _screenshot_multi_monitor(self):
        """多显示器备用方案"""
        # 尝试获取所有显示器的截图
        try:
            from PIL import Image
            
            # 获取所有显示器的截图并拼接
            screenshots = []
            for i in range(10):  # 最多尝试10个显示器
                try:
                    # 尝试获取每个显示器的截图
                    screenshot = ImageGrab.grab(bbox=(i * 1920, 0, (i + 1) * 1920, 1080))
                    if screenshot.size[0] > 0 and screenshot.size[1] > 0:
                        screenshots.append(screenshot)
                except:
                    break
            
            if screenshots:
                # 如果找到多个显示器截图，拼接成一个大图
                total_width = sum(screenshot.width for screenshot in screenshots)
                max_height = max(screenshot.height for screenshot in screenshots)
                
                combined = Image.new('RGB', (total_width, max_height))
                x_offset = 0
                for screenshot in screenshots:
                    combined.paste(screenshot, (x_offset, 0))
                    x_offset += screenshot.width
                
                return combined
        except Exception as e:
            self.add_log(f"多显示器截图失败: {e}")
        
        return None
    
    def _validate_screenshot(self, screenshot):
        """验证截图是否有效"""
        if screenshot is None:
            return False
        
        # 检查截图尺寸是否合理
        if screenshot.size[0] < 100 or screenshot.size[1] < 100:
            return False
        
        # 检查截图是否包含有效内容（不是全黑或全白）
        try:
            # 检查截图中心区域的颜色分布
            center_x = screenshot.size[0] // 2
            center_y = screenshot.size[1] // 2
            
            # 检查中心区域的颜色
            center_color = screenshot.getpixel((center_x, center_y))
            
            # 如果颜色是纯黑或纯白，可能截图无效
            if center_color == (0, 0, 0) or center_color == (255, 255, 255):
                # 检查周围几个点
                points_to_check = [
                    (center_x - 10, center_y - 10),
                    (center_x + 10, center_y + 10),
                    (center_x - 10, center_y + 10),
                    (center_x + 10, center_y - 10)
                ]
                
                all_same = True
                for point in points_to_check:
                    if 0 <= point[0] < screenshot.size[0] and 0 <= point[1] < screenshot.size[1]:
                        if screenshot.getpixel(point) != center_color:
                            all_same = False
                            break
                
                if all_same:
                    return False
        except:
            pass
        
        return True
    
    def check_screen(self):
        if self.executing:
            return
        
        has_running_task = False
        for task_id, task in self.tasks.items():
            if task["status"]:
                has_running_task = True
                break
        
        if not has_running_task:
            return
        
        try:
            # 使用增强的截图功能
            screenshot = self.enhanced_screenshot()
            if screenshot is None:
                return
            
            # 保存截图
            with self.file_lock:
                screenshot_files = sorted([f for f in os.listdir(self.screenshot_dir) 
                                          if f.startswith('screenshot_') and f.endswith('.png')])
                if len(screenshot_files) > 3:
                    for old_file in screenshot_files[:-3]:
                        old_path = os.path.join(self.screenshot_dir, old_file)
                        try:
                            if old_path != self.latest_screenshot:
                                os.remove(old_path)
                        except Exception as e:
                            pass
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
                screenshot.save(screenshot_path)
                self.latest_screenshot = screenshot_path
            
            self.add_log(f"屏幕监听: 截取屏幕成功, 尺寸: {screenshot.size}")
            
            # 检查每个任务
            for task_id, task in self.tasks.items():
                if not task["status"]:
                    continue
                
                if not os.path.exists(task["image_path"]):
                    error_msg = f"任务 {task['name']}: 图像文件不存在: {task['image_path']}"
                    self.add_log(error_msg)
                    continue
                
                try:
                    self.add_log(f"任务 {task['name']}: 开始查找图像: {task['image_path']}")
                    
                    # 使用增强的图像识别
                    location = self.enhanced_locate_on_screen(task["image_path"], screenshot)
                    
                    if location:
                        self.add_log(f"任务 {task['name']}: 图像匹配成功, 位置: {location}")
                        
                        # 执行操作
                        self.executing = True
                        self.execute_actions(task["actions"], location)
                        self.executing = False
                        
                        # 操作完成后暂停任务一段时间
                        task["status"] = False
                        self.save_tasks()
                        self.add_log(f"任务 {task['name']}: 操作完成，任务已暂停")
                        
                        # 暂停一段时间避免重复执行
                        time.sleep(5)
                        break
                    else:
                        self.add_log(f"任务 {task['name']}: 图像未找到")
                        
                except Exception as e:
                    error_msg = f"任务 {task['name']}: 图像识别失败: {str(e)}"
                    self.add_log(error_msg)
                    continue
                    
        except Exception as e:
            error_msg = f"屏幕监听异常: {str(e)}"
            self.add_log(error_msg)
    
    def enhanced_locate_on_screen(self, image_path, screenshot=None):
        """增强的图像识别功能，专门优化远程桌面环境"""
        try:
            from PIL import Image
            
            # 加载模板图像
            template = Image.open(image_path)
            self.add_log(f"模板图像尺寸: {template.size}")
            
            # 方法1: 在提供的截图上查找（优先）
            if screenshot:
                self.add_log(f"在截图上查找，截图尺寸: {screenshot.size}")
                
                # 计算缩放比例
                scale_ratio = min(screenshot.width / self.dpi_manager.screen_width, 
                                 screenshot.height / self.dpi_manager.screen_height)
                
                # 调整模板大小以适应截图
                if scale_ratio != 1.0:
                    new_width = int(template.width * scale_ratio)
                    new_height = int(template.height * scale_ratio)
                    if new_width > 0 and new_height > 0:
                        template_resized = template.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        self.add_log(f"模板调整大小: {template.size} -> {template_resized.size}, 缩放比例: {scale_ratio}")
                        template = template_resized
                
                # 尝试不同的匹配精度
                confidences = [0.9, 0.8, 0.7, 0.6]
                for confidence in confidences:
                    try:
                        location = pyautogui.locate(template, screenshot, confidence=confidence)
                        if location:
                            self.add_log(f"截图匹配成功，精度: {confidence}, 位置: {location}")
                            
                            # 将截图坐标转换为实际屏幕坐标
                            actual_location = self._convert_screenshot_to_screen_coords(location, screenshot)
                            return actual_location
                    except:
                        continue
            
            # 方法2: 直接在屏幕上查找
            self.add_log("尝试直接在屏幕上查找")
            confidences = [0.9, 0.8, 0.7, 0.6]
            for confidence in confidences:
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                    if location:
                        self.add_log(f"直接屏幕匹配成功，精度: {confidence}, 位置: {location}")
                        return location
                except:
                    continue
            
            # 方法3: 使用原始模板在屏幕上查找
            try:
                location = pyautogui.locateOnScreen(image_path)
                if location:
                    self.add_log(f"原始方法匹配成功，位置: {location}")
                    return location
            except:
                pass
            
            return None
            
        except Exception as e:
            self.add_log(f"增强图像识别失败: {e}")
            return None
    
    def _convert_screenshot_to_screen_coords(self, location, screenshot):
        """将截图中的坐标转换为实际屏幕坐标"""
        try:
            # 计算缩放比例
            scale_x = self.dpi_manager.screen_width / screenshot.width
            scale_y = self.dpi_manager.screen_height / screenshot.height
            
            # 转换坐标
            actual_left = int(location.left * scale_x)
            actual_top = int(location.top * scale_y)
            actual_width = int(location.width * scale_x)
            actual_height = int(location.height * scale_y)
            
            # 创建新的位置对象
            class Location:
                def __init__(self, left, top, width, height):
                    self.left = left
                    self.top = top
                    self.width = width
                    self.height = height
            
            actual_location = Location(actual_left, actual_top, actual_width, actual_height)
            
            self.add_log(f"坐标转换: 截图({location.left},{location.top}) -> 屏幕({actual_left},{actual_top})")
            self.add_log(f"缩放比例: X={scale_x:.3f}, Y={scale_y:.3f}")
            
            return actual_location
            
        except Exception as e:
            self.add_log(f"坐标转换失败: {e}")
            return location
    
    def execute_actions(self, actions, match_location=None):
        """执行操作，支持DPI缩放坐标转换"""
        try:
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "click_screen":
                    # 鼠标点击屏幕指定位置（考虑DPI缩放）
                    x = action.get("x", 0)
                    y = action.get("y", 0)
                    
                    # 转换坐标以适应DPI缩放
                    scaled_x, scaled_y = self.dpi_manager.scale_coordinate(x, y)
                    
                    self.add_log(f"执行操作: 鼠标点击屏幕位置 (原始: {x}, {y}, 转换后: {scaled_x}, {scaled_y})")
                    pyautogui.click(scaled_x, scaled_y)
                    
                elif action_type == "click_match":
                    # 点击匹配到的图像位置
                    if match_location:
                        # 计算图像中心点
                        center_x = match_location.left + match_location.width // 2
                        center_y = match_location.top + match_location.height // 2
                        
                        self.add_log(f"执行操作: 点击匹配图像中心位置 ({center_x}, {center_y})")
                        pyautogui.click(center_x, center_y)
                    
                elif action_type == "delay":
                    # 延迟
                    delay_time = action.get("time", 1)
                    self.add_log(f"执行操作: 延迟 {delay_time} 秒")
                    time.sleep(delay_time)
                    
                elif action_type == "key_press":
                    # 按键操作
                    key = action.get("key", "")
                    self.add_log(f"执行操作: 按键 {key}")
                    pyautogui.press(key)
            
        except Exception as e:
            self.add_log(f"执行操作失败: {e}")
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 添加到内存日志
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        # 保存到文件
        log_file = os.path.join(self.log_dir, f"enhanced_auto_click_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except:
            pass
        
        # 同时输出到控制台（用于调试）
        print(log_entry)