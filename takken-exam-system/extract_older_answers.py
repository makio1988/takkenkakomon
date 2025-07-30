#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import sqlite3
import jaconv
import fitz  # PyMuPDF

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_answer_key_from_pdf(pdf_path):
    """PDFの最終ページから正解データを抽出"""
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return {}
    
    # 最終ページのテキストを抽出
    doc = fitz.open(pdf_path)
    last_page_num = len(doc) - 1
    last_page = doc[last_page_num]
    last_page_text = last_page.get_text()
    doc.close()
    
    print(f"=== {pdf_path} から正解を抽出中 ===")
    print(f"最終ページ（ページ {last_page_num + 1}）のテキスト長: {len(last_page_text)}")
    
    # デバッグ用: 最終ページの内容を一部表示
    print("最終ページの内容（先頭500文字）:")
    print(last_page_text[:500])
    print("=" * 50)
    
    # 正解パターンを検索（表形式に対応）
    answer_patterns = [
        # (1) １ や (1) 1 のような括弧付き番号形式
        r'\((\d+)\)\s*([1-4１-４])',
        # 問1 １ のような形式
        r'問(\d+)\s*([1-4１-４])',
        # 1. １ のような形式
        r'(\d+)[.．]\s*([1-4１-４])',
    ]
    
    answers = {}
    
    for i, pattern in enumerate(answer_patterns):
        matches = re.findall(pattern, last_page_text, re.MULTILINE)
        if matches:
            print(f"パターン {i+1} '{pattern}' で {len(matches)} 件の正解を発見")
            for match in matches[:10]:  # 最初の10件を表示
                question_num = int(match[0])
                answer = match[1]
                # 全角数字を半角に変換
                answer = jaconv.z2h(answer, digit=True)
                answers[question_num] = answer
                print(f"  問{question_num}: {answer}")
            
            if len(matches) > 10:
                print(f"  ... 他 {len(matches) - 10} 件")
            
            if len(matches) >= 40:  # 40問以上あれば採用
                break
    
    print(f"抽出された正解数: {len(answers)}")
    return answers

def update_database_with_older_answers():
    """データベースに古い年度の正解データを更新"""
    
    # PDFファイルと年度のマッピング
    pdf_year_mapping = {
        "uploads/20250730_114422_4.pdf": "令和4年",
        "uploads/20250729_125610_312.pdf": "令和3年", 
        "uploads/20250729_131145_212.pdf": "令和2年",
        # 追加のファイルがあれば以下に追加
        "uploads/20250730_132057_310.pdf": "令和3年",  # 追加ファイル
        "uploads/20250730_132157_212.pdf": "令和2年",  # 追加ファイル
        "uploads/20250730_132207_210.pdf": "令和2年",  # 追加ファイル（10月試験？）
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
        updated_count = 0
        for question_num, correct_answer in answers.items():
            try:
                # 年度と問題番号で該当する問題を検索
                cursor.execute('''
                    UPDATE questions 
                    SET correct_answer = ? 
                    WHERE question_number = ? AND year = ?
                ''', (correct_answer, question_num, year))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    total_updated += 1
                    if updated_count <= 5:  # 最初の5件のみ詳細表示
                        print(f"更新: {year} 問{question_num} → 正解{correct_answer}")
                    
            except Exception as e:
                print(f"更新エラー {year} 問{question_num}: {e}")
        
        print(f"{year}: {updated_count}問の正解データを更新")
        print()
    
    # 変更をコミット
    conn.commit()
    conn.close()
    
    print(f"=== 更新完了 ===")
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
    total_with_answers = 0
    for year, count in results:
        print(f"{year}: {count}問")
        total_with_answers += count
    
    print(f"正解データありの総問題数: {total_with_answers}問")
    
    # 全体の問題数も確認
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]
    print(f"データベース内の総問題数: {total_questions}問")
    
    conn.close()

if __name__ == "__main__":
    update_database_with_older_answers()
