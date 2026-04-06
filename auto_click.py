import os
import sys
import pyautogui
import time
import threading
from PIL import ImageGrab
import datetime

class AutoClickManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tasks = {}
        self.listen_freq = int(self.config_manager.get_config("auto_click", "listen_freq", "30"))
        self.load_tasks()
        self.executing = False  # 标记是否正在执行操作
        self.logs = []  # 日志列表
        self.latest_screenshot = None  # 最新截图路径
        
        # 创建日志和截图目录
        self.log_dir = os.path.join(os.getcwd(), "data", "logs")
        self.screenshot_dir = os.path.join(os.getcwd(), "data", "screenshots")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    def load_tasks(self):
        # 从配置中加载任务
        tasks_config = self.config_manager.get_config("auto_click", "tasks", {})
        self.tasks = tasks_config
    
    def save_tasks(self):
        # 保存任务到配置
        self.config_manager.set_config("auto_click", "tasks", self.tasks)
    
    def add_task(self, name, image_path, actions):
        # 生成任务ID
        task_id = str(int(time.time()))
        
        # 创建任务
        self.tasks[task_id] = {
            "name": name,
            "image_path": image_path,
            "actions": actions,
            "status": True  # 默认启动
        }
        
        self.save_tasks()
        return task_id
    
    def update_task_actions(self, task_id, actions):
        # 更新任务的操作清单
        if task_id in self.tasks:
            self.tasks[task_id]["actions"] = actions
            self.save_tasks()
    
    def update_task(self, task_id, name, image_path, actions):
        # 更新任务的所有信息
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
    
    def check_screen(self):
        if self.executing:
            return
        
        # 检查是否有正在运行的任务
        has_running_task = False
        for task_id, task in self.tasks.items():
            if task["status"]:
                has_running_task = True
                break
        
        # 如果没有正在运行的任务，则不进行屏幕监听
        if not has_running_task:
            return
        
        try:
            # 截取屏幕
            screenshot = ImageGrab.grab()
            
            # 删除上一次的截图
            if self.latest_screenshot and os.path.exists(self.latest_screenshot):
                os.remove(self.latest_screenshot)
            
            # 保存最新截图
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
            screenshot.save(screenshot_path)
            self.latest_screenshot = screenshot_path
            
            # 添加日志
            self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 屏幕监听: 截取屏幕成功")
            
            # 检查所有任务
            for task_id, task in self.tasks.items():
                if task["status"]:
                    try:
                        # 加载任务截图
                        if not os.path.exists(task["image_path"]):
                            self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务 {task['name']}: 截图文件不存在")
                            continue
                        
                        # 检查图像文件是否存在
                        if not os.path.exists(task["image_path"]):
                            error_msg = f"任务 {task_id} 失败: 图像文件不存在: {task['image_path']}"
                            print(error_msg)
                            self.add_log(error_msg)
                            continue
                        
                        # 检查图像文件是否为有效文件
                        if not os.path.isfile(task["image_path"]):
                            error_msg = f"任务 {task_id} 失败: 路径不是文件: {task['image_path']}"
                            print(error_msg)
                            self.add_log(error_msg)
                            continue
                        
                        # 检查图像文件大小
                        try:
                            file_size = os.path.getsize(task["image_path"])
                            if file_size == 0:
                                error_msg = f"任务 {task_id} 失败: 图像文件为空: {task['image_path']}"
                                print(error_msg)
                                self.add_log(error_msg)
                                continue
                        except Exception as e:
                            error_msg = f"任务 {task_id} 失败: 无法获取文件大小: {str(e)}"
                            print(error_msg)
                            self.add_log(error_msg)
                            continue
                        
                        # 使用pyautogui的locateOnScreen功能进行图像识别
                        try:
                            # 打印图像路径
                            self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务 {task['name']}: 开始查找图像: {task['image_path']}")
                            # 使用pyautogui的locateOnScreen功能
                            location = pyautogui.locateOnScreen(task["image_path"])
                            
                            # 匹配成功
                            if location:
                                # 命中任务，执行操作
                                self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务 {task['name']}: 命中截图")
                                self.executing = True
                                # 计算匹配位置
                                max_loc = (location.left, location.top)
                                threading.Thread(target=self.execute_actions, args=(task["actions"], max_loc)).start()
                            else:
                                self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务 {task['name']}: 未找到匹配图像")
                        except Exception as e:
                            error_msg = f"检查任务 {task_id} 失败: {str(e)}"
                            print(error_msg)
                            self.add_log(error_msg)
                    except Exception as e:
                        error_msg = f"检查任务 {task_id} 失败: {e}"
                        print(error_msg)
                        self.add_log(error_msg)
        except Exception as e:
            error_msg = f"屏幕截图失败: {e}"
            print(error_msg)
            self.add_log(error_msg)
    
    def add_log(self, message):
        # 添加日志
        self.logs.append(message)
        # 限制日志数量
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        # 保存日志到文件
        log_file = os.path.join(self.log_dir, f"auto_click_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    
    def execute_actions(self, actions, match_loc):
        try:
            for action in actions:
                action_type = action.get("type")
                if action_type == "click_screen":
                    # 鼠标点击屏幕指定位置
                    x = action.get("x", 0)
                    y = action.get("y", 0)
                    pyautogui.click(x, y)
                    self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行操作: 鼠标点击屏幕位置 ({x}, {y})")
                elif action_type == "click_match":
                    # 鼠标点击命中截图位置
                    x = match_loc[0] + action.get("offset_x", 0)
                    y = match_loc[1] + action.get("offset_y", 0)
                    pyautogui.click(x, y)
                    self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行操作: 鼠标点击命中位置 ({x}, {y})")
                elif action_type == "keyboard":
                    # 键盘输入
                    text = action.get("text", "")
                    pyautogui.typewrite(text)
                    self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行操作: 键盘输入 '{text}'")
                elif action_type == "delay":
                    # 延迟等待
                    seconds = action.get("seconds", 1)
                    self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行操作: 延迟等待 {seconds} 秒")
                    time.sleep(seconds)
                
                # 小延迟，确保操作执行
                time.sleep(0.5)
        finally:
            self.executing = False
            self.add_log(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 操作执行完成")
    
    def export_config(self, file_path):
        # 导出配置到文件
        import os
        # 获取程序根目录
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 转换路径为相对路径
        export_tasks = {}
        for task_id, task in self.tasks.items():
            export_task = task.copy()
            if "image_path" in export_task and export_task["image_path"]:
                # 转换为相对路径
                try:
                    export_task["image_path"] = os.path.relpath(export_task["image_path"], root_dir)
                except ValueError:
                    # 如果路径不在同一个驱动器，保持绝对路径
                    pass
            export_tasks[task_id] = export_task
        
        config_data = {
            "tasks": export_tasks,
            "listen_freq": str(self.listen_freq)
        }
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def import_config(self, file_path):
        # 从文件导入配置
        import json
        import os
        # 获取程序根目录
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 转换路径为绝对路径
        import_tasks = {}
        for task_id, task in config_data.get("tasks", {}).items():
            import_task = task.copy()
            if "image_path" in import_task and import_task["image_path"]:
                # 如果是相对路径，转换为绝对路径
                if not os.path.isabs(import_task["image_path"]):
                    import_task["image_path"] = os.path.join(root_dir, import_task["image_path"])
            import_tasks[task_id] = import_task
        
        # 更新任务和监听频率
        self.tasks = import_tasks
        if "listen_freq" in config_data:
            try:
                self.listen_freq = int(config_data["listen_freq"])
            except ValueError:
                pass
        
        # 保存到配置文件
        self.save_tasks()
