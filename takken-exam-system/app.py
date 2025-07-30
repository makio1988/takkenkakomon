#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from pdf_processor import extract_questions_from_pdf

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 問題のジャンル定義
GENRES = {
    'takken_law': '宅建業法',
    'civil_law': '民法',
    'legal_restrictions': '法令等の制限',
    'others': 'その他',
    'random': 'ランダム'
}

def init_db():
    """データベースの初期化"""
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    # PDFファイル管理テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL
        )
    ''')
    
    # 問題データテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            genre TEXT,
            question_number INTEGER,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files (id)
        )
    ''')
    
    # 既存のテーブルにoptions列が存在しない場合は追加
    try:
        cursor.execute('ALTER TABLE questions ADD COLUMN options TEXT')
        logger.info('options列を追加しました')
    except sqlite3.OperationalError:
        # 列が既に存在する場合は無視
        pass
    
    # 既存のテーブルにyear列が存在しない場合は追加
    try:
        cursor.execute('ALTER TABLE questions ADD COLUMN year TEXT')
        logger.info('year列を追加しました')
    except sqlite3.OperationalError:
        # 列が既に存在する場合は無視
        pass
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """アップロード可能なファイル形式をチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

# PDF処理は pdf_processor.py の extract_questions_from_pdf 関数を使用

def classify_question_genre(question_text):
    """問題文からジャンルを分類"""
    if any(keyword in question_text for keyword in ['宅建業法', '宅地建物取引業法', '免許', '営業保証金']):
        return 'takken_law'
    elif any(keyword in question_text for keyword in ['民法', '契約', '所有権', '債権']):
        return 'civil_law'
    elif any(keyword in question_text for keyword in ['都市計画法', '建築基準法', '国土利用計画法']):
        return 'legal_restrictions'
    else:
        return 'others'

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html', genres=GENRES)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """PDFファイルのアップロード"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルが選択されていません')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('ファイルが選択されていません')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # アップロードフォルダが存在しない場合は作成
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # データベースに保存
            conn = sqlite3.connect('takken_exam.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pdf_files (filename, original_name, file_path)
                VALUES (?, ?, ?)
            ''', (filename, file.filename, file_path))
            pdf_id = cursor.lastrowid
            
            # PDFから問題を抽出
            questions = extract_questions_from_pdf(file_path)
            
            # 問題をデータベースに保存
            for question in questions:
                # 選択肢をJSON文字列として保存
                # オプションをJSON形式で保存
                options_json = json.dumps(question.get('options', []), ensure_ascii=False)
                
                cursor.execute(
                    "INSERT INTO questions (pdf_id, question_number, question_text, genre, options, year) VALUES (?, ?, ?, ?, ?, ?)",
                    (pdf_id, question['question_number'], question['question_text'], question['genre'], options_json, question.get('year', ''))
                )
            
            conn.commit()
            conn.close()
            
            flash(f'ファイルが正常にアップロードされました。{len(questions)}問の問題を抽出しました。')
            return redirect(url_for('index'))
        else:
            flash('PDFファイルのみアップロード可能です')
    
    return render_template('upload.html')

@app.route('/question/<genre>')
def get_question(genre):
    """指定されたジャンルから問題を取得"""
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    
    if genre == 'random':
        cursor.execute('SELECT * FROM questions WHERE correct_answer IS NOT NULL AND correct_answer != "" ORDER BY RANDOM() LIMIT 1')
    else:
        cursor.execute('SELECT * FROM questions WHERE genre = ? AND correct_answer IS NOT NULL AND correct_answer != "" ORDER BY RANDOM() LIMIT 1', (genre,))
    
    question = cursor.fetchone()
    conn.close()
    
    if question:
        import json
        # データベースから選択肢を取得してJSONデコード
        try:
            options = json.loads(question[3]) if question[3] else []  # optionsはインデックス3
        except (json.JSONDecodeError, TypeError):
            options = []
        
        question_data = {
            'id': question[0],                    # id
            'question_text': question[2],        # question_text  
            'options': options,                  # options (JSON)
            'correct_answer': question[4],       # correct_answer
            'genre': GENRES.get(question[6], question[6]),  # genre
            'question_number': question[7],      # question_number
            'year': question[8] if len(question) > 8 else ''  # year
        }
        return render_template('question.html', question=question_data)
    else:
        flash('該当するジャンルの問題が見つかりません')
        return redirect(url_for('index'))

@app.route('/files')
def list_files():
    """アップロード済みファイル一覧"""
    conn = sqlite3.connect('takken_exam.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pf.*, COUNT(q.id) as question_count
        FROM pdf_files pf
        LEFT JOIN questions q ON pf.id = q.pdf_id
        GROUP BY pf.id
        ORDER BY pf.upload_date DESC
    ''')
    files = cursor.fetchall()
    conn.close()
    
    return render_template('files.html', files=files)

if __name__ == '__main__':
    init_db()
    # ネットワークアクセスを許可（閲覧のみ、編集不可）
    app.run(debug=True, host='0.0.0.0', port=5000)
