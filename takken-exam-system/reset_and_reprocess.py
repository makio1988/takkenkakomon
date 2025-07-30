#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
import glob
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 拡張PDF処理モジュールを使用
from pdf_processor import extract_questions_from_pdf

def reset_database():
    """データベースをリセットし、PDFファイルを再処理する"""
    print("データベースをリセット中...")
    
    # データベース接続
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    # 既存の問題データを削除
    cursor.execute('DELETE FROM questions')
    print("既存の問題データを削除しました")
    
    # PDFファイル情報を取得
    cursor.execute('SELECT id, file_path FROM pdf_files')
    pdf_files = cursor.fetchall()
    
    total_questions = 0
    
    for pdf_id, file_path in pdf_files:
        print(f"\n処理中: {file_path}")
        
        if os.path.exists(file_path):
            # PDFから問題を抽出
            questions = extract_questions_from_pdf(file_path)
            
            # 問題をデータベースに保存
            for question in questions:
                import json
                # オプションをJSON形式で保存
                options_json = json.dumps(question.get('options', []), ensure_ascii=False)
            
                cursor.execute(
                    "INSERT INTO questions (pdf_id, question_number, question_text, genre, options, year) VALUES (?, ?, ?, ?, ?, ?)",
                    (pdf_id, question['question_number'], question['question_text'], question['genre'], options_json, question.get('year', ''))
                )
            
            print(f"  → {len(questions)}問を抽出・保存しました")
            total_questions += len(questions)
        else:
            print(f"  → ファイルが見つかりません: {file_path}")
    
    conn.commit()
    conn.close()
    
    print(f"\n完了！総問題数: {total_questions}")
    
    # 各ジャンルの問題数を表示
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT genre, COUNT(*) as count 
        FROM questions 
        GROUP BY genre 
        ORDER BY count DESC
    ''')
    genre_counts = cursor.fetchall()
    
    print("\nジャンル別問題数:")
    for genre, count in genre_counts:
        print(f"  {genre}: {count}問")
    
    conn.close()

if __name__ == "__main__":
    reset_database()
