import subprocess


def access_open():
    app_path = r'C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE'
    file_paths = [
        r'C:\☆☆\00_Access_postgre\000_Postgre.accdb',
        r'C:\☆☆\00_Access_postgre\00_生産計画.accdb',
        r'C:\Projects_workspace\02_access\Database1.accdb'
    ]
    
    for file_path in file_paths:
        try:
            subprocess.Popen([app_path, file_path])
        except Exception as e:
            print(f"Error opening {file_path}: {e}")

if __name__ == "__main__":
    access_open()
