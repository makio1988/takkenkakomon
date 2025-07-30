#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import sys

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_options():
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    # 問38の選択肢を確認
    cursor.execute('SELECT question_number, options FROM questions WHERE question_number = 38')
    result = cursor.fetchone()
    
    if result:
        options = json.loads(result[1])
        print(f'問題 {result[0]} の選択肢:')
        for i, opt in enumerate(options):
            print(f'{i+1}: {opt}')
            print(f'   長さ: {len(opt)} 文字')
            print('---')
    else:
        print('問38が見つかりません')
    
    conn.close()

if __name__ == "__main__":
    check_options()
