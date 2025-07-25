# logger.py

import logging
import os

def setup_logger(log_file='script_execution.log'):
    """ ログの設定を行う """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        filemode='a'  # 追記モードに設定
    )

def log_info(message):
    """ 情報メッセージをログに記録 """
    logging.info(message)

def log_error(message):
    """ エラーメッセージをログに記録 """
    logging.error(message)

def log_warning(message):
    """ 警告メッセージをログに記録 """
    logging.warning(message)

def log_duration(start_time, end_time, task_name):
    """ 処理時間をログに記録 """
    duration = end_time - start_time
    logging.info(f"{task_name}が完了しました。処理時間: {duration:.2f}秒")
