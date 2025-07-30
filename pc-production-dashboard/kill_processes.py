#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pythonプロセスを強制終了するスクリプト
"""

import subprocess
import sys
import os

def kill_python_processes():
    """Pythonプロセスを強制終了"""
    try:
        # taskkillコマンドでPythonプロセスを終了
        result = subprocess.run(
            ['taskkill', '/f', '/im', 'python.exe'],
            capture_output=True,
            text=True
        )
        
        print("Python processes killed:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Error killing processes: {e}")

if __name__ == "__main__":
    kill_python_processes()
    print("All Python processes terminated.")
    input("Press Enter to exit...")