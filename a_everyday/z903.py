from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ModuleConfig:
    module_name: str
    function_name: Optional[str] = None
    order: int = 0

MODULES = [
    ModuleConfig("a1_app_open_edge", order=1),
    ModuleConfig("a1_app_open_ac", order=2),
    ModuleConfig("a1_app_open_a", order=3),
    #ModuleConfig("a1_app_open_ac", "access_open", order=4),
]

def execute_module(config: ModuleConfig):
    module = __import__(config.module_name)
    if config.function_name:
        getattr(module, config.function_name)()

def main():
    with ThreadPoolExecutor() as executor:
        executor.map(execute_module, MODULES)

if __name__ == '__main__':
    main()