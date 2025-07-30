#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def debug_option_patterns():
    # PDFファイルのパスを指定
    pdf_path = "uploads/20250730_084025_6.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return
    
    # PDF処理器を初期化
    processor = EnhancedPDFProcessor(use_ocr=False)
    
    # テキスト抽出
    text = processor.extract_text_from_pdf(pdf_path)
    
    # 問1の部分を抽出して詳細に調べる
    problem_1_match = re.search(r'【問\s*1】(.*?)(?=【問\s*2】|$)', text, re.DOTALL)
    if problem_1_match:
        problem_1_text = problem_1_match.group(1)
        print("=== 問1の全テキスト ===")
        print(problem_1_text[:800])
        print()
        
        # 選択肢らしき部分を探す
        print("=== 数字で始まる行を検索 ===")
        lines = problem_1_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and (line[0].isdigit() or line[0] in '１２３４①②③④'):
                print(f"行{i}: '{line[:100]}'")
        print()
        
        # 各パターンをテスト
        patterns = [
            (r'(?:^|\n)\s*([1-4])\s+([\s\S]+?)(?=\n\s*[1-4]\s+|\n\s*問\s*\d+|\Z)', "半角数字 1 2 3 4"),
            (r'(?:^|\n)\s*([１-４])\s+([\s\S]+?)(?=\n\s*[１-４]\s+|\n\s*問\s*\d+|\Z)', "全角数字 １ ２ ３ ４"),
            (r'(?:^|\n)\s*([1-4])[.．]\s*([\s\S]+?)(?=\n\s*[1-4][.．]|\n\s*問\s*\d+|\Z)', "数字+ピリオド"),
            (r'(?:^|\n)\s*\(([1-4１-４])\)\s*([\s\S]+?)(?=\n\s*\([1-4１-４]\)|\n\s*問\s*\d+|\Z)', "括弧付き数字"),
            (r'(?:^|\n)\s*([①-④])\s*([\s\S]+?)(?=\n\s*[①-④]|\n\s*問\s*\d+|\Z)', "丸数字"),
            (r'(?:^|\n)\s*([ア-エ])\s*[.．]?\s*([\s\S]+?)(?=\n\s*[ア-エ]|\n\s*問\s*\d+|\Z)', "カタカナ"),
        ]
        
        print("=== パターンマッチングテスト ===")
        for pattern, name in patterns:
            matches = re.findall(pattern, problem_1_text, re.MULTILINE | re.DOTALL)
            print(f"{name}: {len(matches)} マッチ")
            if matches:
                for i, match in enumerate(matches[:2]):  # 最初の2つだけ表示
                    print(f"  {i+1}: '{match[0]}' -> '{match[1][:50]}...'")
            print()
    else:
        print("問1が見つかりませんでした")

if __name__ == "__main__":
    debug_option_patterns()
