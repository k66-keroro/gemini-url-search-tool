from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ModuleConfig:
    module_name: str
    function_name: Optional[str] = None
    order: int = 0

# モジュールの設定をより構造化
MODULES = [
    ModuleConfig("z900_filecopy_txt", order=1),
    ModuleConfig("z090_zp138_txt", order=2),
    ModuleConfig("z090_zp138_field_mapping", order=3),
    ModuleConfig("zp02", order=4),
    ModuleConfig("zs65", order=5),
    #ModuleConfig("zm87.py", order=6),
    ModuleConfig("zt_zm87_code", order=7),
    ModuleConfig("a1_app_open_ac", "access_open", order=8),
]

def main():
    # 順序でソート
    for config in sorted(MODULES, key=lambda x: x.order):
        module = __import__(config.module_name)
        if config.function_name:
            getattr(module, config.function_name)()

if __name__ == '__main__':
    main()