import multiprocessing

def run_sap_file_dereat():
    import z02_sap_file_dereat  # このスクリプトが直接実行されないことを確認

def run_z090_zp138_hiki_pg():
    import z090_zp138_hiki_pg  # このスクリプトが直接実行されないことを確認

def main():
    # プロセスを作成
    process2 = multiprocessing.Process(target=run_sap_file_dereat)
    process3 = multiprocessing.Process(target=run_z090_zp138_hiki_pg)

    # プロセスを開始
    process2.start()
    process3.start()

    # プロセスの終了を待つ
    process2.join()
    process3.join()

if __name__ == '__main__':
    # Windowsのプロセス生成でfreeze_supportを呼び出し
    multiprocessing.freeze_support()
    main()
