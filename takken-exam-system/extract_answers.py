#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_answer_key_from_pdf(pdf_path):
    """PDFの最終ページから正解データを抽出"""
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return {}
    
    # PDF処理器を初期化
    processor = EnhancedPDFProcessor(use_ocr=False)
    
    # 最終ページのテキストを抽出
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    last_page_num = len(doc) - 1
    last_page = doc[last_page_num]
    last_page_text = last_page.get_text()
    doc.close()
    
    print(f"=== {pdf_path} の最終ページ（ページ {last_page_num + 1}）===")
    print(f"テキスト長: {len(last_page_text)}")
    print("最終ページの内容:")
    print(last_page_text[:1500])  # 最初の1500文字を表示
    print("=" * 50)
    
    # 正解パターンを検索（表形式に対応）
    answer_patterns = [
        # (1) １ や (1) 1 のような括弧付き番号形式
        r'\((\d+)\)\s*([1-4１-４])',
        # 問1 A、問2 B のような形式
        r'問(\d+)\s*([A-E1-4])',
        # 1. A、2. B のような形式
        r'(\d+)[.．]\s*([A-E1-4])',
        # 番号 正解 のような表形式
        r'(\d+)\s+([A-E1-4])',
        # 【問1】A のような形式
        r'【問(\d+)】\s*([A-E1-4])',
    ]
    
    answers = {}
    
    for i, pattern in enumerate(answer_patterns):
        matches = re.findall(pattern, last_page_text, re.MULTILINE)
        if matches:
            print(f"\nパターン {i+1} '{pattern}' で {len(matches)} 件の正解を発見:")
            for match in matches[:10]:  # 最初の10件を表示
                question_num = int(match[0])
                answer = match[1]
                answers[question_num] = answer
                print(f"  問{question_num}: {answer}")
            
            if len(matches) > 10:
                print(f"  ... 他 {len(matches) - 10} 件")
            break
    
    if not answers:
        print("正解データが見つかりませんでした。")
        
        # より詳細な分析
        print("\n=== 詳細分析 ===")
        lines = last_page_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and ('問' in line or any(c in line for c in 'ABCDE12345')):
                print(f"行{i}: '{line}'")
    
    return answers

def main():
    # 両方のPDFファイルから正解を抽出
    pdf_files = [
        "uploads/20250730_084025_6.pdf",  # 令和6年度
        "uploads/20250730_092358_5.pdf",  # 令和5年度
    ]
    
    all_answers = {}
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            answers = extract_answer_key_from_pdf(pdf_path)
            all_answers[pdf_path] = answers
        else:
            print(f"ファイルが見つかりません: {pdf_path}")
    
    print(f"\n=== 抽出結果サマリー ===")
    for pdf_path, answers in all_answers.items():
        print(f"{pdf_path}: {len(answers)} 問の正解を抽出")

if __name__ == "__main__":
    main()
