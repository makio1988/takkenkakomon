#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_correct_answers():
    """データベースの正解データを詳細確認"""
    
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    print("=== データベースの正解データ確認 ===")
    
    # テーブル構造を確認
    cursor.execute("PRAGMA table_info(questions)")
    columns = cursor.fetchall()
    print("\nテーブル構造:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 正解データがあるかどうか確認
    cursor.execute('''
        SELECT COUNT(*) as total,
               COUNT(correct_answer) as with_answer,
               COUNT(CASE WHEN correct_answer IS NOT NULL AND correct_answer != '' THEN 1 END) as non_empty_answer
        FROM questions
    ''')
    
    result = cursor.fetchone()
    print(f"\n統計情報:")
    print(f"  総問題数: {result[0]}")
    print(f"  正解データがある問題数: {result[1]}")
    print(f"  空でない正解データがある問題数: {result[2]}")
    
    # サンプルデータを表示
    cursor.execute('''
        SELECT id, question_number, year, correct_answer
        FROM questions 
        WHERE correct_answer IS NOT NULL AND correct_answer != ''
        ORDER BY year DESC, question_number ASC
        LIMIT 10
    ''')
    
    samples = cursor.fetchall()
    print(f"\nサンプルデータ（正解あり）:")
    for row in samples:
        print(f"  ID:{row[0]} {row[2]} 問{row[1]} → 正解:{row[3]}")
    
    # 正解データがない問題も確認
    cursor.execute('''
        SELECT id, question_number, year, correct_answer
        FROM questions 
        WHERE correct_answer IS NULL OR correct_answer = ''
        ORDER BY year DESC, question_number ASC
        LIMIT 5
    ''')
    
    no_answer_samples = cursor.fetchall()
    print(f"\nサンプルデータ（正解なし）:")
    for row in no_answer_samples:
        print(f"  ID:{row[0]} {row[2]} 問{row[1]} → 正解:{row[3]}")
    
    # 特定の問題の詳細確認（宅建業法の最初の問題）
    cursor.execute('''
        SELECT id, question_number, year, correct_answer, genre, question_text
        FROM questions 
        WHERE genre = '宅建業法'
        ORDER BY year DESC, question_number ASC
        LIMIT 3
    ''')
    
    specific_samples = cursor.fetchall()
    print(f"\n宅建業法の問題詳細:")
    for row in specific_samples:
        print(f"  ID:{row[0]} {row[2]} 問{row[1]} ジャンル:{row[4]}")
        print(f"  正解:{row[3]}")
        print(f"  問題文（先頭50文字）:{row[5][:50]}...")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_correct_answers()
