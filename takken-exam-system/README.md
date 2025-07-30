# 宅建過去問PDF管理・出題システム

宅建（宅地建物取引士）の過去問PDFファイルを管理し、ジャンル別に問題を出題するWebアプリケーションです。

## 機能

- **PDFアップロード**: 宅建の過去問PDFファイルをアップロード・保管
- **自動問題抽出**: PDFから問題を自動的に抽出・分類
- **ジャンル別出題**: 以下のジャンルから選択して問題を出題
  - 宅建業法
  - 民法
  - 法令等の制限
  - その他
  - ランダム
- **ファイル管理**: アップロード済みファイルと抽出問題数の確認

## セットアップ

### 自動セットアップ（推奨）

```bash
python setup.py
```

### 手動セットアップ

#### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### 2. Tesseract OCRのインストール（高精度PDF読み取り用）

**Windows:**
1. [Tesseract Windows版](https://github.com/UB-Mannheim/tesseract/wiki)をダウンロード
2. インストール時に「Additional language data」で日本語を選択
3. システムを再起動

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-jpn
```

#### 3. アプリケーションの起動

```bash
python app.py
```

#### 4. ブラウザでアクセス

http://localhost:5000 にアクセスしてください。

## 使い方

1. **PDFアップロード**: 「アップロード」ページから宅建の過去問PDFファイルをアップロード
2. **ジャンル選択**: ホームページでお好みのジャンルを選択
3. **問題挑戦**: 抽出された問題に挑戦

## 技術仕様

- **フレームワーク**: Flask (Python)
- **データベース**: SQLite
- **PDF処理**: PyMuPDF + PyPDF2 + OCR (Tesseract)
- **OCR機能**: pytesseract + pdf2image (日本語対応)
- **文字エンコーディング**: UTF-8 (Windows互換)
- **UI**: Bootstrap 5 + Font Awesome
- **ファイルサイズ制限**: 16MB

## 新機能・改善点

### 文字化け対策
- Windows環境での文字エンコーディング問題を修正
- UTF-8での統一処理により日本語表示を改善
- chardetライブラリによる自動エンコーディング検出

### PDF読み取り精度向上
- **PyMuPDF**: 高精度なテキスト抽出
- **OCR機能**: 画像化されたPDFからもテキスト抽出可能
- **日本語最適化**: 日本語文字の認識精度を向上
- **複数パターン対応**: 様々な問題形式に対応した抽出パターン

### 処理の流れ
1. PyMuPDFでテキスト抽出を試行
2. 抽出テキストが不十分な場合、OCRを実行
3. より精度の高い結果を採用
4. 文字エンコーディングを正規化
5. 問題パターンマッチングで構造化

## データベース構造

### pdf_files テーブル
- id: ファイルID
- filename: ファイル名
- original_name: 元のファイル名
- upload_date: アップロード日時
- file_path: ファイルパス

### questions テーブル
- id: 問題ID
- pdf_id: 関連PDFファイルID
- question_text: 問題文
- genre: ジャンル
- question_number: 問題番号

## 注意事項

- PDFファイルの形式によっては、問題抽出の精度が変わる場合があります
- 問題の自動分類は基本的なキーワードマッチングを使用しています
- より高精度な抽出・分類が必要な場合は、PDFの構造に応じてカスタマイズが必要です

## カスタマイズ

`extract_questions_from_pdf()` 関数と `classify_question_genre()` 関数を、お使いのPDFファイルの形式に合わせて調整してください。
