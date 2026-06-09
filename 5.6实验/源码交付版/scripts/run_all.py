import sys
import json
from pathlib import Path

# 将项目根目录加入模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core_analysis import analyze_group

def load_config():
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"global_defaults": {}, "group_overrides": {}}

def main():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    config_data = load_config()
    
    if not raw_dir.exists() or not list(raw_dir.iterdir()):
        print("="*60)
        print(f"提示: 请先将各组实验数据(文件夹)放入: {raw_dir}")
        return
        
    for group_dir in raw_dir.iterdir():
        if group_dir.is_dir():
            print(f"==== 开始处理工况: {group_dir.name} ====")
            
            # 合并全局配置和组别特有配置
            group_cfg = config_data.get("global_defaults", {}).copy()
            overrides = config_data.get("group_overrides", {}).get(group_dir.name, {})
            group_cfg.update(overrides)
            
            try:
                # 传入动态配置
                summary = analyze_group(group_dir, config=group_cfg)
                print(f"[{group_dir.name}] 处理成功！")
            except Exception as e:
                print(f"[{group_dir.name}] 处理失败: {e}")

if __name__ == "__main__":
    main()
