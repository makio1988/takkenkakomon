#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def debug_extraction():
    # PDFファイルのパスを指定
    pdf_path = "uploads/20250730_084025_6.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return
    
    # PDF処理器を初期化
    processor = EnhancedPDFProcessor(use_ocr=False)  # OCRは無効にしてテスト
    
    # テキスト抽出
    print("=== テキスト抽出開始 ===")
    text = processor.extract_text_from_pdf(pdf_path)
    print(f"抽出されたテキスト長: {len(text)}")
    print(f"最初の500文字: {text[:500]}")
    print()
    
    # 年度抽出テスト
    print("=== 年度抽出テスト ===")
    if hasattr(processor, 'first_page_text'):
        print(f"第1ページテキスト長: {len(processor.first_page_text)}")
        print(f"第1ページの最初の200文字: {processor.first_page_text[:200]}")
        year = processor._extract_exam_year(processor.first_page_text)
        print(f"抽出された年度: '{year}'")
    else:
        print("第1ページテキストが利用できません")
    print()
    
    # 問題抽出テスト
    print("=== 問題抽出テスト ===")
    questions = processor.extract_questions_from_text(text)
    print(f"抽出された問題数: {len(questions)}")
    
    if questions:
        # 最初の問題を詳細表示
        first_q = questions[0]
        print(f"\n最初の問題 (問{first_q['question_number']}):")
        print(f"問題文: {first_q['question_text'][:100]}...")
        print(f"選択肢数: {len(first_q.get('options', []))}")
        print(f"年度: {first_q.get('year', 'なし')}")
        
        if first_q.get('options'):
            print("選択肢:")
            for i, opt in enumerate(first_q['options'][:2]):  # 最初の2つだけ表示
                print(f"  {i+1}: {opt[:50]}...")
        else:
            print("選択肢が抽出されていません")
    
    print("\n=== デバッグ完了 ===")

if __name__ == "__main__":
    debug_extraction()
