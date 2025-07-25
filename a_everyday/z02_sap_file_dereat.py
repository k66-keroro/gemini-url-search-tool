import os

# Define the target file name
target_file_name = "Basis (1) の ワークシート.xlsx"

def main():
    # Walk through the entire C drive
    for root, dirs, files in os.walk("C:\\"):
        # Check if the target file is in the current directory
        if target_file_name in files:
            # Construct the full file path
            file_path = os.path.join(root, target_file_name)
            try:
                # Delete the file
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

print("File deletion process completed.")
# z02_sap_file_dereat.py の例
if __name__ == '__main__':
    # メインの処理を書く
    main()