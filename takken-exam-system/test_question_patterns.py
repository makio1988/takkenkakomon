#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from pdf_processor import EnhancedPDFProcessor

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_question_patterns():
    # PDFファイルのパスを指定
    pdf_path = "uploads/20250730_084025_6.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return
    
    # PDF処理器を初期化
    processor = EnhancedPDFProcessor(use_ocr=False)
    
    # テキスト抽出
    text = processor.extract_text_from_pdf(pdf_path)
    
    print("=== 問題パターンテスト ===")
    print(f"全テキスト長: {len(text)}")
    print()
    
    # 【問 1】が含まれているかチェック
    if '【問' in text:
        print("✓ '【問' パターンが見つかりました")
        # 【問 1】の周辺を表示
        pos = text.find('【問')
        print(f"位置: {pos}")
        print(f"周辺テキスト: '{text[pos:pos+100]}'")
    else:
        print("✗ '【問' パターンが見つかりません")
    
    print()
    
    # 問題パターンを定義（PDF処理器と同じパターンを使用）
    question_patterns = [
        (r'【問\s*(\d+)】\s*([\s\S]+?)(?=【問\s*\d+】|\Z)', "【問1】形式（更新版）"),
        (r'【問\s*(\d+)】\s*([\s\S]*?)(?=【問\s*\d+】|$)', "【問1】形式（旧版）"),
        (r'問\s*(\d+)[^\d]*?([\s\S]*?)(?=問\s*\d+|$)', "問1形式"),
        (r'第\s*(\d+)\s*問[^\d]*?([\s\S]*?)(?=第\s*\d+\s*問|$)', "第1問形式"),
    ]
    
    # 各パターンをテスト
    for i, (pattern, name) in enumerate(question_patterns):
        try:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            print(f"{name}: {len(matches)} マッチ")
            
            if matches:
                # 最初の3つの問題を表示
                for j, match in enumerate(matches[:3]):
                    question_num = match[0]
                    question_text = match[1][:200] + "..." if len(match[1]) > 200 else match[1]
                    print(f"  問{question_num}: 長さ={len(match[1])}, テキスト='{question_text}'")
                print()
                
                if len(matches) > 10:  # 十分な数の問題が見つかった場合
                    print(f"✓ パターン '{name}' が採用されるべきです")
                    break
            print()
        except Exception as e:
            print(f"パターン {i+1} エラー: {e}")
    
    # テキストの最初の部分を詳細表示
    print("=== テキストの最初の1000文字 ===")
    print(text[:1000])

if __name__ == "__main__":
    test_question_patterns()
