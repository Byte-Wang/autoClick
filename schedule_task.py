import webbrowser
import time
import threading

class ScheduleTaskManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tasks = {}
        self.load_tasks()
        
        # 添加默认任务
        if not self.tasks:
            self.add_default_task()
    
    def add_default_task(self):
        # 默认任务：每天12点打开提现页面
        self.add_task(
            "定时打开提现页面",
            "https://sellercentral.amazon.com/payments/dashboard/index.html/ref=xx_payments_favb_xx&autoPayment=1",
            "12:00"
        )
    
    def load_tasks(self):
        # 从配置中加载任务
        tasks_config = self.config_manager.get_config("schedule", "tasks", {})
        self.tasks = tasks_config
    
    def save_tasks(self):
        # 保存任务到配置
        self.config_manager.set_config("schedule", "tasks", self.tasks)
    
    def add_task(self, name, url, time_str):
        # 生成任务ID
        task_id = str(int(time.time()))
        
        # 创建任务
        self.tasks[task_id] = {
            "name": name,
            "url": url,
            "time": time_str,
            "status": True  # 默认启动
        }
        
        self.save_tasks()
        return task_id
    
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
    
    def check_tasks(self):
        # 检查所有任务
        current_time = time.strftime("%H:%M")
        for task_id, task in self.tasks.items():
            if task["status"] and task["time"] == current_time:
                # 打开URL
                threading.Thread(target=self.open_url, args=(task["url"],)).start()
    
    def open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"打开URL失败: {e}")
