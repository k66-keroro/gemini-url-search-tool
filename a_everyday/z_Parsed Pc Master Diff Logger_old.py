import pandas as pd
import pyodbc
import re
import logging  # loggingをインポート
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine
import os  # osをインポート
import time

# ----- 派生コード・基板番号・cm_code ロジック -----
BLACKLIST = {"SENS", "CV", "CV-055"}
DERIVATIVE_PATTERN = re.compile(r"([STU][0-9]{1,2}|[STU][A-Z][0-9])")

Y_CODE_MAP = {
    "YAMK": "m", "YAUWM": "w", "YAWM": "w", "YBPM": "p", "YCK": "c", "YCUWM": "w",
    "YGK": "g", "YMK": "m", "YPK": "p", "YPM": "p", "YUK": "w", "YWK": "w", "YWM": "w"
}

HEAD_CM_MAP = {
    "AK": "a", "CK": "c", "DK": "d", "EK": "e", "GK": "g", "HK": "h", "IK": "i", "LK": "l",
    "MK": "m", "PK": "p", "PM": "p", "SK": "s", "UK": "w", "UWM": "w", "WK": "w", "WM": "w", "WS": "w",
    "BWM": "w"
}

def extract_derivative(text: str) -> Optional[str]:
    if not isinstance(text, str): return None
    candidates = DERIVATIVE_PATTERN.findall(text.upper())
    for cand in candidates:
        if cand not in BLACKLIST:
            return cand
    return None

def extract_board_number(code: str, name: str) -> Optional[str]:
    if name.startswith("DIMCOM"):
        match = re.search(r"DIMCOM\s*(?:No\.\s*)?(\d{5})", name)
        if match:
            return match.group(1)  # 正しい5桁の番号を返す
    if code.startswith("P00A"):
        return code[5:9]
    elif code.startswith("P0A"):
        return code[3:7]
    elif "-" in name:
        parts = name.split("-")
        if len(parts) > 1:
            match = re.search(r"\d{3,4}", parts[1])
            return match.group(0) if match else None
    elif re.search(r"\d{3,4}", name):
        return re.search(r"\d{3,4}", name).group(0)
    return None

def extract_cm_code(code: str, name: str) -> str:
    name = name.upper()
    if code.startswith("P0E"):
        return "other"
    if name.startswith("WB"): return "CM-W"
    if name.startswith("DIMCOM"): return "CM-L"
    if name.startswith("CV"): return "CM-I"
    if name.startswith("FK"): return "free"
    if name.startswith("X"):
        if name.startswith("XAMK"): return "CM-M"
        if name.startswith("XUK"): return "CM-W"
        return "CM-" + name[1]
    if name.startswith("Y"):
        for l in [5, 4, 3]:
            if name[:l] in Y_CODE_MAP:
                return "CM-" + Y_CODE_MAP[name[:l]].upper()
    m = re.match(r"([A-Z]{2,4})", name)
    if m and m.group(1) in HEAD_CM_MAP:
        return "CM-" + HEAD_CM_MAP[m.group(1)].upper()
    return "other"

# ----- 接続と差分処理 -----
ACCESS_PATH = r"C:\Projects_workspace\02_access\Database1.accdb"
CONN_STR = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    fr"DBQ={ACCESS_PATH};"
    r"Mode=Share Deny None;"
)
TABLE_NAME = "view_pc_master"
MASTER_NAME = "parsed_pc_master"
LOG_FILE = r"a_everyday/差分登録ログ.csv"

# ログ設定を追加
logging.basicConfig(
    filename="debug_log.log", 
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# スクリプト開始時のログを追加
logging.info("z_Parsed Pc Master Diff Logger.py の実行を開始しました。")

# データベース接続
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# テーブル一覧を取得して確認
def check_table_exists(conn, table_name):
    try:
        tables = conn.cursor().tables(tableType='TABLE').fetchall()
        table_names = [table.table_name for table in tables]
        if table_name not in table_names:
            logging.error(f"テーブル '{table_name}' が存在しません。")
            return False
        return True
    except Exception as e:
        logging.error(f"テーブル確認中にエラーが発生しました: {e}")
        return False

# テーブル存在確認
if not check_table_exists(conn, MASTER_NAME):
    print(f"テーブル '{MASTER_NAME}' が存在しません。処理を中断します。")
    cursor.close()
    conn.close()
    exit(1)

try:
    # データを取得
    df_all = pd.read_sql(f"SELECT 品目, 品目テキスト FROM {TABLE_NAME}", conn)
except Exception as e:
    logging.error(f"データ取得エラー: {e}")
    df_all = pd.DataFrame(columns=["品目", "品目テキスト"])

try:
    df_existing = pd.read_sql(f"SELECT 品目, 品目テキスト FROM {MASTER_NAME}", conn)
except Exception as e:
    logging.error(f"データ取得エラー: {e}")
    df_existing = pd.DataFrame(columns=["品目", "品目テキスト"])

# CSVファイルの読み取り時にエンコーディングエラーを回避
try:
    df_csv = pd.read_csv(
        LOG_FILE,
        encoding='cp932',  # エンコーディングを明示的に指定
        errors='replace'   # エンコーディングエラーを回避
    )
except Exception as e:
    logging.error(f"CSV読み取りエラー: {e}")
    df_csv = pd.DataFrame(columns=["品目", "品目テキスト", "cm_code", "board_number", "derivative_code", "board_type", "登録日"])

# 差分データの生成
logging.info("差分データの生成を開始します。")
if not df_all.empty and not df_existing.empty:
    df_new = df_all[~df_all["品目"].isin(df_existing["品目"])]
else:
    df_new = pd.DataFrame(columns=["品目", "品目テキスト"])
logging.debug(f"差分データ: {df_new}")

if df_new.empty:
    logging.info("差分なし（追加不要）")
    print("差分なし（追加不要）")
    logging.info(f"CSV出力: {LOG_FILE}")
    pd.DataFrame(columns=["品目", "品目テキスト", "cm_code", "board_number", "derivative_code", "board_type", "登録日"]).to_csv(
        LOG_FILE, index=False, encoding="utf-8-sig"
    )
else:
    logging.info(f"{len(df_new)} 件の差分データを処理します。")
    df_new = df_new.copy()
    df_new["cm_code"] = df_new.apply(lambda row: extract_cm_code(row["品目"], row["品目テキスト"]), axis=1)
    df_new["board_number"] = df_new.apply(lambda row: extract_board_number(row["品目"], row["品目テキスト"]) if row["cm_code"] != "other" else None, axis=1)
    df_new["derivative_code"] = df_new.apply(lambda row: extract_derivative(row["品目テキスト"]) if row["cm_code"] != "other" else None, axis=1)
    df_new["board_type"] = df_new.apply(lambda row: "派生基板" if row["derivative_code"] else "標準" if row["cm_code"] != "other" else None, axis=1)
    df_new["登録日"] = datetime.now().strftime("%Y-%m-%d")

    # 差分データをCSVに出力
    output_path = os.path.abspath(LOG_FILE)  # 絶対パスを取得
    print({output_path})
    logging.info(f"差分データをCSVに出力します: {output_path}")
    df_new.to_csv(output_path, index=False, encoding="utf-8-sig")

    # ファイル更新確認
    if os.path.exists(output_path):
        last_modified_time = os.path.getmtime(output_path)
        logging.info(f"[確認] 差分登録ログ.csv の最終更新日時: {datetime.fromtimestamp(last_modified_time)}")
    else:
        logging.error("[エラー] 差分登録ログ.csv が存在しません。")

    # データベースへの登録
    logging.info("データベースへの登録を開始します。")
    for _, row in df_new.iterrows():
        try:
            cursor.execute(
                f"""
                INSERT INTO {MASTER_NAME} (品目, 品目テキスト, cm_code, board_number, derivative_code, board_type, 登録日)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                row["品目"], row["品目テキスト"], row["cm_code"],
                row["board_number"], row["derivative_code"], row["board_type"], row["登録日"]
            )
        except Exception as e:
            logging.error(f"データベース登録エラー: {e}")
    conn.commit()
    logging.info(f"{len(df_new)} 件をデータベースに登録しました。")

# データベース接続を閉じる
cursor.close()
conn.close()

# サーバー上のデータベースに接続してデータを追加
SERVER_DB_PATH = r"\\fsdes02\Public\課共有\業務課\000_access_data\0_データ更新\900_PC_マスタ.accdb"
SERVER_CONN_STR = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    fr"DBQ={SERVER_DB_PATH};"
    r"Mode=Share Deny None;"
)

# サーバーDB更新処理
def update_server_db():
    logging.info("サーバーDB更新を開始します。")
    try:
        # サーバーDBへの接続
        server_conn = pyodbc.connect(SERVER_CONN_STR)
        server_cursor = server_conn.cursor()

        # データを挿入するクエリ
        insert_query = """
        INSERT INTO 8000_PC区分 (品目, 品目テキスト, a, b, c, 登録日)
        SELECT parsed_pc_master.品目, parsed_pc_master.品目テキスト, parsed_pc_master.cm_code, 
               parsed_pc_master.board_number, parsed_pc_master.derivative_code, parsed_pc_master.登録日
        FROM parsed_pc_master 
        LEFT JOIN 8000_PC区分 ON parsed_pc_master.品目 = [8000_PC区分].品目
        WHERE ((([8000_PC区分].品目) Is Null));
        """

        # クエリの実行
        server_cursor.execute(insert_query)
        server_conn.commit()
        logging.info("サーバーDBにデータを追加しました。")

    except Exception as e:
        logging.error(f"サーバーDB更新中にエラーが発生しました: {e}")
    finally:
        # 接続を閉じる
        server_cursor.close()
        server_conn.close()

# 差分データの処理が完了した後にサーバーDBを更新
update_server_db()

# スクリプト終了時のログを追加
logging.info("z_Parsed Pc Master Diff Logger.py の実行が完了しました。")

# 差分登録ログの更新確認
if os.path.exists(LOG_FILE):
    last_modified_time = os.path.getmtime(LOG_FILE)
    logging.info(f"[確認] 差分登録ログ.csv の最終更新日時: {datetime.fromtimestamp(last_modified_time)}")
else:
    logging.warning("[警告] 差分登録ログ.csv が存在しません。")

def wait_for_file(file_path, timeout=30):
    """ファイルが利用可能になるまで待機"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
            time.sleep(1)
        else:
            return True
    logging.error(f"[エラー] ファイルがロックされているため、タイムアウトしました: {file_path}")
    return False

# 差分登録ログ.csv の確認
log_file_path = os.path.abspath(LOG_FILE)
if wait_for_file(log_file_path):
    logging.info(f"[確認] 差分登録ログ.csv が利用可能です。")
else:
    logging.error("[エラー] 差分登録ログ.csv が利用できません。")