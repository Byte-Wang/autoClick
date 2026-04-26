import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.font
import threading
import time
import os
import sys
import ctypes

# 添加当前目录到sys.path，确保优先导入项目中的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schedule_task import ScheduleTaskManager
from enhanced_auto_click import EnhancedAutoClickManager
from app_config import ConfigManager

# 设置DPI感知，确保在远程桌面环境下正确显示
if os.name == 'nt':  # Windows系统
    try:
        # 设置进程为DPI感知
        ctypes.windll.user32.SetProcessDPIAware()
        
        # 获取系统DPI缩放比例
        hdc = ctypes.windll.user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        dpi_scale = dpi_x / 96.0
        
        # 设置tkinter的缩放比例
        if dpi_scale > 1.0:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

class AutoToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化工具")
        
        # 获取系统信息并智能调整窗口大小
        try:
            # 获取实际屏幕尺寸
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            screen_height = ctypes.windll.user32.GetSystemMetrics(1)
            
            # 获取DPI信息
            hdc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            dpi_scale = dpi_x / 96.0
            
            # 智能窗口大小计算
            base_width = 1200  # 降低基础宽度以适应小屏幕
            base_height = 800  # 降低基础高度以适应小屏幕
            
            # 确保窗口不超过屏幕尺寸的80%
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            
            # 计算最终窗口大小
            scaled_width = min(int(base_width / dpi_scale), max_width)
            scaled_height = min(int(base_height / dpi_scale), max_height)
            
            # 确保最小尺寸
            min_width = 800
            min_height = 600
            scaled_width = max(scaled_width, min_width)
            scaled_height = max(scaled_height, min_height)
            
            self.root.geometry(f"{scaled_width}x{scaled_height}")
            
            # 设置字体大小适应DPI
            default_font = tk.font.nametofont("TkDefaultFont")
            font_size = max(8, int(10 / dpi_scale))  # 确保最小字体大小
            default_font.configure(size=font_size)
            
            # 记录窗口设置信息
            print(f"屏幕尺寸: {screen_width}x{screen_height}")
            print(f"DPI缩放: {dpi_scale}")
            print(f"窗口大小: {scaled_width}x{scaled_height}")
            
        except Exception as e:
            # 如果获取失败，使用安全的默认大小
            print(f"窗口设置失败: {e}")
            self.root.geometry("1000x700")  # 更小的默认大小
        
        # 配置管理
        self.config_manager = ConfigManager()
        
        # 定时任务管理器
        self.schedule_manager = ScheduleTaskManager(self.config_manager)
        
        # 自动化点击管理器（使用增强版本，支持远程桌面）
        self.auto_click_manager = EnhancedAutoClickManager(self.config_manager)
        
        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 定时任务标签页
        self.schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.schedule_frame, text="定时打开URL")
        
        # 自动化点击标签页
        self.auto_click_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.auto_click_frame, text="自动化点击")
        
        # 初始化界面
        self.init_schedule_ui()
        self.init_auto_click_ui()
        
        # 启动后台线程
        self.start_background_threads()
    
    def init_schedule_ui(self):
        # 任务列表
        self.schedule_tree = ttk.Treeview(self.schedule_frame, columns=("name", "url", "time", "status"), show="headings")
        self.schedule_tree.heading("name", text="任务名称")
        self.schedule_tree.heading("url", text="URL")
        self.schedule_tree.heading("time", text="执行时间")
        self.schedule_tree.heading("status", text="状态")
        # 设置行高
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        self.schedule_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(self.schedule_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_btn = ttk.Button(button_frame, text="添加任务", command=self.add_schedule_task)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        start_btn = ttk.Button(button_frame, text="启动任务", command=self.start_schedule_task)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        pause_btn = ttk.Button(button_frame, text="暂停任务", command=self.pause_schedule_task)
        pause_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ttk.Button(button_frame, text="移除任务", command=self.remove_schedule_task)
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # 底部编辑按钮
        edit_frame = ttk.Frame(self.schedule_frame)
        edit_frame.pack(fill=tk.X, padx=10, pady=10)
        
        edit_btn = ttk.Button(edit_frame, text="编辑选中任务", command=self.edit_schedule_task)
        edit_btn.pack(fill=tk.X)
        
        # 刷新任务列表
        self.refresh_schedule_list()
    
    def capture_screen(self, image_var=None):
        """统一的屏幕截图功能，支持区域选择"""
        # 创建日志文件
        log_dir = os.path.join(os.getcwd(), "data", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "screenshot_debug.log")
        
        def log_message(message):
            """记录日志到文件和控制台"""
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            print(log_entry, end='')
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        
        log_message("开始截图流程")
        
        # 创建data/images目录
        image_dir = os.path.join(os.getcwd(), "data", "images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            log_message(f"创建图片目录: {image_dir}")
        
        # 截取屏幕 - 使用nircmd.exe
        from PIL import Image, ImageTk
        import subprocess
        import time
        
        log_message("开始使用nircmd.exe截取屏幕")
        
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
            log_message("未找到nircmd.exe，请确保nircmd.exe已放置在程序目录或指定路径")
            return
        
        log_message(f"找到nircmd.exe: {nircmd_path}")
        
        # 创建临时截图文件
        timestamp = int(time.time())
        temp_screenshot = os.path.join(image_dir, f"temp_screenshot_{timestamp}.png")
        
        # 执行nircmd截图命令
        cmd = [nircmd_path, "savescreenshot", f'"{temp_screenshot}"']
        log_message(f"执行nircmd命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode == 0:
            log_message("nircmd截图执行成功")
            
            # 等待文件创建完成
            time.sleep(1)
            
            # 检查截图文件是否存在
            if os.path.exists(temp_screenshot) and os.path.getsize(temp_screenshot) > 0:
                try:
                    # 加载截图文件
                    screen = Image.open(temp_screenshot)
                    log_message(f"nircmd截图成功，尺寸: {screen.width}x{screen.height}")
                except Exception as e:
                    log_message(f"加载截图文件失败: {e}")
                    return
            else:
                log_message(f"截图文件不存在或为空: {temp_screenshot}")
                return
        else:
            log_message(f"nircmd执行失败，返回码: {result.returncode}")
            if result.stderr:
                log_message(f"错误信息: {result.stderr.decode('utf-8', errors='ignore')}")
            return
        
        # 创建截图预览窗口
        log_message("创建截图预览窗口")
        capture_dialog = tk.Toplevel(self.root)
        capture_dialog.title("屏幕截图 - 选择区域")
        capture_dialog.geometry(f"{screen.width}x{screen.height}+0+0")
        capture_dialog.attributes("-topmost", True)
        
        # 确保窗口能够捕获所有鼠标事件
        capture_dialog.grab_set()
        capture_dialog.focus_force()
        
        # 创建画布
        from PIL import ImageTk
        img = ImageTk.PhotoImage(screen)
        canvas = tk.Canvas(capture_dialog, width=screen.width, height=screen.height, cursor="crosshair")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 显示截图
        canvas.create_image(0, 0, anchor=tk.NW, image=img)
        canvas.image = img
        
        # 保存原始截图尺寸和比例
        original_screen_size = (screen.width, screen.height)
        screen_ratio = screen.width / screen.height
        log_message(f"原始截图尺寸: {original_screen_size}, 宽高比: {screen_ratio:.3f}")
        
        def on_window_resize(event):
            """窗口缩放事件处理，保持截图比例"""
            if not hasattr(canvas, 'image'):
                return
                
            # 获取当前窗口尺寸
            window_width = event.width
            window_height = event.height
            
            # 计算保持比例的新尺寸
            new_width = window_width
            new_height = int(new_width / screen_ratio)
            
            # 如果按宽度计算的高度超过窗口高度，则按高度计算
            if new_height > window_height:
                new_height = window_height
                new_width = int(new_height * screen_ratio)
            
            # 重新调整画布尺寸
            canvas.config(width=new_width, height=new_height)
            
            # 重新缩放并显示图像
            try:
                resized_screen = screen.resize((new_width, new_height), Image.Resampling.LANCZOS)
                new_img = ImageTk.PhotoImage(resized_screen)
                canvas.delete("all")  # 清除画布
                canvas.create_image(0, 0, anchor=tk.NW, image=new_img)
                canvas.image = new_img  # 保持引用
                
                # 重新显示操作提示
                canvas.create_text(new_width//2, 30, text="拖动鼠标选择要监听的区域，按ESC取消", 
                                 fill="white", font=("Arial", 14), anchor=tk.CENTER)
                
                log_message(f"窗口缩放: {window_width}x{window_height}, 截图调整: {new_width}x{new_height}")
            except Exception as e:
                log_message(f"窗口缩放时调整图像出错: {str(e)}")
        
        # 绑定窗口缩放事件
        capture_dialog.bind("<Configure>", on_window_resize)
        log_message("截图窗口创建完成")
        
        # 框选变量
        start_x = start_y = end_x = end_y = 0
        rect_id = None
        selection_made = False
        
        # 添加操作提示
        info_text = canvas.create_text(screen.width//2, 30, text="拖动鼠标选择要监听的区域，按ESC取消", 
                                     fill="white", font=("Arial", 14), anchor=tk.CENTER)
        
        def on_mouse_down(event):
            nonlocal start_x, start_y, rect_id
            if selection_made:
                log_message("鼠标按下事件被忽略，因为选择已完成")
                return
            start_x, start_y = event.x, event.y
            log_message(f"鼠标按下，起始坐标: ({start_x}, {start_y})")
            # 创建矩形
            rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                            outline="red", width=3, fill="", dash=(5, 5))
            # 移除提示文字
            canvas.delete(info_text)
            log_message("提示文字已移除")
        
        def on_mouse_move(event):
            nonlocal end_x, end_y, rect_id
            if rect_id and not selection_made:
                end_x, end_y = event.x, event.y
                canvas.coords(rect_id, start_x, start_y, end_x, end_y)
                log_message(f"鼠标移动，当前坐标: ({end_x}, {end_y})")
                
                # 检查框选是否结束（鼠标移动停止一段时间）
                check_selection_complete()
        
        # 用于检测框选结束的变量
        last_move_time = time.time()
        selection_complete_timer = None
        
        def check_selection_complete():
            """检查框选是否完成（鼠标停止移动一段时间）"""
            nonlocal last_move_time, selection_complete_timer
            
            # 取消之前的定时器
            if selection_complete_timer:
                capture_dialog.after_cancel(selection_complete_timer)
            
            # 更新最后移动时间
            last_move_time = time.time()
            
            # 设置新的定时器，300毫秒后检查是否停止移动
            selection_complete_timer = capture_dialog.after(300, confirm_if_stopped)
        
        def confirm_if_stopped():
            """如果鼠标停止移动，确认选择"""
            nonlocal selection_made
            
            # 检查是否在最近300毫秒内没有移动
            if time.time() - last_move_time >= 0.3 and rect_id and not selection_made:
                log_message("检测到鼠标停止移动，自动确认选择")
                selection_made = True
                save_selection()
        
        def save_selection():
            """保存选择的区域"""
            nonlocal selection_made
            
            # 获取当前画布尺寸和缩放比例
            current_canvas_width = canvas.winfo_width()
            current_canvas_height = canvas.winfo_height()
            scale_x = original_screen_size[0] / current_canvas_width if current_canvas_width > 0 else 1
            scale_y = original_screen_size[1] / current_canvas_height if current_canvas_height > 0 else 1
            
            # 将画布坐标转换为原始截图坐标
            left = min(start_x, end_x) * scale_x
            top = min(start_y, end_y) * scale_y
            right = max(start_x, end_x) * scale_x
            bottom = max(start_y, end_y) * scale_y
            
            log_message(f"画布尺寸: {current_canvas_width}x{current_canvas_height}")
            log_message(f"缩放比例: X={scale_x:.3f}, Y={scale_y:.3f}")
            log_message(f"原始坐标: ({min(start_x, end_x)}, {min(start_y, end_y)}) - ({max(start_x, end_x)}, {max(start_y, end_y)})")
            log_message(f"转换后坐标: ({int(left)}, {int(top)}) - ({int(right)}, {int(bottom)})")
            
            # 确保框选区域有效
            if right > left and bottom > top:
                log_message("框选区域有效，开始保存图片")
                # 直接保存裁剪后的图片
                import time
                timestamp = int(time.time())
                file_name = f"screenshot_{timestamp}.png"
                dest_path = os.path.join(image_dir, file_name)
                log_message(f"准备保存到: {dest_path}")
                
                # 裁剪图像并保存
                try:
                    crop_img = screen.crop((int(left), int(top), int(right), int(bottom)))
                    log_message(f"图片裁剪完成，尺寸: {crop_img.width}x{crop_img.height}")
                    crop_img.save(dest_path)
                    log_message("图片保存成功")
                    
                    # 更新路径变量
                    if image_var:
                        image_var.set(dest_path)
                        log_message(f"路径变量已更新: {dest_path}")
                    else:
                        log_message("image_var 为 None，跳过路径更新")
                    
                    # 关闭窗口
                    log_message("准备关闭截图窗口")
                    capture_dialog.destroy()
                    log_message("截图窗口已关闭")
                except Exception as e:
                    log_message(f"保存图片时出错: {str(e)}")
            else:
                log_message("框选区域无效，重新开始")
                # 无效区域，重新开始
                selection_made = False
                canvas.delete(rect_id)
                rect_id = None
                log_message("已重置选择状态")
        
        def on_mouse_up(event):
            """鼠标释放事件 - 现在主要用于调试"""
            nonlocal end_x, end_y
            log_message(f"鼠标释放事件触发，坐标: ({event.x}, {event.y})")
            
            # 更新结束坐标，但不立即保存
            if rect_id and not selection_made:
                end_x, end_y = event.x, event.y
                log_message(f"更新结束坐标: ({end_x}, {end_y})")
                
                # 立即触发保存检查（因为鼠标已经释放）
                capture_dialog.after(100, save_selection)
        

        
        def on_key_press(event):
            if event.keysym == "Escape":
                capture_dialog.destroy()
        
        # 延迟绑定事件，确保窗口完全显示
        def bind_events():
            log_message("开始绑定事件")
            log_message(f"画布尺寸: {canvas.winfo_width()}x{canvas.winfo_height()}")
            log_message(f"窗口尺寸: {capture_dialog.winfo_width()}x{capture_dialog.winfo_height()}")
            
            # 绑定事件 - 尝试多种绑定方式
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            
            # 同时绑定到窗口和画布，确保能捕获事件
            capture_dialog.bind("<ButtonRelease-1>", on_mouse_up)
            capture_dialog.bind("<Key>", on_key_press)
            
            # 确保画布能够接收事件
            canvas.focus_set()
            capture_dialog.focus_set()
            
            log_message("事件绑定完成，开始等待用户操作")
        
        # 延迟100毫秒后绑定事件
        capture_dialog.after(100, bind_events)

    def init_auto_click_ui(self):
        # 任务列表
        self.auto_click_tree = ttk.Treeview(self.auto_click_frame, columns=("name", "status"), show="headings")
        self.auto_click_tree.heading("name", text="任务名称")
        self.auto_click_tree.heading("status", text="状态")
        self.auto_click_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(self.auto_click_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_btn = ttk.Button(button_frame, text="添加任务", command=self.add_auto_click_task)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        edit_btn = ttk.Button(button_frame, text="编辑任务", command=self.edit_auto_click_task)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        start_btn = ttk.Button(button_frame, text="启动任务", command=self.start_auto_click_task)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        pause_btn = ttk.Button(button_frame, text="暂停任务", command=self.pause_auto_click_task)
        pause_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ttk.Button(button_frame, text="移除任务", command=self.remove_auto_click_task)
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出导入按钮
        export_btn = ttk.Button(button_frame, text="导出配置", command=self.export_auto_click_config)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        import_btn = ttk.Button(button_frame, text="导入配置", command=self.import_auto_click_config)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 系统信息按钮
        info_btn = ttk.Button(button_frame, text="系统信息", command=self.show_system_info)
        info_btn.pack(side=tk.LEFT, padx=5)
        
        # 截图测试按钮
        test_screenshot_btn = ttk.Button(button_frame, text="测试截图", command=self.test_screenshot)
        test_screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        # 监听频率设置
        freq_frame = ttk.Frame(self.auto_click_frame)
        freq_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(freq_frame, text="屏幕监听频率(秒):").pack(side=tk.LEFT, padx=5)
        self.freq_var = tk.StringVar(value="30")
        ttk.Entry(freq_frame, textvariable=self.freq_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(freq_frame, text="保存", command=self.save_freq).pack(side=tk.LEFT, padx=5)
        
        # 日志和截图区域
        log_frame = ttk.LabelFrame(self.auto_click_frame, text="日志和截图")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧日志区域
        log_text_frame = ttk.Frame(log_frame, width=800)
        log_text_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        log_text_frame.pack_propagate(False)  # 防止子组件影响大小
        
        ttk.Label(log_text_frame, text="操作日志:").pack(anchor=tk.W, padx=5, pady=5)
        self.log_text = tk.Text(log_text_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧截图区域
        screenshot_frame = ttk.Frame(log_frame, width=600, height=400)
        screenshot_frame.pack(side=tk.RIGHT, fill=tk.NONE, padx=5)
        screenshot_frame.pack_propagate(False)  # 防止子组件影响大小
        
        tk.Label(screenshot_frame, text="最新截图:").pack(anchor=tk.W, padx=5, pady=5)
        self.screenshot_label = tk.Label(screenshot_frame, relief=tk.SUNKEN)
        self.screenshot_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 刷新任务列表
        self.refresh_auto_click_list()
        
        # 启动日志和截图更新线程
        threading.Thread(target=self.update_log_and_screenshot, daemon=True).start()
    
    def add_schedule_task(self):
        # 打开添加任务对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加定时任务")
        dialog.geometry("400x450")  # 增加高度
        
        ttk.Label(dialog, text="任务名称:").pack(padx=10, pady=10)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="URL:").pack(padx=10, pady=10)
        url_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=url_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="执行时间(HH:MM):").pack(padx=10, pady=10)
        time_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=time_var).pack(padx=10, pady=5, fill=tk.X)
        
        def save():
            name = name_var.get()
            url = url_var.get()
            time_str = time_var.get()
            if name and url and time_str:
                self.schedule_manager.add_task(name, url, time_str)
                self.refresh_schedule_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save).pack(padx=10, pady=20)
    
    def edit_schedule_task(self):
        # 打开编辑任务对话框
        selected = self.schedule_tree.selection()
        if not selected:
            return
        
        task_id = selected[0]
        task = self.schedule_manager.tasks.get(task_id)
        if not task:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑定时任务")
        dialog.geometry("400x450")  # 增加高度
        
        ttk.Label(dialog, text="任务名称:").pack(padx=10, pady=10)
        name_var = tk.StringVar(value=task["name"])
        ttk.Entry(dialog, textvariable=name_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="URL:").pack(padx=10, pady=10)
        url_var = tk.StringVar(value=task["url"])
        ttk.Entry(dialog, textvariable=url_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="执行时间(HH:MM):").pack(padx=10, pady=10)
        time_var = tk.StringVar(value=task["time"])
        ttk.Entry(dialog, textvariable=time_var).pack(padx=10, pady=5, fill=tk.X)
        
        def save():
            name = name_var.get()
            url = url_var.get()
            time_str = time_var.get()
            if name and url and time_str:
                # 更新任务
                task["name"] = name
                task["url"] = url
                task["time"] = time_str
                self.schedule_manager.save_tasks()
                self.refresh_schedule_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save).pack(padx=10, pady=20)
    
    def start_schedule_task(self):
        selected = self.schedule_tree.selection()
        if selected:
            task_id = selected[0]
            self.schedule_manager.start_task(task_id)
            self.refresh_schedule_list()
    
    def pause_schedule_task(self):
        selected = self.schedule_tree.selection()
        if selected:
            task_id = selected[0]
            self.schedule_manager.pause_task(task_id)
            self.refresh_schedule_list()
    
    def remove_schedule_task(self):
        selected = self.schedule_tree.selection()
        if selected:
            task_id = selected[0]
            self.schedule_manager.remove_task(task_id)
            self.refresh_schedule_list()
    
    def add_auto_click_task(self):
        # 打开添加任务对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加自动化点击任务")
        dialog.geometry("800x760")
        
        # 任务基本信息
        basic_frame = ttk.Frame(dialog)
        basic_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(basic_frame, text="任务名称:").pack(padx=10, pady=5, anchor=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=name_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(basic_frame, text="截图路径:").pack(padx=10, pady=5, anchor=tk.W)
        image_var = tk.StringVar()
        path_frame = ttk.Frame(basic_frame)
        path_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Entry(path_frame, textvariable=image_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def upload_image():
            # 创建data/images目录
            image_dir = os.path.join(os.getcwd(), "data", "images")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择截图",
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")]
            )
            
            if file_path:
                # 复制文件到data/images目录
                import shutil
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(image_dir, file_name)
                shutil.copyfile(file_path, dest_path)
                
                # 更新路径变量
                image_var.set(dest_path)
        

        
        ttk.Button(path_frame, text="上传截图", command=upload_image).pack(side=tk.RIGHT, padx=5)
        ttk.Button(path_frame, text="手动截图", command=lambda: self.capture_screen(image_var)).pack(side=tk.RIGHT, padx=5)
        
        # 操作清单
        actions_frame = ttk.Frame(dialog)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(actions_frame, text="操作清单:").pack(padx=10, pady=5, anchor=tk.W)
        
        # 操作列表
        action_tree = ttk.Treeview(actions_frame, columns=("type", "detail"), show="headings")
        action_tree.heading("type", text="操作类型")
        action_tree.heading("detail", text="操作详情")
        action_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 操作按钮
        action_buttons = ttk.Frame(actions_frame)
        action_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        # 操作列表数据
        actions = []
        
        def update_action_list():
            # 清空列表
            for item in action_tree.get_children():
                action_tree.delete(item)
            
            # 添加操作
            for i, action in enumerate(actions):
                action_type = ""
                detail = ""
                
                if action["type"] == "click_screen":
                    action_type = "鼠标点击屏幕指定位置"
                    detail = f"X: {action['x']}, Y: {action['y']}"
                elif action["type"] == "click_match":
                    action_type = "鼠标点击命中截图位置"
                    detail = f"X偏移: {action['offset_x']}, Y偏移: {action['offset_y']}"
                elif action["type"] == "keyboard":
                    action_type = "键盘输入"
                    detail = action['text']
                elif action["type"] == "delay":
                    action_type = "延迟等待"
                    detail = f"{action['seconds']}秒"
                
                action_tree.insert("", tk.END, id=i, values=(action_type, detail))
        
        def add_action():
            action_dialog = tk.Toplevel(dialog)
            action_dialog.title("添加操作")
            action_dialog.geometry("450x500")
            
            ttk.Label(action_dialog, text="操作类型:").pack(padx=10, pady=5)
            action_type = tk.StringVar()
            combo = ttk.Combobox(action_dialog, textvariable=action_type, values=["鼠标点击屏幕指定位置", "鼠标点击命中截图位置", "键盘输入", "延迟等待"])
            combo.pack(padx=10, pady=5, fill=tk.X)
            
            # 详细信息
            detail_frame = ttk.Frame(action_dialog)
            detail_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(detail_frame, text="详细信息:").pack(anchor=tk.W)
            
            # 根据操作类型显示不同的输入项
            def update_detail_fields(event):
                for widget in detail_frame.winfo_children():
                    if widget != detail_frame.winfo_children()[0]:
                        widget.destroy()
                
                if action_type.get() == "鼠标点击屏幕指定位置":
                    ttk.Label(detail_frame, text="X坐标:").pack(anchor=tk.W)
                    x_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=x_var).pack(fill=tk.X)
                    
                    ttk.Label(detail_frame, text="Y坐标:").pack(anchor=tk.W)
                    y_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=y_var).pack(fill=tk.X)
                    
                    def select_screen_position():
                        # 截取屏幕
                        from PIL import ImageGrab
                        screen = ImageGrab.grab()
                        
                        # 创建坐标选择窗口
                        select_dialog = tk.Toplevel(action_dialog)
                        select_dialog.title("选择屏幕位置")
                        select_dialog.attributes("-fullscreen", True)
                        select_dialog.attributes("-topmost", True)
                        
                        # 显示截图
                        from PIL import ImageTk
                        img = ImageTk.PhotoImage(screen)
                        label = tk.Label(select_dialog, image=img)
                        label.image = img
                        label.pack(fill=tk.BOTH, expand=True)
                        
                        # 显示坐标
                        coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                        coord_label.place(x=10, y=10)
                        
                        def on_mouse_move(event):
                            coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                        
                        def on_mouse_click(event):
                            x_var.set(str(event.x))
                            y_var.set(str(event.y))
                            select_dialog.destroy()
                        
                        label.bind("<Motion>", on_mouse_move)
                        label.bind("<Button-1>", on_mouse_click)
                    
                    ttk.Button(detail_frame, text="手动选取", command=select_screen_position).pack(pady=5)
                    
                    def save_action():
                        action = {
                            "type": "click_screen",
                            "x": int(x_var.get()),
                            "y": int(y_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "鼠标点击命中截图位置":
                    ttk.Label(detail_frame, text="X偏移:").pack(anchor=tk.W)
                    offset_x_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=offset_x_var).pack(fill=tk.X)
                    
                    ttk.Label(detail_frame, text="Y偏移:").pack(anchor=tk.W)
                    offset_y_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=offset_y_var).pack(fill=tk.X)
                    
                    def select_match_position():
                        # 加载任务截图
                        image_path = image_var.get()
                        if not os.path.exists(image_path):
                            return
                        
                        from PIL import Image
                        img = Image.open(image_path)
                        
                        # 创建坐标选择窗口
                        select_dialog = tk.Toplevel(action_dialog)
                        select_dialog.title("选择截图位置")
                        
                        # 显示截图
                        from PIL import ImageTk
                        photo = ImageTk.PhotoImage(img)
                        label = tk.Label(select_dialog, image=photo)
                        label.image = photo
                        label.pack()
                        
                        # 显示坐标
                        coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                        coord_label.pack(pady=5)
                        
                        def on_mouse_move(event):
                            coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                        
                        def on_mouse_click(event):
                            offset_x_var.set(str(event.x))
                            offset_y_var.set(str(event.y))
                            select_dialog.destroy()
                        
                        label.bind("<Motion>", on_mouse_move)
                        label.bind("<Button-1>", on_mouse_click)
                    
                    ttk.Button(detail_frame, text="手动选取", command=select_match_position).pack(pady=5)
                    
                    def save_action():
                        action = {
                            "type": "click_match",
                            "offset_x": int(offset_x_var.get()),
                            "offset_y": int(offset_y_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "键盘输入":
                    ttk.Label(detail_frame, text="输入内容:").pack(anchor=tk.W)
                    text_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=text_var).pack(fill=tk.X)
                    
                    def save_action():
                        action = {
                            "type": "keyboard",
                            "text": text_var.get()
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "延迟等待":
                    ttk.Label(detail_frame, text="等待时间(秒):").pack(anchor=tk.W)
                    seconds_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=seconds_var).pack(fill=tk.X)
                    
                    def save_action():
                        action = {
                            "type": "delay",
                            "seconds": float(seconds_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
            
            combo.bind("<<ComboboxSelected>>", update_detail_fields)
        
        def edit_action():
            selected = action_tree.selection()
            if not selected:
                return
            
            action_index = int(selected[0])
            if action_index < len(actions):
                action = actions[action_index]
                
                action_dialog = tk.Toplevel(dialog)
                action_dialog.title("编辑操作")
                action_dialog.geometry("450x500")
                
                ttk.Label(action_dialog, text="操作类型:").pack(padx=10, pady=5)
                action_type = tk.StringVar()
                combo = ttk.Combobox(action_dialog, textvariable=action_type, values=["鼠标点击屏幕指定位置", "鼠标点击命中截图位置", "键盘输入", "延迟等待"])
                
                # 设置当前操作类型
                if action["type"] == "click_screen":
                    action_type.set("鼠标点击屏幕指定位置")
                elif action["type"] == "click_match":
                    action_type.set("鼠标点击命中截图位置")
                elif action["type"] == "keyboard":
                    action_type.set("键盘输入")
                elif action["type"] == "delay":
                    action_type.set("延迟等待")
                
                combo.pack(padx=10, pady=5, fill=tk.X)
                
                # 详细信息
                detail_frame = ttk.Frame(action_dialog)
                detail_frame.pack(fill=tk.X, padx=10, pady=10)
                
                ttk.Label(detail_frame, text="详细信息:").pack(anchor=tk.W)
                
                # 根据操作类型显示不同的输入项
                def update_detail_fields(event):
                    for widget in detail_frame.winfo_children():
                        if widget != detail_frame.winfo_children()[0]:
                            widget.destroy()
                    
                    if action_type.get() == "鼠标点击屏幕指定位置":
                        ttk.Label(detail_frame, text="X坐标:").pack(anchor=tk.W)
                        x_var = tk.StringVar(value=str(action.get("x", 0)))
                        ttk.Entry(detail_frame, textvariable=x_var).pack(fill=tk.X)
                        
                        ttk.Label(detail_frame, text="Y坐标:").pack(anchor=tk.W)
                        y_var = tk.StringVar(value=str(action.get("y", 0)))
                        ttk.Entry(detail_frame, textvariable=y_var).pack(fill=tk.X)
                        
                        def select_screen_position():
                            # 截取屏幕
                            from PIL import ImageGrab
                            screen = ImageGrab.grab()
                            
                            # 创建坐标选择窗口
                            select_dialog = tk.Toplevel(action_dialog)
                            select_dialog.title("选择屏幕位置")
                            select_dialog.attributes("-fullscreen", True)
                            select_dialog.attributes("-topmost", True)
                            
                            # 显示截图
                            from PIL import ImageTk
                            img = ImageTk.PhotoImage(screen)
                            label = tk.Label(select_dialog, image=img)
                            label.image = img
                            label.pack(fill=tk.BOTH, expand=True)
                            
                            # 显示坐标
                            coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                            coord_label.place(x=10, y=10)
                            
                            def on_mouse_move(event):
                                coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                            
                            def on_mouse_click(event):
                                x_var.set(str(event.x))
                                y_var.set(str(event.y))
                                select_dialog.destroy()
                            
                            label.bind("<Motion>", on_mouse_move)
                            label.bind("<Button-1>", on_mouse_click)
                        
                        ttk.Button(detail_frame, text="手动选取", command=select_screen_position).pack(pady=5)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "click_screen",
                                "x": int(x_var.get()),
                                "y": int(y_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "鼠标点击命中截图位置":
                        ttk.Label(detail_frame, text="X偏移:").pack(anchor=tk.W)
                        offset_x_var = tk.StringVar(value=str(action.get("offset_x", 0)))
                        ttk.Entry(detail_frame, textvariable=offset_x_var).pack(fill=tk.X)
                        
                        ttk.Label(detail_frame, text="Y偏移:").pack(anchor=tk.W)
                        offset_y_var = tk.StringVar(value=str(action.get("offset_y", 0)))
                        ttk.Entry(detail_frame, textvariable=offset_y_var).pack(fill=tk.X)
                        
                        def select_match_position():
                            # 加载任务截图
                            image_path = image_var.get()
                            if not os.path.exists(image_path):
                                return
                            
                            from PIL import Image
                            img = Image.open(image_path)
                            
                            # 创建坐标选择窗口
                            select_dialog = tk.Toplevel(action_dialog)
                            select_dialog.title("选择截图位置")
                            
                            # 显示截图
                            from PIL import ImageTk
                            photo = ImageTk.PhotoImage(img)
                            label = tk.Label(select_dialog, image=photo)
                            label.image = photo
                            label.pack()
                            
                            # 显示坐标
                            coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                            coord_label.pack(pady=5)
                            
                            def on_mouse_move(event):
                                coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                            
                            def on_mouse_click(event):
                                offset_x_var.set(str(event.x))
                                offset_y_var.set(str(event.y))
                                select_dialog.destroy()
                            
                            label.bind("<Motion>", on_mouse_move)
                            label.bind("<Button-1>", on_mouse_click)
                        
                        ttk.Button(detail_frame, text="手动选取", command=select_match_position).pack(pady=5)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "click_match",
                                "offset_x": int(offset_x_var.get()),
                                "offset_y": int(offset_y_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "键盘输入":
                        ttk.Label(detail_frame, text="输入内容:").pack(anchor=tk.W)
                        text_var = tk.StringVar(value=action.get("text", ""))
                        ttk.Entry(detail_frame, textvariable=text_var).pack(fill=tk.X)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "keyboard",
                                "text": text_var.get()
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "延迟等待":
                        ttk.Label(detail_frame, text="等待时间(秒):").pack(anchor=tk.W)
                        seconds_var = tk.StringVar(value=str(action.get("seconds", 1)))
                        ttk.Entry(detail_frame, textvariable=seconds_var).pack(fill=tk.X)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "delay",
                                "seconds": float(seconds_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                combo.bind("<<ComboboxSelected>>", update_detail_fields)
                # 初始显示
                update_detail_fields(None)
        
        def remove_action():
            selected = action_tree.selection()
            if not selected:
                return
            
            action_index = int(selected[0])
            if action_index < len(actions):
                del actions[action_index]
                update_action_list()
        
        add_action_btn = ttk.Button(action_buttons, text="添加操作", command=add_action)
        add_action_btn.pack(side=tk.LEFT, padx=5)
        
        edit_action_btn = ttk.Button(action_buttons, text="编辑操作", command=edit_action)
        edit_action_btn.pack(side=tk.LEFT, padx=5)
        
        remove_action_btn = ttk.Button(action_buttons, text="删除操作", command=remove_action)
        remove_action_btn.pack(side=tk.LEFT, padx=5)
        
        def save():
            name = name_var.get()
            image_path = image_var.get()
            if name and image_path:
                self.auto_click_manager.add_task(name, image_path, actions)
                self.refresh_auto_click_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save).pack(padx=10, pady=20)
    
    def edit_auto_click_task(self):
        # 检查是否选中了任务
        selected = self.auto_click_tree.selection()
        if not selected:
            return
        
        task_id = selected[0]
        if task_id not in self.auto_click_manager.tasks:
            return
        
        task = self.auto_click_manager.tasks[task_id]
        
        # 打开编辑任务对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑自动化点击任务")
        dialog.geometry("800x700")
        
        # 任务基本信息
        basic_frame = ttk.Frame(dialog)
        basic_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(basic_frame, text="任务名称:").pack(padx=10, pady=5, anchor=tk.W)
        name_var = tk.StringVar(value=task["name"])
        ttk.Entry(basic_frame, textvariable=name_var).pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(basic_frame, text="截图路径:").pack(padx=10, pady=5, anchor=tk.W)
        image_var = tk.StringVar(value=task["image_path"])
        path_frame = ttk.Frame(basic_frame)
        path_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Entry(path_frame, textvariable=image_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def upload_image():
            # 创建data/images目录
            image_dir = os.path.join(os.getcwd(), "data", "images")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择截图",
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")]
            )
            
            if file_path:
                # 复制文件到data/images目录
                import shutil
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(image_dir, file_name)
                shutil.copyfile(file_path, dest_path)
                
                # 更新路径变量
                image_var.set(dest_path)
        

        
        ttk.Button(path_frame, text="上传截图", command=upload_image).pack(side=tk.RIGHT, padx=5)
        ttk.Button(path_frame, text="手动截图", command=lambda: self.capture_screen(image_var)).pack(side=tk.RIGHT, padx=5)
        
        # 操作清单
        actions_frame = ttk.Frame(dialog)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(actions_frame, text="操作清单:").pack(padx=10, pady=5, anchor=tk.W)
        
        # 操作列表
        action_tree = ttk.Treeview(actions_frame, columns=("type", "detail"), show="headings")
        action_tree.heading("type", text="操作类型")
        action_tree.heading("detail", text="操作详情")
        action_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 操作按钮
        action_buttons = ttk.Frame(actions_frame)
        action_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        # 操作列表数据（复制当前任务的操作清单）
        actions = task["actions"].copy()
        
        def update_action_list():
            # 清空列表
            for item in action_tree.get_children():
                action_tree.delete(item)
            
            # 添加操作
            for i, action in enumerate(actions):
                action_type = ""
                detail = ""
                
                if action["type"] == "click_screen":
                    action_type = "鼠标点击屏幕指定位置"
                    detail = f"X: {action['x']}, Y: {action['y']}"
                elif action["type"] == "click_match":
                    action_type = "鼠标点击命中截图位置"
                    detail = f"X偏移: {action['offset_x']}, Y偏移: {action['offset_y']}"
                elif action["type"] == "keyboard":
                    action_type = "键盘输入"
                    detail = action['text']
                elif action["type"] == "delay":
                    action_type = "延迟等待"
                    detail = f"{action['seconds']}秒"
                
                action_tree.insert("", tk.END, id=i, values=(action_type, detail))
        
        # 初始化操作列表
        update_action_list()
        
        def add_action():
            action_dialog = tk.Toplevel(dialog)
            action_dialog.title("添加操作")
            action_dialog.geometry("400x300")
            
            ttk.Label(action_dialog, text="操作类型:").pack(padx=10, pady=5)
            action_type = tk.StringVar()
            combo = ttk.Combobox(action_dialog, textvariable=action_type, values=["鼠标点击屏幕指定位置", "鼠标点击命中截图位置", "键盘输入", "延迟等待"])
            combo.pack(padx=10, pady=5, fill=tk.X)
            
            # 详细信息
            detail_frame = ttk.Frame(action_dialog)
            detail_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(detail_frame, text="详细信息:").pack(anchor=tk.W)
            
            # 根据操作类型显示不同的输入项
            def update_detail_fields(event):
                for widget in detail_frame.winfo_children():
                    if widget != detail_frame.winfo_children()[0]:
                        widget.destroy()
                
                if action_type.get() == "鼠标点击屏幕指定位置":
                    ttk.Label(detail_frame, text="X坐标:").pack(anchor=tk.W)
                    x_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=x_var).pack(fill=tk.X)
                    
                    ttk.Label(detail_frame, text="Y坐标:").pack(anchor=tk.W)
                    y_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=y_var).pack(fill=tk.X)
                    
                    def select_screen_position():
                        # 截取屏幕
                        from PIL import ImageGrab
                        screen = ImageGrab.grab()
                        
                        # 创建坐标选择窗口
                        select_dialog = tk.Toplevel(action_dialog)
                        select_dialog.title("选择屏幕位置")
                        select_dialog.attributes("-fullscreen", True)
                        select_dialog.attributes("-topmost", True)
                        
                        # 显示截图
                        from PIL import ImageTk
                        img = ImageTk.PhotoImage(screen)
                        label = tk.Label(select_dialog, image=img)
                        label.image = img
                        label.pack(fill=tk.BOTH, expand=True)
                        
                        # 显示坐标
                        coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                        coord_label.place(x=10, y=10)
                        
                        def on_mouse_move(event):
                            coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                        
                        def on_mouse_click(event):
                            x_var.set(str(event.x))
                            y_var.set(str(event.y))
                            select_dialog.destroy()
                        
                        label.bind("<Motion>", on_mouse_move)
                        label.bind("<Button-1>", on_mouse_click)
                    
                    ttk.Button(detail_frame, text="手动选取", command=select_screen_position).pack(pady=5)
                    
                    def save_action():
                        action = {
                            "type": "click_screen",
                            "x": int(x_var.get()),
                            "y": int(y_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "鼠标点击命中截图位置":
                    ttk.Label(detail_frame, text="X偏移:").pack(anchor=tk.W)
                    offset_x_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=offset_x_var).pack(fill=tk.X)
                    
                    ttk.Label(detail_frame, text="Y偏移:").pack(anchor=tk.W)
                    offset_y_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=offset_y_var).pack(fill=tk.X)
                    
                    def select_match_position():
                        # 加载任务截图
                        image_path = image_var.get()
                        if not os.path.exists(image_path):
                            return
                        
                        from PIL import Image
                        img = Image.open(image_path)
                        
                        # 创建坐标选择窗口
                        select_dialog = tk.Toplevel(action_dialog)
                        select_dialog.title("选择截图位置")
                        
                        # 显示截图
                        from PIL import ImageTk
                        photo = ImageTk.PhotoImage(img)
                        label = tk.Label(select_dialog, image=photo)
                        label.image = photo
                        label.pack()
                        
                        # 显示坐标
                        coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                        coord_label.pack(pady=5)
                        
                        def on_mouse_move(event):
                            coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                        
                        def on_mouse_click(event):
                            offset_x_var.set(str(event.x))
                            offset_y_var.set(str(event.y))
                            select_dialog.destroy()
                        
                        label.bind("<Motion>", on_mouse_move)
                        label.bind("<Button-1>", on_mouse_click)
                    
                    ttk.Button(detail_frame, text="手动选取", command=select_match_position).pack(pady=5)
                    
                    def save_action():
                        action = {
                            "type": "click_match",
                            "offset_x": int(offset_x_var.get()),
                            "offset_y": int(offset_y_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "键盘输入":
                    ttk.Label(detail_frame, text="输入内容:").pack(anchor=tk.W)
                    text_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=text_var).pack(fill=tk.X)
                    
                    def save_action():
                        action = {
                            "type": "keyboard",
                            "text": text_var.get()
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                elif action_type.get() == "延迟等待":
                    ttk.Label(detail_frame, text="等待时间(秒):").pack(anchor=tk.W)
                    seconds_var = tk.StringVar()
                    ttk.Entry(detail_frame, textvariable=seconds_var).pack(fill=tk.X)
                    
                    def save_action():
                        action = {
                            "type": "delay",
                            "seconds": float(seconds_var.get())
                        }
                        actions.append(action)
                        update_action_list()
                        action_dialog.destroy()
                    
                    ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
            
            combo.bind("<<ComboboxSelected>>", update_detail_fields)
        
        def edit_action():
            selected = action_tree.selection()
            if not selected:
                return
            
            action_index = int(selected[0])
            if action_index < len(actions):
                action = actions[action_index]
                
                action_dialog = tk.Toplevel(dialog)
                action_dialog.title("编辑操作")
                action_dialog.geometry("400x300")
                
                ttk.Label(action_dialog, text="操作类型:").pack(padx=10, pady=5)
                action_type = tk.StringVar()
                combo = ttk.Combobox(action_dialog, textvariable=action_type, values=["鼠标点击屏幕指定位置", "鼠标点击命中截图位置", "键盘输入", "延迟等待"])
                
                # 设置当前操作类型
                if action["type"] == "click_screen":
                    action_type.set("鼠标点击屏幕指定位置")
                elif action["type"] == "click_match":
                    action_type.set("鼠标点击命中截图位置")
                elif action["type"] == "keyboard":
                    action_type.set("键盘输入")
                elif action["type"] == "delay":
                    action_type.set("延迟等待")
                
                combo.pack(padx=10, pady=5, fill=tk.X)
                
                # 详细信息
                detail_frame = ttk.Frame(action_dialog)
                detail_frame.pack(fill=tk.X, padx=10, pady=10)
                
                ttk.Label(detail_frame, text="详细信息:").pack(anchor=tk.W)
                
                # 根据操作类型显示不同的输入项
                def update_detail_fields(event):
                    for widget in detail_frame.winfo_children():
                        if widget != detail_frame.winfo_children()[0]:
                            widget.destroy()
                    
                    if action_type.get() == "鼠标点击屏幕指定位置":
                        ttk.Label(detail_frame, text="X坐标:").pack(anchor=tk.W)
                        x_var = tk.StringVar(value=str(action.get("x", 0)))
                        ttk.Entry(detail_frame, textvariable=x_var).pack(fill=tk.X)
                        
                        ttk.Label(detail_frame, text="Y坐标:").pack(anchor=tk.W)
                        y_var = tk.StringVar(value=str(action.get("y", 0)))
                        ttk.Entry(detail_frame, textvariable=y_var).pack(fill=tk.X)
                        
                        def select_screen_position():
                            # 截取屏幕
                            from PIL import ImageGrab
                            screen = ImageGrab.grab()
                            
                            # 创建坐标选择窗口
                            select_dialog = tk.Toplevel(action_dialog)
                            select_dialog.title("选择屏幕位置")
                            select_dialog.attributes("-fullscreen", True)
                            select_dialog.attributes("-topmost", True)
                            
                            # 显示截图
                            from PIL import ImageTk
                            img = ImageTk.PhotoImage(screen)
                            label = tk.Label(select_dialog, image=img)
                            label.image = img
                            label.pack(fill=tk.BOTH, expand=True)
                            
                            # 显示坐标
                            coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                            coord_label.place(x=10, y=10)
                            
                            def on_mouse_move(event):
                                coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                            
                            def on_mouse_click(event):
                                x_var.set(str(event.x))
                                y_var.set(str(event.y))
                                select_dialog.destroy()
                            
                            label.bind("<Motion>", on_mouse_move)
                            label.bind("<Button-1>", on_mouse_click)
                        
                        ttk.Button(detail_frame, text="手动选取", command=select_screen_position).pack(pady=5)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "click_screen",
                                "x": int(x_var.get()),
                                "y": int(y_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "鼠标点击命中截图位置":
                        ttk.Label(detail_frame, text="X偏移:").pack(anchor=tk.W)
                        offset_x_var = tk.StringVar(value=str(action.get("offset_x", 0)))
                        ttk.Entry(detail_frame, textvariable=offset_x_var).pack(fill=tk.X)
                        
                        ttk.Label(detail_frame, text="Y偏移:").pack(anchor=tk.W)
                        offset_y_var = tk.StringVar(value=str(action.get("offset_y", 0)))
                        ttk.Entry(detail_frame, textvariable=offset_y_var).pack(fill=tk.X)
                        
                        def select_match_position():
                            # 加载任务截图
                            image_path = image_var.get()
                            if not os.path.exists(image_path):
                                return
                            
                            from PIL import Image
                            img = Image.open(image_path)
                            
                            # 创建坐标选择窗口
                            select_dialog = tk.Toplevel(action_dialog)
                            select_dialog.title("选择截图位置")
                            
                            # 显示截图
                            from PIL import ImageTk
                            photo = ImageTk.PhotoImage(img)
                            label = tk.Label(select_dialog, image=photo)
                            label.image = photo
                            label.pack()
                            
                            # 显示坐标
                            coord_label = tk.Label(select_dialog, text="X: 0, Y: 0", bg="white", fg="black")
                            coord_label.pack(pady=5)
                            
                            def on_mouse_move(event):
                                coord_label.config(text=f"X: {event.x}, Y: {event.y}")
                            
                            def on_mouse_click(event):
                                offset_x_var.set(str(event.x))
                                offset_y_var.set(str(event.y))
                                select_dialog.destroy()
                            
                            label.bind("<Motion>", on_mouse_move)
                            label.bind("<Button-1>", on_mouse_click)
                        
                        ttk.Button(detail_frame, text="手动选取", command=select_match_position).pack(pady=5)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "click_match",
                                "offset_x": int(offset_x_var.get()),
                                "offset_y": int(offset_y_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "键盘输入":
                        ttk.Label(detail_frame, text="输入内容:").pack(anchor=tk.W)
                        text_var = tk.StringVar(value=action.get("text", ""))
                        ttk.Entry(detail_frame, textvariable=text_var).pack(fill=tk.X)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "keyboard",
                                "text": text_var.get()
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                    
                    elif action_type.get() == "延迟等待":
                        ttk.Label(detail_frame, text="等待时间(秒):").pack(anchor=tk.W)
                        seconds_var = tk.StringVar(value=str(action.get("seconds", 1)))
                        ttk.Entry(detail_frame, textvariable=seconds_var).pack(fill=tk.X)
                        
                        def save_action():
                            actions[action_index] = {
                                "type": "delay",
                                "seconds": float(seconds_var.get())
                            }
                            update_action_list()
                            action_dialog.destroy()
                        
                        ttk.Button(detail_frame, text="保存", command=save_action).pack(pady=10)
                
                combo.bind("<<ComboboxSelected>>", update_detail_fields)
                # 初始显示
                update_detail_fields(None)
        
        def remove_action():
            selected = action_tree.selection()
            if not selected:
                return
            
            action_index = int(selected[0])
            if action_index < len(actions):
                del actions[action_index]
                update_action_list()
        
        add_action_btn = ttk.Button(action_buttons, text="添加操作", command=add_action)
        add_action_btn.pack(side=tk.LEFT, padx=5)
        
        edit_action_btn = ttk.Button(action_buttons, text="编辑操作", command=edit_action)
        edit_action_btn.pack(side=tk.LEFT, padx=5)
        
        remove_action_btn = ttk.Button(action_buttons, text="删除操作", command=remove_action)
        remove_action_btn.pack(side=tk.LEFT, padx=5)
        
        def save():
            name = name_var.get()
            image_path = image_var.get()
            if name and image_path:
                self.auto_click_manager.update_task(task_id, name, image_path, actions)
                self.refresh_auto_click_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save).pack(padx=10, pady=20)
    
    def export_auto_click_config(self):
        # 导出配置
        file_path = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*")]
        )
        if file_path:
            self.auto_click_manager.export_config(file_path)
    
    def import_auto_click_config(self):
        # 导入配置
        file_path = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*")]
        )
        if file_path:
            self.auto_click_manager.import_config(file_path)
            self.refresh_auto_click_list()
            # 更新监听频率显示
            self.freq_var.set(str(self.auto_click_manager.listen_freq))
    
    def start_auto_click_task(self):
        selected = self.auto_click_tree.selection()
        if selected:
            task_id = selected[0]
            self.auto_click_manager.start_task(task_id)
            self.refresh_auto_click_list()
    
    def pause_auto_click_task(self):
        selected = self.auto_click_tree.selection()
        if selected:
            task_id = selected[0]
            self.auto_click_manager.pause_task(task_id)
            self.refresh_auto_click_list()
    
    def remove_auto_click_task(self):
        selected = self.auto_click_tree.selection()
        if selected:
            task_id = selected[0]
            self.auto_click_manager.remove_task(task_id)
            self.refresh_auto_click_list()
    
    def save_freq(self):
        freq = self.freq_var.get()
        try:
            freq = int(freq)
            if freq > 0:
                self.auto_click_manager.set_listen_freq(freq)
                self.config_manager.set_config("auto_click", "listen_freq", str(freq))
        except ValueError:
            pass
    
    def show_system_info(self):
        """显示系统信息，用于调试远程桌面环境问题"""
        try:
            import pyautogui
            
            # 获取系统信息
            info_text = "=== 系统信息 ===\n"
            
            # DPI信息
            try:
                hdc = ctypes.windll.user32.GetDC(0)
                dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
                ctypes.windll.user32.ReleaseDC(0, hdc)
                dpi_scale = dpi_x / 96.0
                info_text += f"DPI缩放比例: {dpi_scale:.2f} (X:{dpi_x}, Y:{dpi_y})\n"
            except:
                info_text += "DPI信息获取失败\n"
            
            # 屏幕尺寸信息
            try:
                screen_width = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
                screen_height = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
                info_text += f"系统屏幕尺寸: {screen_width}x{screen_height}\n"
            except:
                info_text += "系统屏幕尺寸获取失败\n"
            
            # 虚拟屏幕尺寸
            try:
                virtual_width = ctypes.windll.user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
                virtual_height = ctypes.windll.user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
                info_text += f"虚拟屏幕尺寸: {virtual_width}x{virtual_height}\n"
            except:
                info_text += "虚拟屏幕尺寸获取失败\n"
            
            # pyautogui屏幕尺寸
            try:
                pg_size = pyautogui.size()
                info_text += f"pyautogui屏幕尺寸: {pg_size.width}x{pg_size.height}\n"
            except:
                info_text += "pyautogui屏幕尺寸获取失败\n"
            
            # 增强管理器信息
            if hasattr(self.auto_click_manager, 'dpi_manager'):
                dpi_mgr = self.auto_click_manager.dpi_manager
                info_text += f"增强管理器DPI缩放: {dpi_mgr.dpi_scale:.2f}\n"
                info_text += f"增强管理器屏幕尺寸: {dpi_mgr.screen_width}x{dpi_mgr.screen_height}\n"
            
            info_text += "=== 系统信息结束 ==="
            
            # 显示信息对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("系统信息")
            dialog.geometry("600x400")
            
            text_widget = tk.Text(dialog, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, info_text)
            text_widget.config(state=tk.DISABLED)
            
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"获取系统信息失败: {str(e)}")
    
    def test_screenshot(self):
        """测试截图功能，显示详细的调试信息"""
        try:
            # 导入必要的模块
            from PIL import ImageGrab
            import pyautogui
            
            # 创建测试对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("截图测试")
            dialog.geometry("800x600")
            
            # 创建文本区域显示日志
            log_text = tk.Text(dialog, wrap=tk.WORD, height=20)
            log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            def add_log(message):
                log_text.insert(tk.END, message + "\n")
                log_text.see(tk.END)
                dialog.update()
            
            # 开始测试
            add_log("=== 开始截图测试 ===")
            
            # 测试各种截图方法
            screenshot_methods = [
                ("ImageGrab.grab()", lambda: ImageGrab.grab()),
                ("ImageGrab.grab(all_screens=True)", lambda: ImageGrab.grab(all_screens=True)),
                ("pyautogui.screenshot()", lambda: pyautogui.screenshot()),
                ("增强截图方法", self.auto_click_manager.enhanced_screenshot)
            ]
            
            for method_name, method_func in screenshot_methods:
                add_log(f"\n测试方法: {method_name}")
                try:
                    screenshot = method_func()
                    if screenshot:
                        add_log(f"  成功 - 尺寸: {screenshot.size}")
                        
                        # 检查截图内容
                        if hasattr(self.auto_click_manager, '_check_screenshot_completeness'):
                            is_complete = self.auto_click_manager._check_screenshot_completeness(screenshot)
                            add_log(f"  内容完整性: {'完整' if is_complete else '不完整'}")
                        
                        # 保存截图用于检查
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"test_screenshot_{method_name.replace(' ', '_')}_{timestamp}.png"
                        filepath = os.path.join("data", "tests", filename)
                        
                        # 确保目录存在
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        screenshot.save(filepath)
                        add_log(f"  截图已保存: {filepath}")
                    else:
                        add_log("  失败 - 返回None")
                except Exception as e:
                    add_log(f"  失败 - 错误: {str(e)}")
            
            add_log("\n=== 截图测试结束 ===")
            
            # 添加关闭按钮
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"截图测试失败: {str(e)}")
    
    def refresh_schedule_list(self):
        # 清空列表
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 添加任务
        for task_id, task in self.schedule_manager.tasks.items():
            status = "运行中" if task["status"] else "暂停"
            self.schedule_tree.insert("", tk.END, id=task_id, values=(task["name"], task["url"], task["time"], status))
    
    def refresh_auto_click_list(self):
        # 清空列表
        for item in self.auto_click_tree.get_children():
            self.auto_click_tree.delete(item)
        
        # 添加任务
        for task_id, task in self.auto_click_manager.tasks.items():
            status = "运行中" if task["status"] else "暂停"
            self.auto_click_tree.insert("", tk.END, id=task_id, values=(task["name"], status))
    
    def start_background_threads(self):
        # 启动定时任务线程
        def schedule_thread():
            while True:
                self.schedule_manager.check_tasks()
                time.sleep(60)  # 每分钟检查一次
        
        # 启动自动化点击线程
        def auto_click_thread():
            while True:
                self.auto_click_manager.check_screen()
                time.sleep(self.auto_click_manager.listen_freq)
        
        threading.Thread(target=schedule_thread, daemon=True).start()
        threading.Thread(target=auto_click_thread, daemon=True).start()
    
    def update_log_and_screenshot(self):
        # 更新日志和截图显示
        while True:
            try:
                # 更新日志
                if hasattr(self.auto_click_manager, 'logs'):
                    logs = self.auto_click_manager.logs
                    if logs:
                        # 清空日志文本
                        self.log_text.delete(1.0, tk.END)
                        # 添加日志
                        for log in logs:
                            self.log_text.insert(tk.END, log + "\n")
                        # 滚动到底部
                        self.log_text.see(tk.END)
                
                # 更新截图
                if hasattr(self.auto_click_manager, 'latest_screenshot') and self.auto_click_manager.latest_screenshot:
                    screenshot_path = self.auto_click_manager.latest_screenshot
                    if os.path.exists(screenshot_path):
                        # 使用文件访问锁保护文件操作
                        if hasattr(self.auto_click_manager, 'file_lock'):
                            with self.auto_click_manager.file_lock:
                                # 加载并显示截图
                                from PIL import Image, ImageTk
                                img = Image.open(screenshot_path)
                        else:
                            # 加载并显示截图
                            from PIL import Image, ImageTk
                            img = Image.open(screenshot_path)
                        
                        # 获取截图显示区域的大小
                        label_width = self.screenshot_label.winfo_width()
                        label_height = self.screenshot_label.winfo_height()
                        
                        # 确保宽度和高度都大于0
                        if label_width > 0 and label_height > 0:
                            # 计算等比例缩放后的大小
                            img_width, img_height = img.size
                            ratio = min(label_width / img_width, label_height / img_height)
                            new_width = int(img_width * ratio)
                            new_height = int(img_height * ratio)
                            
                            # 调整大小
                            img = img.resize((new_width, new_height), Image.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            self.screenshot_label.config(image=photo)
                            self.screenshot_label.image = photo  # 保持引用
            except Exception as e:
                print(f"更新日志和截图失败: {e}")
            
            # 每2秒更新一次
            time.sleep(2)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoToolApp(root)
    root.mainloop()
