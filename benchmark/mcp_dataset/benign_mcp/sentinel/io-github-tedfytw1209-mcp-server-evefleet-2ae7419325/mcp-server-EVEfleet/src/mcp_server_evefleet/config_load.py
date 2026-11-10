import yaml
from pathlib import Path
from importlib import resources

def set_globals_from_dict(d):
    for key, value in d.items():
        globals()[key] = value
        
# Prefer CWD config.yaml if present; otherwise load packaged resource
config_path = Path('config.yaml')
if config_path.exists():
    with open(config_path, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f)
else:
    with resources.files('mcp_server_evefleet').joinpath('config.yaml').open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

CONFIG = config
