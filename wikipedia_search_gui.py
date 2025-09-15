"""
Wikipediaの検索を補助するGUIツール。
検索キーワードの履歴を保存し、過去の検索を容易にします。
"""

import tkinter as tk
import json
import webbrowser
from tkinter import ttk  # ttkモジュールをインポート
from tkinter import messagebox
from urllib.parse import quote
from datetime import datetime, timedelta
from pathlib import Path

# --- 定数 ---
HISTORY_FILE = Path("search_history.json")
MAX_HISTORY_COUNT = 20
HISTORY_RETENTION_DAYS = 15  # 履歴を保存する日数
WIKIPEDIA_SEARCH_URL = "https://ja.wikipedia.org/wiki/Special:Search?search={query}"

def load_history():
    """検索履歴をファイルから読み込む"""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # ファイルが空の場合にJSONDecodeErrorが発生するのを防ぐ
            if f.tell() == HISTORY_FILE.stat().st_size:
                return []
            history = json.load(f)

        if not isinstance(history, list):
            return []

        # --- 古い履歴形式との互換性処理 ---
        # 最初の要素が文字列なら、古い形式と判断して新しい形式に変換
        if history and isinstance(history[0], str):
            # 変換した結果をhistory変数に再代入する
            history = [{"query": item, "timestamp": datetime.now().isoformat()} for item in history]

        # --- 古い履歴の削除処理 ---
        cutoff_date = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
        
        # 保存期間内の履歴のみをフィルタリング
        valid_history = []
        for item in history:
            try:
                # タイムスタンプ文字列をdatetimeオブジェクトに変換
                timestamp = datetime.fromisoformat(item.get("timestamp", "1970-01-01T00:00:00"))
                if timestamp >= cutoff_date:
                    valid_history.append(item)
            except (ValueError, TypeError):
                continue # タイムスタンプの形式が不正な場合はスキップ
        return valid_history
    except (json.JSONDecodeError, IOError):
        return []

def save_history(history):
    """検索履歴をファイルに保存する"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"履歴の保存に失敗しました: {e}")

def search_wikipedia():
    """
    入力フィールドから検索語を取得し、
    Wikipediaの検索結果ページをブラウザで開きます。
    """
    query = combo.get() # Comboboxから値を取得
    if not query:
        messagebox.showwarning("入力エラー", "検索する単語を入力してください。")
        return

    # 日本語などのマルチバイト文字をURLで安全に使えるようにエンコードします
    encoded_query = quote(query)
    
    # Wikipediaの検索用URLを構築します (日本語版)
    url = WIKIPEDIA_SEARCH_URL.format(query=encoded_query)
    
    # デフォルトのウェブブラウザでURLを開きます
    print(f"'{query}' を検索します: {url}")
    webbrowser.open(url)

    # --- 検索履歴の更新 ---
    # 既存の履歴から同じキーワードのものを削除
    search_history[:] = [item for item in search_history if item.get("query") != query]
    
    # 履歴の先頭に追加
    new_entry = {"query": query, "timestamp": datetime.now().isoformat()}
    search_history.insert(0, new_entry)

    # 履歴が最大数を超えたら古いものから削除
    if len(search_history) > MAX_HISTORY_COUNT:
        search_history.pop()

    # Comboboxのリストを更新
    combo['values'] = [item['query'] for item in search_history]

# --- GUIのセットアップ ---

# 1. メインウィンドウを作成
window = tk.Tk()
window.title("Wikipedia 簡易検索ツール")
window.geometry("400x160")  # ウィンドウの高さを少し広げる
window.resizable(False, False) # ウィンドウサイズを固定

# 2. 検索履歴をロード
search_history = load_history()

# 2. ウィジェット（部品）の作成
# フレームを作成してパディングを設定
main_frame = tk.Frame(window, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

label = tk.Label(main_frame, text="検索したい単語を入力または選択してください:")
# EntryをComboboxに変更
combo = ttk.Combobox(main_frame, width=38, values=[item['query'] for item in search_history])
search_button = tk.Button(main_frame, text="検索", fg="blue", command=search_wikipedia)

# 3. ウィジェットの配置
label.pack(pady=5)
combo.pack(pady=5)
search_button.pack(pady=10)

# フォーカスを入力フィールドに設定
combo.focus_set()

# 4. ウィンドウが閉じられるときの処理を定義
window.protocol("WM_DELETE_WINDOW", lambda: (save_history(search_history), window.destroy()))

# 4. イベントループを開始（ウィンドウを表示し、ユーザーの操作を待つ）
window.mainloop()
