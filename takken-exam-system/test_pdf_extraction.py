#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_questions_from_pdf
import glob

def test_existing_pdfs():
    """既存のPDFファイルをテストする"""
    pdf_files = glob.glob("uploads/*.pdf")
    
    if not pdf_files:
        print("アップロード済みのPDFファイルが見つかりません")
        return
    
    print(f"テスト対象PDFファイル数: {len(pdf_files)}")
    
    for pdf_file in pdf_files[:1]:  # 最初の1つだけテスト
        print(f"\n{'='*50}")
        print(f"テスト中: {pdf_file}")
        print(f"{'='*50}")
        
        questions = extract_questions_from_pdf(pdf_file)
        
        print(f"\n抽出結果:")
        print(f"問題数: {len(questions)}")
        
        for i, q in enumerate(questions[:3]):  # 最初の3問だけ表示
            print(f"\n問題 {i+1}:")
            print(f"  番号: {q['question_number']}")
            print(f"  ジャンル: {q['genre']}")
            try:
                print(f"  内容: {q['question_text'][:100]}...")
            except UnicodeEncodeError:
                print(f"  内容: [文字エンコーディングのため表示省略]")
                print(f"  内容長: {len(q['question_text'])}文字")

if __name__ == "__main__":
    test_existing_pdfs()
