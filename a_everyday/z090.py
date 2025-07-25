def run_z900_filecopy_txt():
    import z900_filecopy_txt

def run_z090_zp138_txt():
    import z090_zp138_txt

def run_z090_zp138_field_mapping():
    import z090_zp138_field_mapping

def run_a1_app_open_ac():
    import a1_app_open_ac
    a1_app_open_ac.access_open()


def main():
    run_z900_filecopy_txt()
    run_z090_zp138_txt()  # 順次実行
    run_z090_zp138_field_mapping()
    run_a1_app_open_ac()


if __name__ == '__main__':
    main()


