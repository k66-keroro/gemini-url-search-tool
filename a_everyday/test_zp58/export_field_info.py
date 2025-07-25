import pandas as pd

def export_field_info_to_csv(input_file, output_file):
    try:
        # データフレームを読み込む
        df = pd.read_csv(input_file, delimiter='\t', encoding='cp932', low_memory=False)

        # フィールド名とデータ型を取得
        field_info = pd.DataFrame({
            'Field Name': df.columns,
            'Data Type': [str(df[col].dtype) for col in df.columns]
        })

        # CSVに出力
        field_info.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"フィールド情報を {output_file} に出力しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    # 入力ファイルと出力ファイルのパス
    input_file = r'C:\Projects_workspace\02_access\テキスト\zp58.txt'
    output_file = r'C:\Projects_workspace\02_access\テキスト\field_info.csv'

    # フィールド情報をエクスポート
    export_field_info_to_csv(input_file, output_file)