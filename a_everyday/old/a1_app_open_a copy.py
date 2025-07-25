import subprocess

def notion_open():
    app_path4 = r'C:\Users\sem3171\AppData\Local\Programs\Notion\Notion.exe'
    try:
        subprocess.Popen([app_path4])
        print('Notionを開きました')
    except Exception as e:
        print(f'エラーが発生しました: {e}')

print('Notionを開きます')
notion_open()
