import toml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / "config-tools.toml"
    
    try:
        config = toml.load(config_path)
        return config
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 {config_path}")
        return {}
    except toml.TomlDecodeError as e:
        print(f"错误: 配置文件格式不正确 - {e}")
        return {}

config = load_config() 