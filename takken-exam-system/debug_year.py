#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def debug_year_extraction():
    # PDFファイルのパスを指定
    pdf_path = "uploads/20250730_084025_6.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return
    
    # PDF処理器を初期化
    processor = EnhancedPDFProcessor(use_ocr=False)
    
    # テキスト抽出
    full_text = processor.extract_text_from_pdf(pdf_path)
    first_page_text = processor.first_page_text
    
    print("=== 年度抽出デバッグ ===")
    print(f"第1ページテキスト長: {len(first_page_text)}")
    print(f"第1ページテキスト:")
    print(first_page_text)
    print()
    
    # 年度抽出パターンをテスト
    reiwa_patterns = [
        r'令和\s*(元|[1-9１-９]\d?)年度?',  # 令和元年、令和６年度...
        r'令和\s*(元|[1-9１-９]\d?)年',     # 令和元年、令和６年...
        r'R\s*(元|[1-9１-９]\d?)',            # R元、R６...
    ]
    
    print("=== パターンテスト ===")
    for i, pattern in enumerate(reiwa_patterns):
        matches = re.findall(pattern, first_page_text)
        print(f"パターン {i+1} '{pattern}': {matches}")
        
        if matches:
            for match in matches:
                print(f"  マッチ: '{match}'")
    
    print()
    
    # 実際の抽出メソッドをテスト
    extracted_year = processor._extract_exam_year(first_page_text)
    print(f"抽出された年度: '{extracted_year}'")
    
    # 全テキストからも試してみる
    extracted_year_full = processor._extract_exam_year(full_text)
    print(f"全テキストから抽出された年度: '{extracted_year_full}'")

if __name__ == "__main__":
    debug_year_extraction()
