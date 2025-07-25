import pandas as pd
import pyodbc
from decimal import Decimal, InvalidOperation, getcontext
import time
from datetime import datetime
import logging

logging.basicConfig(filename='inventory.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# スクリプトの実行時間を測定
start_time = time.time()
# データベース接続
db_start_time = time.time()
# データベース関連処理
print(f"データベース処理時間: {time.time() - db_start_time:.2f}秒")

def calculate_inventory(df):
    new_data = []
    for _, row in df.iterrows():
        new_row = {
            '連続行番号': row['連続行番号'],
            '品目': row['品目'],
            '名称': row['名称'],
            'MRPエリア': row['MRPエリア'],
            'プラント': row['プラント'],
            '所要日付': row['所要日付'],  # datetimeオブジェクトをそのまま格納
            'MRP要素': row['MRP要素'],
            'MRP要素データ': 'MRP要素データ',
            '再日程計画日付': row['再日程計画日付'], # datetimeオブジェクトをそのまま格納
            '例外Msg': row.get('例外Msg'), # KeyError対策
            '入庫_所要量': row['入庫_所要量'],
            '利用可能数量': row['利用可能数量'],
            '保管場所': row['保管場所'],
            '入出庫予定': row['入出庫予定'],
            'Itm': row['Itm'],
            '引当': row['引当'],
            '過不足': row['過不足']
        }
        new_data.append(new_row)
    new_df = pd.DataFrame(new_data)
    return new_df



# 小数点以下の桁数を設定
getcontext().prec = 10

# ファイルパスの設定
input_file_path = r'\\fssha01\common\HOST\ZP138\ZP138.txt'
access_db_path = r'C:\\Projects_workspace\\02_access\\Database1.accdb'
table_name = 't_zp138引当'

# SAP後ろマイナス対応
def process_trailing_minus(value):
    if isinstance(value, str) and value.endswith('-'):
        return f"-{value[:-1]}"
    return value

# 日付フォーマット
def format_date_for_db(date): # 修正
    if pd.isnull(date):
        return None
    return pyodbc.Date(date.year, date.month, date.day)

# Decimal変換（エラー処理強化）
def safe_decimal_conversion(value):
    value = process_trailing_minus(value)
    try:
        if value in [None, '', '']:
            return Decimal(0)
        return Decimal(value).quantize(Decimal('0.001'))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)

# 在庫計算
def calculate_inventory(df_batch):
    df_result = df_batch.copy() # copyを作成
    grouped = df_result.sort_values(by=['品目', '連続行番号']).groupby('品目')

    for item, group in grouped:
        #print(f"■■■ 品目: {item} の処理開始 ■■■")
        actual_stock = Decimal(0).quantize(Decimal('0.001'))
        shortage = Decimal(0).quantize(Decimal('0.001'))
        group_indices = group.index #indexを取得

        for index, row in group.iterrows():
            #print(f"□□□ 品目: {item}, 連続行番号: {row['連続行番号']}, index: {index} の処理開始 □□□")
            #try:
            #    print(row)
            #except UnicodeEncodeError:
            #    print("UnicodeEncodeError occurred for this row.")

            row_quantity = Decimal(row['入庫_所要量']).quantize(Decimal('0.001'))

            #print(f"品目: {item}, 連続行番号: {row['連続行番号']}, MRP要素: {row['MRP要素']}, 入庫_所要量: {row_quantity}, actual_stock: {actual_stock}, shortage: {shortage}") # ★詳細出力★
            if row['MRP要素'] == '在庫':
                actual_stock = row_quantity
                shortage = Decimal(0)
                allocation = Decimal(0)
                excess_shortage = actual_stock
                df_result.loc[index, '引当'] = float(allocation)
                df_result.loc[index, '過不足'] = excess_shortage
                #print(f"品目: {item}, 連続行番号: {row['連続行番号']}, MRP要素: 在庫, actual_stock: {actual_stock}, allocation: {allocation}, excess_shortage: {excess_shortage}")
            elif row['MRP要素'] in ['外注依', '受注', '従所要', '入出予', '出荷']:
                required_qty = abs(row_quantity)
                #print(f"品目: {item}, 連続行番号: {row['連続行番号']}, MRP要素: {row['MRP要素']}, actual_stock: {actual_stock}, required_qty: {required_qty}")

                if actual_stock >= required_qty:
                    allocation = required_qty
                    actual_stock -= allocation
                else:
                    allocation = actual_stock
                    shortage += (required_qty - actual_stock)
                    actual_stock = Decimal(0)

                #print(f"品目: {item}, 連続行番号: {row['連続行番号']}, MRP要素: {row['MRP要素']}, allocation: {allocation}, actual_stock: {actual_stock}, shortage: {shortage}")
                excess_shortage = actual_stock - shortage
                if excess_shortage is not None:
                    excess_shortage = Decimal(excess_shortage).quantize(Decimal('0.001'))
                df_result.loc[index, '引当'] = float(allocation)
                df_result.loc[index, '過不足'] = excess_shortage
            else:
                allocation = Decimal(0)
                excess_shortage = None
                #print(f"品目: {item}, 連続行番号: {row['連続行番号']}, MRP要素: その他, allocation: {allocation}, excess_shortage: {excess_shortage}")
                df_result.loc[index, '引当'] = float(allocation)
                df_result.loc[index, '過不足'] = excess_shortage
            #print(f"□□□ 品目: {item}, 連続行番号: {row['連続行番号']}, index: {index} の処理終了 □□□")
        #print(f"■■■ 品目: {item} の処理終了 ■■■")
    df_batch.update(df_result) # 元のdfに反映
    return df_batch #df_batchを返すように修正




# 文字列の切り詰め関数
def truncate_text(text, max_length=255):
    if isinstance(text, str):
        return text[:max_length]
    return text

# 特殊文字削除
def clean_text(value):
    if isinstance(value, str):
        return ''.join(c for c in value if c.isprintable()).strip()
    return value


column_mapping = {
    '連続行番号': '連続行番号',
    '品目': '品目',
    '名称': '名称',
    'MRP エリア': 'MRPエリア',
    'プラント': 'プラント',
    '所要日付': '所要日付',
    'MRP 要素': 'MRP要素',
    'MRP 要素データ': 'MRP要素データ', # ★半角スペースに修正★
    '再日程計画日付': '再日程計画日付',
    '例外Msg': '例外Msg',
    '入庫/所要量': '入庫_所要量',
    '利用可能数量': '利用可能数量',
    '保管場所': '保管場所',
    '入出庫予定': '入出庫予定',
    'Itm': 'Itm',
    '引当': '引当',
    '過不足': '過不足'
}

try:
    data = pd.read_csv(input_file_path, delimiter='\t', encoding='cp932', header=0)
except FileNotFoundError:
    print(f"エラー: ファイルが見つかりません: {input_file_path}")
    exit()
except Exception as e:
    print(f"ファイルの読み込み中にエラーが発生しました: {e}")
    exit()

# データ数を50件に絞る（検証用）★ここを追加★
#data = data.head(50)

# 読み込んだ直後のカラム名を出力 (★ここを修正★)
#print("txtファイル読み込み直後のカラム名:")
#print(data.columns)

# カラム名を変更
data = data.rename(columns=column_mapping)

# データ数を50件に絞る（検証用）
#data = data.head(50)

# 「引当」と「過不足」カラムを追加 (初期値はNone)
data['引当'] = None
data['過不足'] = None


# 日付列処理
data['所要日付'] = pd.to_datetime(data['所要日付'], format='%Y%m%d', errors='coerce')
data['所要日付'] = data['所要日付'].where(pd.notna(data['所要日付']), None)

data['再日程計画日付'] = pd.to_datetime(data['再日程計画日付'], format='%Y%m%d', errors='coerce')
data['再日程計画日付'] = data['再日程計画日付'].where(pd.notna(data['再日程計画日付']), None)

#print("pd.to_datetime後のデータ:")
#print(data[['所要日付', '再日程計画日付']].head())
#print("pd.to_datetime後のデータ型:")
#print(data[['所要日付', '再日程計画日付']].dtypes)

# 追加：個々の要素の型を確認
#for i in range(5):  # 最初の5行で確認
#    print(f"所要日付[{i}]の型: {type(data['所要日付'][i])}")
#    print(f"再日程計画日付[{i}]の型: {type(data['再日程計画日付'][i])}")


# 数値列処理
data['入庫_所要量'] = data['入庫_所要量'].apply(safe_decimal_conversion)
data['利用可能数量'] = data['利用可能数量'].apply(safe_decimal_conversion)

# 保管場所整形（修正版）
data['保管場所'] = data['保管場所'].fillna('').apply(lambda x: str(int(x)) if isinstance(x, (int, float)) else str(x)).str.replace(r',.*$', '', regex=True)

# 過不足計算
final_df = calculate_inventory(data)

# データ変換とNoneへの統一（日付変換処理を削除）
for col in final_df.select_dtypes(exclude=['datetime64[ns]']): # datetime64[ns]型は除外
    if pd.api.types.is_numeric_dtype(final_df[col]):
        continue # 数値型はスキップ
    else: # 文字列型の場合
        final_df[col] = final_df[col].apply(clean_text)
        final_df[col] = final_df[col].fillna('NULL')

# MRP要素データのNULLをpd.NAに変換
final_df['MRP要素データ'] = final_df['MRP要素データ'].apply(lambda x: pd.NA if x == 'NULL' or pd.isna(x) else x)
# Noneをpd.NAに変換
final_df['MRP要素データ'] = final_df['MRP要素データ'].fillna(pd.NA)
final_df['例外Msg'] = final_df['例外Msg'].fillna(pd.NA)


# データ確認
#print("final_df の最初の5行:")
#print(final_df.head())
#print("final_df のデータ型:")
#print(final_df.dtypes)


# データベース接続とテーブル作成
connection_string = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
with pyodbc.connect(connection_string) as conn:
    cursor = conn.cursor()
    # 既存テーブル削除
    try:
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
    except pyodbc.Error:
        pass

    # テーブル作成 (データ型を修正)
    columns = []
    for col_name_txt, col_name_db in column_mapping.items():
        if col_name_db == '連続行番号':
            columns.append(f"[連続行番号] LONG")
        elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
            columns.append(f"[{col_name_db}] DOUBLE")
        elif col_name_db in ['所要日付', '再日程計画日付']:
            columns.append(f"[{col_name_db}] DATETIME")    # ★DATETIME型に変更★
        else:
            columns.append(f"[{col_name_db}] TEXT(255)")

    create_table_sql = f"""
        CREATE TABLE {table_name} (
            {", ".join(columns)}
        )
    """
    #print("CREATE TABLE SQL:")
    #print(create_table_sql)
    cursor.execute(create_table_sql)
    conn.commit()


    try:
        for _, row in final_df.iterrows():
            values = []
            cols = []
            placeholders = []

            for col_name_db in final_df.columns:
                value = row[col_name_db]

                if col_name_db == '連続行番号':
                    if pd.notnull(value):
                        try:
                            values.append(int(value))
                        except ValueError:
                            print(f"Warning: Could not convert '{value}' to integer.")
                            values.append(None)
                    else:
                        values.append(None)
                elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
                    if pd.notnull(value) and isinstance(value,(int,float,Decimal)): # 型の確認を厳格化
                        values.append(float(value))
                    else:
                        values.append(None) # Noneを明示的に追加
                elif col_name_db in ['所要日付', '再日程計画日付']: # 修正
                    #print(f"{col_name_db} の値 (strftime 直前): {value}, 型: {type(value)}")
                    if value is None:
                        values.append(None)
                    elif isinstance(value, datetime):
                        values.append(format_date_for_db(value))
                    else:
                        print(f"Warning: Value for {col_name_db} is not a datetime object: {value}, type: {type(value)}")
                        values.append(None)
                elif col_name_db == '引当':
                    #print(f"引当の値: {value}, 型: {type(value)}")
                    values.append(value)
                elif pd.isna(value):
                    values.append(None)
                else:
                    values.append(str(value))
                cols.append(f"[{col_name_db}]")
                placeholders.append("?")

            cols_str = ", ".join(cols)
            placeholders_str = ", ".join(placeholders)
            
            sql = f"""
                INSERT INTO {table_name} ({cols_str})
                VALUES ({placeholders_str})
            """
            #print(f"cols: {cols}") # ★追加★
            #print(f"実行しようとしたSQL: \n{sql}")
            #print(f"values: {values}")
            cursor.execute(sql, values)

        conn.commit()
    except pyodbc.Error as e:
        sqlstate = e.args[0]
        print(f"DBエラーが発生しました: {str(e)}")
        print(f"SQLSTATE: {sqlstate}")
        if sqlstate == '23000':
            print("重複エラーの可能性があります。")
        conn.rollback()
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
print(f"データ挿入が完了しました。処理時間: {time.time() - start_time:.2f}秒")        

# 最後に Access.Application を安全に終了
try:
    import win32com.client
    access_app = win32com.client.Dispatch("Access.Application")
    access_app.Quit()
    del access_app
except Exception as e:
    print(f"Accessアプリケーションの終了時にエラー: {e}")
# 全体の処理終了
print(f"全体の処理時間: {time.time() - start_time:.2f}秒")