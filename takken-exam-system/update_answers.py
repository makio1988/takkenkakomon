#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import sqlite3
import jaconv
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_answer_key_from_pdf(pdf_path):
    """PDFの最終ページから正解データを抽出"""
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return {}
    
    # 最終ページのテキストを抽出
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    last_page_num = len(doc) - 1
    last_page = doc[last_page_num]
    last_page_text = last_page.get_text()
    doc.close()
    
    print(f"=== {pdf_path} から正解を抽出中 ===")
    
    # 正解パターンを検索（表形式に対応）
    answer_patterns = [
        # (1) １ や (1) 1 のような括弧付き番号形式
        r'\((\d+)\)\s*([1-4１-４])',
    ]
    
    answers = {}
    
    for pattern in answer_patterns:
        matches = re.findall(pattern, last_page_text, re.MULTILINE)
        if matches:
            print(f"パターン '{pattern}' で {len(matches)} 件の正解を発見")
            for match in matches:
                question_num = int(match[0])
                answer = match[1]
                # 全角数字を半角に変換
                answer = jaconv.z2h(answer, digit=True)
                answers[question_num] = answer
            break
    
    print(f"抽出された正解数: {len(answers)}")
    return answers

def update_database_with_answers():
    """データベースに正解データを更新"""
    
    # PDFファイルと年度のマッピング
    pdf_year_mapping = {
        "uploads/20250730_084025_6.pdf": "令和6年",
        "uploads/20250730_092358_5.pdf": "令和5年",
    }
    
    # データベース接続
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    total_updated = 0
    
    for pdf_path, year in pdf_year_mapping.items():
        if not os.path.exists(pdf_path):
            print(f"PDFファイルが見つかりません: {pdf_path}")
            continue
            
        # 正解データを抽出
        answers = extract_answer_key_from_pdf(pdf_path)
        
        if not answers:
            print(f"正解データが抽出できませんでした: {pdf_path}")
            continue
        
        # データベースの該当する問題を更新
        for question_num, correct_answer in answers.items():
            try:
                # 年度と問題番号で該当する問題を検索
                cursor.execute('''
                    UPDATE questions 
                    SET correct_answer = ? 
                    WHERE question_number = ? AND year = ?
                ''', (correct_answer, question_num, year))
                
                if cursor.rowcount > 0:
                    print(f"更新: {year} 問{question_num} → 正解{correct_answer}")
                    total_updated += 1
                else:
                    print(f"該当なし: {year} 問{question_num}")
                    
            except Exception as e:
                print(f"更新エラー {year} 問{question_num}: {e}")
    
    # 変更をコミット
    conn.commit()
    conn.close()
    
    print(f"\n=== 更新完了 ===")
    print(f"合計 {total_updated} 問の正解データを更新しました")
    
    # 更新結果を確認
    verify_answers()

def verify_answers():
    """正解データの更新結果を確認"""
    
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    # 正解データが設定された問題数を確認
    cursor.execute('''
        SELECT year, COUNT(*) as count
        FROM questions 
        WHERE correct_answer IS NOT NULL AND correct_answer != ''
        GROUP BY year
        ORDER BY year DESC
    ''')
    
    results = cursor.fetchall()
    
    print(f"\n=== 正解データ設定状況 ===")
    for year, count in results:
        print(f"{year}: {count}問")
    
    # サンプルデータを表示
    cursor.execute('''
        SELECT question_number, year, correct_answer
        FROM questions 
        WHERE correct_answer IS NOT NULL AND correct_answer != ''
        ORDER BY year DESC, question_number ASC
        LIMIT 10
    ''')
    
    samples = cursor.fetchall()
    
    print(f"\n=== サンプルデータ ===")
    for question_num, year, correct_answer in samples:
        print(f"{year} 問{question_num}: 正解{correct_answer}")
    
    conn.close()

if __name__ == "__main__":
    update_database_with_answers()
