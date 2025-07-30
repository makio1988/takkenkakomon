#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pdf2image
import chardet
import jaconv
from typing import List, Dict, Optional, Tuple
import logging

# Windowsエンコーディング設定
if sys.platform.startswith('win'):
    # Windows環境での標準出力エンコーディング設定
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processing.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    """OCR機能付き高精度PDF処理クラス"""
    
    def __init__(self, use_ocr: bool = True, tesseract_path: Optional[str] = None):
        """
        初期化
        
        Args:
            use_ocr: OCRを使用するかどうか
            tesseract_path: TesseractのパスWindows環境では必要な場合がある
        """
        self.use_ocr = use_ocr
        
        # Windows環境でTesseractのパスを設定
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif sys.platform.startswith('win'):
            # 一般的なWindows環境でのTesseractパス
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', ''))
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Tesseractパスを設定: {path}")
                    break
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        PDFからテキストを抽出（PyMuPDF + OCR）
        
        Args:
            file_path: PDFファイルのパス
            
        Returns:
            抽出されたテキスト
        """
        text = ""
        self.first_page_text = ""  # 年度抽出用に1ページ目のテキストを保存
        
        try:
            # まずPyMuPDFでテキスト抽出を試行
            logger.info(f"PyMuPDFでテキスト抽出開始: {file_path}")
            text, self.first_page_text = self._extract_with_pymupdf(file_path)
            
            # テキストが少ない場合やOCRが有効な場合はOCRも実行
            if self.use_ocr and (len(text.strip()) < 100 or self._needs_ocr(text)):
                logger.info("OCRによる追加テキスト抽出を実行")
                ocr_text = self._extract_with_ocr(file_path)
                if len(ocr_text) > len(text):
                    text = ocr_text
                    logger.info("OCRテキストを採用")
                else:
                    logger.info("PyMuPDFテキストを採用")
            
            # エンコーディング正規化
            text = self._normalize_encoding(text)
            
            logger.info(f"テキスト抽出完了。文字数: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"PDF処理エラー: {e}")
            return ""
    
    def _extract_with_pymupdf(self, file_path: str) -> Tuple[str, str]:
        """PyMuPDFでテキスト抽出（全テキストと第1ページを返す）"""
        text = ""
        first_page_text = ""
        try:
            doc = fitz.open(file_path)
            logger.info(f"ページ数: {len(doc)}")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # より詳細なテキスト抽出オプションを使用
                page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)
                
                # エンコーディング問題を解決
                if isinstance(page_text, bytes):
                    try:
                        page_text = page_text.decode('utf-8')
                    except UnicodeDecodeError:
                        detected = chardet.detect(page_text)
                        encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
                        page_text = page_text.decode(encoding, errors='ignore')
                
                # 第1ページのテキストを保存（年度抽出用）
                if page_num == 0:
                    first_page_text = page_text
                
                text += page_text + "\n"
            
            doc.close()
            return text, first_page_text
            
        except Exception as e:
            logger.error(f"PyMuPDF抽出エラー: {e}")
            return "", ""
    
    def _extract_with_ocr(self, file_path: str) -> str:
        """OCRでテキスト抽出"""
        text = ""
        try:
            # PDFを画像に変換
            logger.info("PDFを画像に変換中...")
            images = pdf2image.convert_from_path(
                file_path,
                dpi=300,  # 高解像度で変換
                fmt='PNG'
            )
            
            logger.info(f"変換された画像数: {len(images)}")
            
            # 各画像をOCR処理
            for i, image in enumerate(images):
                logger.debug(f"ページ {i + 1} OCR処理中...")
                
                # 日本語OCR設定
                custom_config = r'--oem 3 --psm 6 -l jpn'
                page_text = pytesseract.image_to_string(
                    image, 
                    config=custom_config,
                    lang='jpn'
                )
                
                text += page_text
                logger.debug(f"ページ {i + 1}: {len(page_text)} 文字抽出")
            
            return text
            
        except Exception as e:
            logger.error(f"OCR抽出エラー: {e}")
            logger.info("Tesseractがインストールされていない可能性があります")
            return ""
    
    def _needs_ocr(self, text: str) -> bool:
        """OCRが必要かどうかを判定"""
        # 日本語文字の割合が低い場合はOCRが必要
        japanese_chars = len(re.findall(r'[ひらがなカタカナ漢字]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return True
        
        japanese_ratio = japanese_chars / total_chars
        return japanese_ratio < 0.3  # 日本語文字が30%未満の場合
    
    def _normalize_encoding(self, text: str) -> str:
        """エンコーディングを正規化"""
        try:
            # 文字化け修正
            if isinstance(text, bytes):
                # バイト列の場合、エンコーディングを検出
                detected = chardet.detect(text)
                encoding = detected.get('encoding', 'utf-8')
                text = text.decode(encoding, errors='ignore')
            
            # 全角・半角正規化
            text = jaconv.normalize(text)
            
            # 改行の正規化
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # 余分な空白の削除
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            return text
            
        except Exception as e:
            logger.error(f"エンコーディング正規化エラー: {e}")
            return text
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, any]]:
        """
        テキストから問題を抽出（選択肢も含む）
        
        Args:
            text: 抽出されたテキスト
            
        Returns:
            問題のリスト
        """
        questions = []
        
        try:
            # テキストの前処理
            text = self._preprocess_text(text)
            
            # 年度を抽出（第1ページのみから）
            exam_year = self._extract_exam_year(self.first_page_text if hasattr(self, 'first_page_text') else text[:1000])
            
            logger.info("問題抽出開始")
            
            # 問題パターンを定義（複数のパターンを試行）
            question_patterns = [
                # 【問1】、【問2】... 形式（最も一般的）
                r'【問\s*(\d+)】\s*([\s\S]+?)(?=【問\s*\d+】|\Z)',
                # 問1、問2... 形式（括弧なし）
                r'問\s*(\d+)[^\d]*?([\s\S]*?)(?=問\s*\d+|$)',
                # 第1問、第2問... 形式
                r'第\s*(\d+)\s*問[^\d]*?([\s\S]*?)(?=第\s*\d+\s*問|$)',
                # [問1]、[問2]... 形式
                r'\[問\s*(\d+)\]\s*([\s\S]*?)(?=\[問\s*\d+\]|$)',
                # 1.、2.、3.、4. 形式
                r'(\d+)\s*[.．]\s*([\s\S]*?)(?=\d+\s*[.．]|$)',
                # [1]、[2]、[3]、[4] 形式
                r'\[(\d+)\]\s*([\s\S]*?)(?=\[\d+\]|$)',
                # 1)、2)、3)、4) 形式
                r'(\d+)\s*[）)]\s*([\s\S]*?)(?=\d+\s*[）)]|$)',
                # 1-、2-、3-、4- 形式
                r'(\d+)\s*[-－]\s*([\s\S]*?)(?=\d+\s*[-－]|$)',
                # No.1、No.2... 形式
                r'No\.?\s*(\d+)\s*([\s\S]*?)(?=No\.?\s*\d+|$)',
                # 1:、2:、3:、4: 形式
                r'(\d+)\s*[:：]\s*([\s\S]*?)(?=\d+\s*[:：]|$)',
                # 単純な番号+スペース形式
                r'(\d{1,2})\s+([\s\S]*?)(?=\d{1,2}\s+|$)',
            ]    
            
            # 各パターンを試行
            all_matches = []
            for i, pattern in enumerate(question_patterns):
                try:
                    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                    logger.debug(f"パターン {i+1}: {len(matches)} 件マッチ")
                    
                    if matches and len(matches) > 1:  # 複数問題が見つかった場合のみ採用
                        all_matches = matches
                        logger.info(f"パターン {i+1} を採用: {len(matches)} 問題")
                        break
                except Exception as e:
                    logger.error(f"パターン {i+1} 処理エラー: {e}")
            
            # マッチしなかった場合は単純分割を試行
            if not all_matches:
                logger.info("パターンマッチ失敗、単純分割を試行")
                all_matches = self._simple_question_split(text)
            
            # 問題を処理
            for match in all_matches:
                try:
                    question_num = int(match[0])
                    full_text = match[1].strip()
                    
                    if len(full_text) < 30:  # 最小文字数チェック
                        continue
                    
                    # 問題文と選択肢を分離
                    question_data = self._parse_question_and_options(question_num, full_text)
                    
                    if question_data:
                        # 年度情報を追加
                        question_data['year'] = exam_year
                        questions.append(question_data)
                        
                except (ValueError, IndexError) as e:
                    logger.debug(f"問題処理スキップ: {e}")
            
            logger.info(f"最終抽出問題数: {len(questions)}")
            
        except Exception as e:
            logger.error(f"問題抽出エラー: {e}")
        
        return questions
    
    def _preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        # 不要な空白や改行を整理
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 複数改行を2つに統一
        text = re.sub(r'[ \t]+', ' ', text)  # 複数スペースを1つに統一
        text = text.strip()
        return text
    
    def _extract_exam_year(self, text: str) -> str:
        """テキストから試験年度を抽出"""
        # 優先度の高い順にパターンを定義（全角数字も含む）
        priority_patterns = [
            # 1. 最優先: 「令和６年度」のような独立した年度表記
            (r'(?<!（)(?<!「)令和\s*(元|[1-9１-９]\d?)年度(?!法改正)', 1),
            # 2. 次優先: 「令和６年」のような独立した年表記
            (r'(?<!（)(?<!「)令和\s*(元|[1-9１-９]\d?)年(?!度法改正)(?!月)(?!日)', 2),
            # 3. 一般: 任意の令和年度
            (r'令和\s*(元|[1-9１-９]\d?)年度?', 3),
            # 4. R表記
            (r'R\s*(元|[1-9１-９]\d?)', 4),
        ]
        
        # 優先度順にパターンを試行
        for pattern, priority in priority_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 最初のマッチを使用
                year_str = matches[0]
                if year_str == '元':
                    return '令和元年'
                else:
                    # 全角数字を半角に変換（６→６）
                    year_num = jaconv.z2h(year_str, digit=True)
                    return f'令和{year_num}年'
                break
        
        # 平成年度のパターンを検索
        heisei_patterns = [
            r'平成\s*([1-9]\d?)年',  # 平成XX年
            r'H\s*([1-9]\d?)',  # HXX
        ]
        
        for pattern in heisei_patterns:
            match = re.search(pattern, text)
            if match:
                year_num = jaconv.z2h(match.group(1), digit=True)
                return f'平成{year_num}年'
        
        # 西暦年度のパターンを検索
        western_patterns = [
            r'(20[0-9]{2})年',  # 20XX年
            r'(20[0-9]{2})',  # 20XX
        ]
        
        for pattern in western_patterns:
            match = re.search(pattern, text)
            if match:
                year = int(match.group(1))
                if year >= 2019:  # 令和元年は2019年
                    reiwa_year = year - 2018
                    if reiwa_year == 1:
                        return '令和元年'
                    else:
                        return f'令和{reiwa_year}年'
                elif year >= 1989:  # 平成元年は1989年
                    heisei_year = year - 1988
                    return f'平成{heisei_year}年'
        
        return ''  # 年度が見つからない場合
    
    def _simple_question_split(self, text: str) -> List[tuple]:
        """単純な問題分割（フォールバック）"""
        # 改行で分割して問題らしい行を探す
        lines = text.split('\n')
        questions = []
        current_question = ""
        question_num = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 問題番号らしい行を検出
            if re.match(r'^\d+[.．）)\s]', line) or re.match(r'^問\s*\d+', line):
                if current_question and question_num > 0:
                    questions.append((str(question_num), current_question))
                
                # 新しい問題開始
                question_num += 1
                current_question = line
            else:
                current_question += "\n" + line
        
        # 最後の問題を追加
        if current_question and question_num > 0:
            questions.append((str(question_num), current_question))
        
        return questions
    
    def _parse_question_and_options(self, question_num: int, full_text: str) -> Dict[str, any]:
        """問題文と選択肢を分離して構造化"""
        try:
            # 選択肢パターンを検索（完全なテキストをキャプチャ、非貪欲的マッチを使用）
            option_patterns = [
                # 半角数字 1 2 3 4 形式（複数行対応、非貪欲的）
                r'(?:^|\n)\s*([1-4])\s+([\s\S]+?)(?=\n\s*[1-4]\s+|\n\s*問\s*\d+|\Z)',
                # 全角数字 １ ２ ３ ４ 形式
                r'(?:^|\n)\s*([１-４])\s+([\s\S]+?)(?=\n\s*[１-４]\s+|\n\s*問\s*\d+|\Z)',
                # 数字+ピリオド 1. 2. 3. 4. 形式
                r'(?:^|\n)\s*([1-4])[.．]\s*([\s\S]+?)(?=\n\s*[1-4][.．]|\n\s*問\s*\d+|\Z)',
                # 括弧付き数字 (1) (2) (3) (4) 形式
                r'(?:^|\n)\s*\(([1-4１-４])\)\s*([\s\S]+?)(?=\n\s*\([1-4１-４]\)|\n\s*問\s*\d+|\Z)',
                # 丸数字 ① ② ③ ④ 形式
                r'(?:^|\n)\s*([①-④])\s*([\s\S]+?)(?=\n\s*[①-④]|\n\s*問\s*\d+|\Z)',
                # カタカナ ア イ ウ エ 形式
                r'(?:^|\n)\s*([ア-エ])\s*[.．]?\s*([\s\S]+?)(?=\n\s*[ア-エ]|\n\s*問\s*\d+|\Z)',
            ]
            
            options = []
            question_text = full_text
            best_split_pos = len(full_text)  # 最初の選択肢位置
            
            # 選択肢を抽出
            for i, pattern in enumerate(option_patterns):
                matches = re.findall(pattern, full_text, re.MULTILINE | re.DOTALL)
                logger.debug(f"パターン {i+1}: {len(matches)} マッチ")
                
                if len(matches) >= 3:  # 3つ以上の選択肢があれば採用
                    logger.debug(f"パターン {i+1} を採用: {len(matches)} マッチ")
                    
                    # 選択肢をクリーンアップ（タプルの2番目要素がテキスト）
                    raw_options = [match[1] for match in matches if len(match) >= 2 and match[1].strip()]
                    logger.debug(f"生の選択肢数: {len(raw_options)}")
                    
                    options = [self._clean_option_text(opt) for opt in raw_options]
                    options = [opt for opt in options if opt.strip()]  # 空の選択肢を除去
                    logger.debug(f"クリーンアップ後の選択肢数: {len(options)}")
                    
                    if options:  # クリーンアップ後に選択肢が残っているかチェック
                        # 最初の選択肢の位置を見つけて問題文を分離
                        first_option_match = re.search(pattern, full_text, re.MULTILINE | re.DOTALL)
                        if first_option_match:
                            split_pos = first_option_match.start()
                            if split_pos < best_split_pos:
                                best_split_pos = split_pos
                                question_text = full_text[:split_pos].strip()
                        
                        logger.debug(f"パターン {i+1} 最終採用: {len(options)} 選択肢抽出")
                        break
                    else:
                        logger.debug(f"パターン {i+1}: クリーンアップ後に選択肢が空")
                
                # 問題文が空の場合は全テキストを使用
                if not question_text.strip():
                    question_text = full_text
            
            # 問題文の最後の整理（不完全な文を除去）
            question_text = self._clean_question_text(question_text)
            
            # ジャンル分類
            genre = self._classify_question_genre(question_text)
            
            result = {
                'question_number': question_num,
                'question_text': question_text,
                'options': options,
                'genre': genre
            }
            
            logger.debug(f"問題 {question_num}: テキスト長={len(question_text)}, 選択肢数={len(options)}")
            return result
            
        except Exception as e:
            logger.error(f"問題解析エラー (問題{question_num}): {e}")
            return None
    
    def _clean_question_text(self, text: str) -> str:
        """問題文をクリーンアップ"""
        # 基本的なクリーンアップ
        text = text.strip()
        
        # 先頭の不要な文字を除去（】、【、」、「など）
        text = re.sub(r'^[】【」「』『］［〉〈）（〕〔〗〖〙〘〛〚〝〜〟〞〡〠]+', '', text)
        
        # 改行をスペースに置き換え（読みやすくするため）
        text = re.sub(r'\n+', ' ', text)
        
        # 複数のスペースを一つに統一
        text = re.sub(r'\s+', ' ', text)
        
        # 最後が不完全な場合は削除
        if text.endswith(('、', '。', 'で', 'に', 'を', 'が', 'は', 'と')):
            pass  # 正常な終わり
        elif len(text) > 10 and not text[-1] in '。？！':
            # 最後の不完全な単語を削除
            words = text.split()
            if len(words) > 1:
                last_word = words[-1]
                if len(last_word) < 3:  # 短い不完全な単語
                    text = ' '.join(words[:-1])
        
        # 最終クリーンアップ
        text = text.strip()
        
        return text
    
    def _clean_option_text(self, text: str) -> str:
        """選択肢テキストをクリーンアップ（完全なテキストを保持）"""
        if not text:
            return ""
            
        # 基本的なクリーンアップ
        text = text.strip()
        
        # 改行をスペースに置き換え（読みやすくするため）
        text = re.sub(r'\n+', ' ', text)
        
        # 複数のスペースを一つに統一
        text = re.sub(r'\s+', ' ', text)
        
        # 不要な文字を最小限で除去（テキストを切り捨てない）
        text = re.sub(r'\d+\s*ページ\s*$', '', text)  # 末尾のページ番号のみ除去
        text = re.sub(r'問\s*\d+\s*$', '', text)  # 末尾の問題番号のみ除去
        
        # ページフッター情報を除去
        text = re.sub(r'\s*-\s*\d+\s*-\s*〈.*?〉.*?【.*$', '', text)  # 「- 19 - 〈宅地建物取引士資格試験〉 【」形式
        text = re.sub(r'\s*〈.*?〉.*$', '', text)  # 試験名などの情報
        text = re.sub(r'\s*【.*$', '', text)  # 【で始まる不完全な情報
        
        # 最終クリーンアップ
        text = text.strip()
        
        # デバッグ情報
        logger.debug(f"オプションテキストクリーンアップ後: {len(text)} 文字 - {text[:50]}...")
        
        return text
    
    def _classify_question_genre(self, question_text: str) -> str:
        """問題文からジャンルを分類"""
        # 宅建業法関連キーワード
        if any(keyword in question_text for keyword in [
            '宅建業法', '宅地建物取引業法', '宅建業者', '宅地建物取引士',
            '重要事項説明', '37条書面', '35条書面', '媒介契約', '宅建業'
        ]):
            return 'takken_law'
        
        # 民法関連キーワード
        elif any(keyword in question_text for keyword in [
            '民法', '契約', '債権', '物権', '所有権', '抵当権', '賃貸借',
            '売買', '贈与', '委任', '請負', '損害賠償', '時効'
        ]):
            return 'civil_law'
        
        # 法令制限関連キーワード
        elif any(keyword in question_text for keyword in [
            '都市計画法', '建築基準法', '国土利用計画法', '農地法',
            '土地区画整理法', '宅地造成等規制法', '用途地域', '建ぺい率'
        ]):
            return 'legal_restrictions'
        
        else:
            return 'others'


def extract_questions_from_pdf(file_path: str, use_ocr: bool = True) -> List[Dict[str, any]]:
    """
    PDFから問題を抽出する関数（既存のapp.pyとの互換性維持）
    
    Args:
        file_path: PDFファイルのパス
        use_ocr: OCRを使用するかどうか
        
    Returns:
        問題のリスト
    """
    processor = EnhancedPDFProcessor(use_ocr=use_ocr)
    
    # テキスト抽出
    text = processor.extract_text_from_pdf(file_path)
    
    if not text.strip():
        logger.warning("テキストが抽出されませんでした")
        return []
    
    # 問題抽出
    questions = processor.extract_questions_from_text(text)
    
    return questions


if __name__ == "__main__":
    # テスト用
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        if os.path.exists(test_file):
            questions = extract_questions_from_pdf(test_file)
            print(f"抽出された問題数: {len(questions)}")
            for q in questions[:3]:  # 最初の3問を表示
                print(f"問題 {q['question_number']}: {q['question_text'][:100]}...")
        else:
            print(f"ファイルが見つかりません: {test_file}")
    else:
        print("使用方法: python pdf_processor.py <PDFファイルパス>")
