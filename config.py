import json
import os

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()
    
    def load_config(self):
        # 加载配置文件
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_config(self):
        # 保存配置文件
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_config(self, section, key, default=None):
        # 获取配置
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set_config(self, section, key, value):
        # 设置配置
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()
