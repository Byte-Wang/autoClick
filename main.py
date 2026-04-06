import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
import time
import os
import sys

# 添加当前目录到sys.path，确保优先导入项目中的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schedule_task import ScheduleTaskManager
from auto_click import AutoClickManager
from app_config import ConfigManager

class AutoToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化工具")
        self.root.geometry("1600x1200")
        
        # 配置管理
        self.config_manager = ConfigManager()
        
        # 定时任务管理器
        self.schedule_manager = ScheduleTaskManager(self.config_manager)
        
        # 自动化点击管理器
        self.auto_click_manager = AutoClickManager(self.config_manager)
        
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
        
        def capture_screen():
            # 创建data/images目录
            image_dir = os.path.join(os.getcwd(), "data", "images")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            # 截取屏幕
            from PIL import ImageGrab
            screen = ImageGrab.grab()
            
            # 创建截图预览窗口
            capture_dialog = tk.Toplevel(dialog)
            capture_dialog.title("截取屏幕")
            capture_dialog.attributes("-fullscreen", True)
            capture_dialog.attributes("-topmost", True)
            
            # 创建画布
            from PIL import ImageTk
            img = ImageTk.PhotoImage(screen)
            canvas = tk.Canvas(capture_dialog, width=screen.width, height=screen.height)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # 显示截图
            canvas.create_image(0, 0, anchor=tk.NW, image=img)
            canvas.image = img
            
            # 添加半透明黑色遮罩
            canvas.create_rectangle(0, 0, screen.width, screen.height, fill="black", stipple="gray50")
            
            # 框选变量
            start_x = start_y = end_x = end_y = 0
            rect_id = None
            
            def on_mouse_down(event):
                nonlocal start_x, start_y, rect_id
                start_x, start_y = event.x, event.y
                # 创建矩形
                rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2, fill="", dash=(5, 5))
            
            def on_mouse_move(event):
                nonlocal end_x, end_y, rect_id
                if rect_id:
                    end_x, end_y = event.x, event.y
                    canvas.coords(rect_id, start_x, start_y, end_x, end_y)
            
            def on_mouse_up(event):
                nonlocal end_x, end_y
                end_x, end_y = event.x, event.y
                
                # 计算框选区域
                left = min(start_x, end_x)
                top = min(start_y, end_y)
                right = max(start_x, end_x)
                bottom = max(start_y, end_y)
                
                # 确保框选区域有效
                if right > left and bottom > top:
                    # 裁剪截图
                    crop = screen.crop((left, top, right, bottom))
                    
                    # 保存裁剪后的图片
                    import time
                    timestamp = int(time.time())
                    file_name = f"screenshot_{timestamp}.png"
                    dest_path = os.path.join(image_dir, file_name)
                    crop.save(dest_path)
                    
                    # 更新路径变量
                    image_var.set(dest_path)
                
                # 关闭窗口
                capture_dialog.destroy()
            
            # 绑定鼠标事件
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        ttk.Button(path_frame, text="上传截图", command=upload_image).pack(side=tk.RIGHT, padx=5)
        ttk.Button(path_frame, text="手动截图", command=capture_screen).pack(side=tk.RIGHT, padx=5)
        
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
        
        def capture_screen():
            # 创建data/images目录
            image_dir = os.path.join(os.getcwd(), "data", "images")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            # 截取屏幕
            from PIL import ImageGrab
            screen = ImageGrab.grab()
            
            # 创建截图预览窗口
            capture_dialog = tk.Toplevel(dialog)
            capture_dialog.title("截取屏幕")
            capture_dialog.attributes("-fullscreen", True)
            capture_dialog.attributes("-topmost", True)
            
            # 创建画布
            from PIL import ImageTk
            img = ImageTk.PhotoImage(screen)
            canvas = tk.Canvas(capture_dialog, width=screen.width, height=screen.height)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # 显示截图
            canvas.create_image(0, 0, anchor=tk.NW, image=img)
            canvas.image = img
            
            # 添加半透明黑色遮罩
            canvas.create_rectangle(0, 0, screen.width, screen.height, fill="black", stipple="gray50")
            
            # 框选变量
            start_x = start_y = end_x = end_y = 0
            rect_id = None
            
            def on_mouse_down(event):
                nonlocal start_x, start_y, rect_id
                start_x, start_y = event.x, event.y
                # 创建矩形
                rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2, fill="", dash=(5, 5))
            
            def on_mouse_move(event):
                nonlocal end_x, end_y, rect_id
                if rect_id:
                    end_x, end_y = event.x, event.y
                    canvas.coords(rect_id, start_x, start_y, end_x, end_y)
            
            def on_mouse_up(event):
                nonlocal end_x, end_y
                end_x, end_y = event.x, event.y
                
                # 计算框选区域
                left = min(start_x, end_x)
                top = min(start_y, end_y)
                right = max(start_x, end_x)
                bottom = max(start_y, end_y)
                
                # 确保框选区域有效
                if right > left and bottom > top:
                    # 裁剪截图
                    crop = screen.crop((left, top, right, bottom))
                    
                    # 保存裁剪后的图片
                    import time
                    timestamp = int(time.time())
                    file_name = f"screenshot_{timestamp}.png"
                    dest_path = os.path.join(image_dir, file_name)
                    crop.save(dest_path)
                    
                    # 更新路径变量
                    image_var.set(dest_path)
                
                # 关闭窗口
                capture_dialog.destroy()
            
            # 绑定鼠标事件
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        ttk.Button(path_frame, text="上传截图", command=upload_image).pack(side=tk.RIGHT, padx=5)
        ttk.Button(path_frame, text="手动截图", command=capture_screen).pack(side=tk.RIGHT, padx=5)
        
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
