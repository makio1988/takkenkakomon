#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import sys

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_database():
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    # 問38の詳細を確認
    cursor.execute('SELECT question_number, question_text, options, year FROM questions WHERE question_number = 38')
    result = cursor.fetchone()
    
    if result:
        print(f'問題 {result[0]}:')
        print(f'問題文: {result[1][:100] if result[1] else "None"}...')
        print(f'選択肢: {result[2][:100] if result[2] else "None"}...')
        print(f'年度: {result[3] if result[3] else "None"}')
        print()
        
        # 選択肢をJSONデコードして確認
        if result[2]:
            try:
                options = json.loads(result[2])
                print(f'選択肢数: {len(options)}')
                for i, opt in enumerate(options[:2]):  # 最初の2つだけ表示
                    print(f'  {i+1}: {opt[:50]}...')
            except json.JSONDecodeError:
                print('選択肢のJSONデコードに失敗')
    else:
        print('問題38が見つかりません')
    
    # 総問題数を確認
    cursor.execute('SELECT COUNT(*) FROM questions')
    total = cursor.fetchone()[0]
    print(f'\n総問題数: {total}')
    
    # 年度情報がある問題数を確認
    cursor.execute('SELECT COUNT(*) FROM questions WHERE year IS NOT NULL AND year != ""')
    with_year = cursor.fetchone()[0]
    print(f'年度情報がある問題数: {with_year}')
    
    conn.close()

if __name__ == "__main__":
    check_database()
