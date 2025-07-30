#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
宅建試験システム セットアップスクリプト
OCRとPDF処理の依存関係をインストールします
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Python バージョンチェック"""
    if sys.version_info < (3, 7):
        print("Python 3.7以上が必要です")
        return False
    print(f"Python {sys.version} 検出")
    return True

def install_requirements():
    """requirements.txt から依存関係をインストール"""
    print("依存関係をインストール中...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依存関係のインストールが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依存関係のインストールに失敗しました: {e}")
        return False

def check_tesseract():
    """Tesseract OCRの確認"""
    print("Tesseract OCRを確認中...")
    
    if platform.system() == "Windows":
        # Windows環境でのTesseractパス候補
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                print(f"Tesseract が見つかりました: {path}")
                return True
        
        print("⚠️  Tesseract OCRがインストールされていません")
        print("以下の手順でインストールしてください:")
        print("1. https://github.com/UB-Mannheim/tesseract/wiki からWindows版をダウンロード")
        print("2. インストール時に「Additional language data」で日本語を選択")
        print("3. インストール後、システムを再起動")
        return False
    
    else:
        # Linux/Mac環境
        try:
            subprocess.check_call(["tesseract", "--version"], stdout=subprocess.DEVNULL)
            print("Tesseract が見つかりました")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Tesseract OCRがインストールされていません")
            print("以下のコマンドでインストールしてください:")
            if platform.system() == "Darwin":  # macOS
                print("brew install tesseract tesseract-lang")
            else:  # Linux
                print("sudo apt-get install tesseract-ocr tesseract-ocr-jpn")
            return False

def create_directories():
    """必要なディレクトリを作成"""
    directories = ["uploads", "logs"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"ディレクトリを作成しました: {directory}")

def test_pdf_processing():
    """PDF処理のテスト"""
    print("PDF処理機能をテスト中...")
    try:
        from pdf_processor import EnhancedPDFProcessor
        processor = EnhancedPDFProcessor(use_ocr=False)  # OCRなしでテスト
        print("PDF処理モジュールが正常に読み込まれました")
        return True
    except ImportError as e:
        print(f"PDF処理モジュールの読み込みに失敗しました: {e}")
        return False

def main():
    """メイン処理"""
    print("=== 宅建試験システム セットアップ ===")
    print()
    
    # Python バージョンチェック
    if not check_python_version():
        return False
    
    # 依存関係インストール
    if not install_requirements():
        return False
    
    # ディレクトリ作成
    create_directories()
    
    # PDF処理テスト
    if not test_pdf_processing():
        return False
    
    # Tesseract チェック
    tesseract_ok = check_tesseract()
    
    print()
    print("=== セットアップ完了 ===")
    
    if tesseract_ok:
        print("✅ すべての機能が利用可能です")
        print("OCR機能付きでPDF読み取り精度が向上します")
    else:
        print("⚠️  基本機能は利用可能ですが、OCR機能は無効です")
        print("より高精度なPDF読み取りにはTesseractのインストールを推奨します")
    
    print()
    print("アプリケーションを起動するには:")
    print("python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
