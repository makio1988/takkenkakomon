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

def extract_all_answers_from_pdf(pdf_path):
    """PDFの最終ページから全ての正解データを抽出（改良版）"""
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return {}
    
    # 最終ページのテキストを抽出
    doc = fitz.open(pdf_path)
    last_page_num = len(doc) - 1
    last_page = doc[last_page_num]
    last_page_text = last_page.get_text()
    doc.close()
    
    print(f"=== {pdf_path} から全正解を抽出中 ===")
    print(f"最終ページ（ページ {last_page_num + 1}）のテキスト長: {len(last_page_text)}")
    
    # 正解パターンを検索（より包括的に）
    answer_patterns = [
        # (1) １ や (1) 1 のような括弧付き番号形式（最も一般的）
        r'\((\d+)\)\s*([1-4１-４])',
        # 問1 １ のような形式
        r'問(\d+)\s*([1-4１-４])',
        # 1. １ のような形式
        r'(\d+)[.．]\s*([1-4１-４])',
        # 番号 正解 の表形式（改行を含む）
        r'(\d+)\s*\n\s*([1-4１-４])',
    ]
    
    answers = {}
    best_pattern = None
    max_matches = 0
    
    # 全パターンを試して最も多くマッチするものを選択
    for i, pattern in enumerate(answer_patterns):
        matches = re.findall(pattern, last_page_text, re.MULTILINE | re.DOTALL)
        print(f"パターン {i+1} '{pattern}': {len(matches)} 件")
        
        if len(matches) > max_matches:
            max_matches = len(matches)
            best_pattern = i
            answers = {}
            
            for match in matches:
                question_num = int(match[0])
                answer = match[1]
                # 全角数字を半角に変換
                answer = jaconv.z2h(answer, digit=True)
                answers[question_num] = answer
    
    if best_pattern is not None:
        print(f"採用パターン: {best_pattern + 1} ({max_matches} 件)")
        
        # 抽出結果の詳細表示
        sorted_answers = sorted(answers.items())
        print("抽出された正解:")
        for i, (q_num, ans) in enumerate(sorted_answers):
            if i < 10:  # 最初の10件
                print(f"  問{q_num}: {ans}")
            elif i == 10:
                print(f"  ... 他 {len(sorted_answers) - 10} 件")
                break
    
    print(f"抽出された正解数: {len(answers)}")
    return answers

def update_all_older_answers():
    """全ての古い年度の正解データを完全更新"""
    
    # PDFファイルと年度のマッピング
    pdf_year_mapping = {
        "uploads/20250730_114422_4.pdf": "令和4年",
        "uploads/20250729_125610_312.pdf": "令和3年", 
        "uploads/20250729_131145_212.pdf": "令和2年",
        "uploads/20250730_132057_310.pdf": "令和3年",  # 10月試験
        "uploads/20250730_132157_212.pdf": "令和2年",  # 重複チェック用
        "uploads/20250730_132207_210.pdf": "令和2年",  # 10月試験
    }
    
    # データベース接続
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    total_updated = 0
    year_stats = {}
    
    for pdf_path, year in pdf_year_mapping.items():
        if not os.path.exists(pdf_path):
            print(f"PDFファイルが見つかりません: {pdf_path}")
            continue
            
        # 正解データを抽出
        answers = extract_all_answers_from_pdf(pdf_path)
        
        if not answers:
            print(f"正解データが抽出できませんでした: {pdf_path}")
            continue
        
        # データベースの該当する問題を更新
        updated_count = 0
        for question_num, correct_answer in answers.items():
            try:
                # 年度と問題番号で該当する問題を検索・更新
                cursor.execute('''
                    UPDATE questions 
                    SET correct_answer = ? 
                    WHERE question_number = ? AND year = ?
                ''', (correct_answer, question_num, year))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    total_updated += 1
                    
            except Exception as e:
                print(f"更新エラー {year} 問{question_num}: {e}")
        
        # 年度別統計を更新
        if year not in year_stats:
            year_stats[year] = 0
        year_stats[year] += updated_count
        
        print(f"{year}: {updated_count}問の正解データを更新")
        print()
    
    # 変更をコミット
    conn.commit()
    conn.close()
    
    print(f"=== 更新完了 ===")
    print(f"合計 {total_updated} 問の正解データを更新しました")
    
    print("\n年度別更新統計:")
    for year, count in sorted(year_stats.items(), reverse=True):
        print(f"  {year}: {count}問")
    
    # 最終確認
    verify_final_results()

def verify_final_results():
    """最終的な正解データの状況を確認"""
    
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
    
    print(f"\n=== 最終的な正解データ設定状況 ===")
    total_with_answers = 0
    for year, count in results:
        print(f"{year}: {count}問")
        total_with_answers += count
    
    print(f"\n正解データありの総問題数: {total_with_answers}問")
    
    # 全体の問題数も確認
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]
    print(f"データベース内の総問題数: {total_questions}問")
    
    # カバー率を計算
    coverage = (total_with_answers / total_questions) * 100 if total_questions > 0 else 0
    print(f"正解データカバー率: {coverage:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    update_all_older_answers()
