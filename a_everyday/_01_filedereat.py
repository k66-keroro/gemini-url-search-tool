import os
from office365.sharepoint.client_context import ClientContext

# SharePointのサイトURL
site_url = "https://sanrex-my.sharepoint.com/personal/masakatsu-sakai_sanrex_onmicrosoft_com"

# ファイルパス
file_path = "Documents/ドキュメント 2/Basis (1) の ワークシート.xlsx"

# 認証情報
username = "masakatsu-sakai@sanrex.onmicrosoft.com"
password = "03171Sakai4"

# SharePointクライアントの作成
ctx = ClientContext(site_url).with_credentials(username, password)

# ファイルの削除
file = ctx.web.get_file_by_server_relative_url(file_path)
file.delete_object()
ctx.execute_query()

print("ファイルを削除しました。")
