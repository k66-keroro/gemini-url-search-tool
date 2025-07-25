from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Paths:
    """パス定数管理"""
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    RAW_DATA: Path = PROJECT_ROOT / "data" / "raw"
    SQLITE_DB: Path = PROJECT_ROOT / "data" / "sqlite" / "main.db"
    ACCESS_OUTPUT: Path = PROJECT_ROOT / "data" / "access"
    LOGS: Path = PROJECT_ROOT / "logs"
    
    def __post_init__(self):
        """ディレクトリ作成"""
        for path in [self.RAW_DATA, self.SQLITE_DB.parent, self.ACCESS_OUTPUT, self.LOGS]:
            path.mkdir(parents=True, exist_ok=True)

@dataclass 
class FilePatterns:
    """ファイルパターン定義"""
    SAP_FILES: Dict[str, str] = None
    
    def __post_init__(self):
        self.SAP_FILES = {
            "GetPLMItmPlntInfo_P100": "GetPLMItmPlntInfo_P100.txt",
            "GetSekkeiWBSJisseki": "GetSekkeiWBSJisseki.txt",
            "KANSEI_JISSEKI": "KANSEI_JISSEKI.txt",
            "KOUSU_JISSEKI": "KOUSU_JISSEKI.txt",
            "KOUTEI_JISSEKI": "KOUTEI_JISSEKI.txt",
            "MARA_DL": "MARA_DL.csv",
            "PP_DL_CSV_SEISAN_YOTEI": "PP_DL_CSV_SEISAN_YOTEI.csv",
            "PP_DL_CSV_ZTBP110": "PP_DL_CSV_ZTBP110.csv",
            "PP_SUMMARY_ZTBP080_KOJOZISSEKI_D_0": "PP_SUMMARY_ZTBP080_KOJOZISSEKI_D_0.xlsx",
            "SASIZU_JISSEKI": "SASIZU_JISSEKI.txt",
            "V_SAGYO_TIME": "V_SAGYO_TIME.txt",
            "zf26": "zf26.csv",
            "zm114": "zm114.txt",
            "zm21": "zm21.txt",
            "ZM29": "ZM29.txt",
            "zm37": "zm37.txt",
            "zm87n": "zm87n.txt",
            "zp02": "zp02.txt",
            "ZP128_P100": "ZP128_P100.txt",
            "ZP128_P300": "ZP128_P300.txt",
            "ZP138": "ZP138.txt",
            "zp160": "zp160.txt",
            "ZP170": "ZP170.TXT",
            "zp35": "zp35.txt",
            "ZP51N": "ZP51N.TXT",
            "zp58": "zp58.txt",
            "zp70": "zp70.txt",
            "ZPF01802_mikanryo": "ZPF01802_未完了分.TXT",
            "zs191": "zs191.txt",
            "zs45": "zs45.txt",
            "ZS58MONTH": "ZS58MONTH.csv",
            "ZS61KDAY": "ZS61KDAY.csv",
            "zs65": "zs65.txt",
            "zs65_sss": "zs65_sss.txt",
            "plm_shiryoirai": "資料依頼未完了一覧.xlsx",
            "haraidashi_shiga_zpr01201": "払出明細（滋賀）_ZPR01201.txt",
            "haraidashi_osaka_zpr01201": "払出明細（大阪）_ZPR01201.txt",
            "hinmoku_nyushutsu": "dbo_提出用_経理_滞留在庫資料_通常.xlsx",
            "ZM122_P100_1220": "ZM122_P100_1220.TXT",
            "ZM122_P100_1230": "ZM122_P100_1230.TXT",
            "ZM122_P100_1240": "ZM122_P100_1240.TXT",
            "ZP173": "ZP173.TXT",
            "ZP173_MEISAI": "ZP173_MEISAI.TXT",
        }

@dataclass
class ProcessConfig:
    """処理設定"""
    CHUNK_SIZE: int = 50000
    MAX_WORKERS: int = 4
    TIMEOUT_SECONDS: int = 300
    ENCODING_LIST: List[str] = None
    
    def __post_init__(self):
        self.ENCODING_LIST = ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']