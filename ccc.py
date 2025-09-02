import google.generativeai as genai
import os

# APIキーを環境変数から取得
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def call_gemini(prompt, models=['gemini-2.5-flash', 'gemini-1.5-flash']):
    """
    指定されたモデルのリストを順番に試して、
    API呼び出しに成功するまで実行する関数
    """
    for model_name in models:
        try:
            print(f"モデル '{model_name}' を試行中...")
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content(prompt)
            print("API呼び出しが成功しました。")
            return response.text
        except Exception as e:
            print(f"モデル '{model_name}' でエラーが発生しました: {e}")
            continue # 次のモデルを試す

    return "すべてのモデルの呼び出しに失敗しました。"

# ユーザーのプロンプト
user_prompt = "日本の首都はどこですか？"

# 関数を実行
result = call_gemini(user_prompt)

# 結果を表示
print("\n--- 結果 ---")
print(result)