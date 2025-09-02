import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import threading
from urllib.parse import urljoin, quote

DB_FILE = "fuji_parts_test.db"

class PartsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_fuji_electric(self, part_number):
        """富士電機のサイトから部品情報を検索"""
        search_urls = []
        try:
            # 富士電機の検索URL（例）
            base_url = "https://www.fujielectric.co.jp"
            search_urls = [
                f"{base_url}/products/search?q={quote(part_number)}",
                f"{base_url}/products/electronic_components/search?keyword={quote(part_number)}",
                f"{base_url}/search?keyword={quote(part_number)}",
                f"https://felib.fujielectric.co.jp/download/search.htm?keyword={quote(part_number)}"
            ]
            
            for url in search_urls:
                print(f"🔍 富士電機URL: {url}")
                try:
                    response = self.session.get(url, timeout=10)
                    print(f"📊 レスポンス: {response.status_code}")
                    if response.status_code == 200:
                        result = self.parse_fuji_page(response.text, part_number)
                        if result:
                            result['search_urls'] = search_urls
                            return result
                except Exception as e:
                    print(f"❌ URL失敗 {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"富士電機検索エラー: {e}")
        
        return {'search_urls': search_urls, 'error': 'すべてのURLで404またはエラー'}
    
    def search_hoei_denki(self, part_number):
        """宝永電機のサイトから部品情報を検索"""
        search_urls = []
        try:
            # 宝永電機の正しいURLを調査
            search_urls = [
                f"https://www.hoei.co.jp/",  # トップページから手動確認用
                f"https://hoei.co.jp/",     # wwwなし版
                f"https://www.hoei-denki.co.jp/search?q={quote(part_number)}",  # 推測URL
                f"https://hoei-denki.co.jp/products/{quote(part_number)}",      # 推測URL
            ]
            
            for url in search_urls:
                print(f"🔍 宝永電機URL: {url}")
                try:
                    response = self.session.get(url, timeout=10)
                    print(f"📊 レスポンス: {response.status_code}")
                    if response.status_code == 200:
                        result = self.parse_hoei_page(response.text, part_number)
                        if result:
                            result['search_urls'] = search_urls
                            return result
                except Exception as e:
                    print(f"❌ URL失敗 {url}: {str(e)[:100]}...")
                    continue
                    
        except Exception as e:
            print(f"宝永電機検索エラー: {e}")
        
        return {'search_urls': search_urls, 'error': 'すべてのURLで404またはエラー'}
    
    def parse_fuji_page(self, html_content, part_number):
        """富士電機のページを解析（改良版）"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"📄 HTMLサイズ: {len(html_content)} 文字")
        
        # より精密な仕様情報の抽出
        specs = {}
        
        # 1. テーブルから抽出
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    header = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    # 電圧関連
                    if any(keyword in header.lower() for keyword in ['電圧', 'voltage', '定格電圧']):
                        if self._is_valid_voltage(value):
                            specs['voltage'] = value
                    
                    # 電流関連
                    elif any(keyword in header.lower() for keyword in ['電流', 'current', '定格電流']):
                        if self._is_valid_current(value):
                            specs['current_rating'] = value
                    
                    # 寸法関連
                    elif any(keyword in header.lower() for keyword in ['寸法', 'dimension', 'サイズ']):
                        specs['dimensions'] = value
                    
                    # 重量関連
                    elif any(keyword in header.lower() for keyword in ['重量', 'weight', '質量']):
                        if self._is_valid_weight(value):
                            specs['weight'] = value
        
        # 2. 検索結果一覧から製品リンクを探す
        product_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            if part_number.upper() in text.upper() or part_number.lower() in href.lower():
                product_links.append(urljoin('https://www.fujielectric.co.jp', href))
        
        if product_links:
            specs['product_links'] = product_links[:3]  # 最大3個まで
            print(f"🔗 製品リンク発見: {len(product_links)}個")
        
        # 3. データシートリンク
        datasheet_link = self.find_datasheet_link(soup)
        if datasheet_link:
            specs['datasheet'] = urljoin('https://www.fujielectric.co.jp', datasheet_link)
        
        print(f"🎯 抽出した仕様: {list(specs.keys())}")
        return specs if specs else None
    
    def _is_valid_voltage(self, value):
        """電圧値が有効かチェック"""
        # -127Vのような明らかに間違った値を除外
        if re.search(r'-?\d+(\.\d+)?\s*V', value):
            voltage_match = re.search(r'(-?\d+(?:\.\d+)?)', value)
            if voltage_match:
                voltage = float(voltage_match.group(1))
                return -1000 < voltage < 1000  # 現実的な範囲
        return False
    
    def _is_valid_current(self, value):
        """電流値が有効かチェック"""
        return re.search(r'\d+(\.\d+)?\s*[mM]?A', value) is not None
    
    def _is_valid_weight(self, value):
        """重量値が有効かチェック"""
        return re.search(r'\d+(\.\d+)?\s*[gk]', value) is not None
    
    def parse_hoei_page(self, html_content, part_number):
        """宝永電機のページを解析"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        specs = {
            'price': self.extract_spec(soup, ['価格', 'price', '円', '¥']),
            'stock': self.extract_spec(soup, ['在庫', 'stock', '個']),
            'delivery': self.extract_spec(soup, ['納期', 'delivery', '日'])
        }
        
        return specs
    
    def extract_spec(self, soup, keywords):
        """仕様情報を抽出"""
        for keyword in keywords:
            # テーブル内を検索
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if keyword.lower() in cell.get_text().lower():
                            if i + 1 < len(cells):
                                return cells[i + 1].get_text().strip()
            
            # div、span等を検索
            for tag in soup.find_all(['div', 'span', 'p']):
                text = tag.get_text()
                if keyword.lower() in text.lower():
                    # 数値と単位を抽出
                    match = re.search(rf'{keyword}[:\s]*([0-9.,~-]+\s*[A-Za-z℃%]*)', text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
        
        return None
    
    def find_datasheet_link(self, soup):
        """データシートのリンクを検索"""
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()
            if any(keyword in text for keyword in ['datasheet', 'データシート', 'pdf', '仕様書']):
                return href
            if href.lower().endswith('.pdf'):
                return href
        return None

class PartsSearchApp:
    def __init__(self, root):
        self.root = root
        self.scraper = PartsScraper()
        self.setup_database()
        self.setup_gui()
    
    def setup_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 既存テーブルの構造を確認
        cursor.execute("PRAGMA table_info(part_specifications)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        if not existing_columns:
            # テーブルが存在しない場合は新規作成
            cursor.execute("""
                CREATE TABLE part_specifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_number TEXT UNIQUE,
                    voltage TEXT,
                    absorption_type TEXT,
                    capacitance TEXT,
                    resistance TEXT,
                    current_rating TEXT,
                    temperature_range TEXT,
                    dimensions TEXT,
                    weight TEXT,
                    price TEXT,
                    stock TEXT,
                    delivery TEXT,
                    datasheet_url TEXT,
                    search_urls TEXT,
                    remarks TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("新しいテーブルを作成しました")
        else:
            print(f"既存のカラム: {existing_columns}")
            
            # 必要なカラムを追加
            new_columns = {
                'current_rating': 'TEXT',
                'temperature_range': 'TEXT', 
                'dimensions': 'TEXT',
                'weight': 'TEXT',
                'price': 'TEXT',
                'stock': 'TEXT',
                'delivery': 'TEXT',
                'datasheet_url': 'TEXT',
                'search_urls': 'TEXT',
                'last_updated': 'DATETIME'
            }
            
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE part_specifications ADD COLUMN {col_name} {col_type}")
                        print(f"カラム {col_name} を追加しました")
                    except sqlite3.OperationalError as e:
                        print(f"カラム {col_name} 追加失敗: {e}")
        
        conn.commit()
        conn.close()
    
    def setup_gui(self):
        """GUIをセットアップ"""
        self.root.title("部品仕様検索ツール（スクレイピング対応）")
        self.root.geometry("900x700")
        
        # 入力フレーム
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="品番を入力:").grid(row=0, column=0, sticky=tk.W)
        self.part_entry = ttk.Entry(input_frame, width=40)
        self.part_entry.grid(row=0, column=1, padx=5)
        self.part_entry.bind('<Return>', lambda e: self.search_part())
        
        # ボタンフレーム
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=2, padx=5)
        
        self.search_button = ttk.Button(button_frame, text="DB検索", command=self.search_part)
        self.search_button.pack(side=tk.LEFT, padx=2)
        
        self.scrape_button = ttk.Button(button_frame, text="Web検索", command=self.scrape_part)
        self.scrape_button.pack(side=tk.LEFT, padx=2)
        
        self.update_button = ttk.Button(button_frame, text="DB更新", command=self.update_database)
        self.update_button.pack(side=tk.LEFT, padx=2)
        
        # プログレスバー
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # 結果表示フレーム
        result_frame = ttk.Frame(self.root, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=100, height=30)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def search_part(self):
        """データベースから部品を検索"""
        part_number = self.part_entry.get().strip()
        if not part_number:
            messagebox.showwarning("入力エラー", "品番を入力してください。")
            return
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM part_specifications WHERE part_number = ?
            """, (part_number,))
            result = cursor.fetchone()
            conn.close()
            
            self.result_text.delete(1.0, tk.END)
            if result:
                self.display_result(result, "データベース")
            else:
                self.result_text.insert(tk.END, f"品番「{part_number}」の情報はデータベースにありません。\nWeb検索を試してください。")
                
        except Exception as e:
            messagebox.showerror("データベースエラー", f"エラーが発生しました:\n{e}")
    
    def scrape_part(self):
        """Webスクレイピングで部品情報を検索"""
        part_number = self.part_entry.get().strip()
        if not part_number:
            messagebox.showwarning("入力エラー", "品番を入力してください。")
            return
        
        # バックグラウンドで実行
        threading.Thread(target=self._scrape_thread, args=(part_number,), daemon=True).start()
    
    def _scrape_thread(self, part_number):
        """スクレイピングをバックグラウンドで実行"""
        self.root.after(0, lambda: self.progress.start())
        self.root.after(0, lambda: self.status_var.set(f"検索中: {part_number}"))
        
        try:
            # 富士電機と宝永電機から検索
            fuji_data = self.scraper.search_fuji_electric(part_number)
            hoei_data = self.scraper.search_hoei_denki(part_number)
            
            # 結果をマージ
            merged_data = {}
            if fuji_data:
                merged_data.update(fuji_data)
            if hoei_data:
                merged_data.update(hoei_data)
            
            self.root.after(0, lambda: self._display_scrape_result(part_number, merged_data))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("スクレイピングエラー", f"エラーが発生しました:\n{e}"))
        
        finally:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.status_var.set("準備完了"))
    
    def _display_scrape_result(self, part_number, data):
        """スクレイピング結果を表示"""
        self.result_text.delete(1.0, tk.END)
        
        # 検索URL一覧を表示
        output = f"🌐 Web検索結果: {part_number}\n"
        output += "=" * 50 + "\n"
        
        # 検索したURLを表示
        if data.get('search_urls'):
            output += "🔗 検索URL:\n"
            for i, url in enumerate(data['search_urls'], 1):
                output += f"   {i}. {url}\n"
            output += "\n"
        
        if not data or all(v is None or v == '' for k, v in data.items() if k not in ['search_urls', 'error']):
            output += f"❌ 品番「{part_number}」の情報がWebで見つかりませんでした。\n\n"
            output += "📋 可能な原因:\n"
            output += "・URLが変更されている\n"
            output += "・認証が必要なページ\n"
            output += "・部品番号の表記違い\n"
            output += "・JavaScriptによる動的生成\n"
            
            if data.get('error'):
                output += f"・エラー詳細: {data['error']}\n"
        else:
            output += "✅ 取得した仕様情報:\n"
            
            if data.get('voltage'):
                output += f"🔌 電圧: {data['voltage']}\n"
            if data.get('current_rating'):
                output += f"⚡ 電流定格: {data['current_rating']}\n"
            if data.get('temperature_range'):
                output += f"🌡️ 動作温度: {data['temperature_range']}\n"
            if data.get('dimensions'):
                output += f"📏 寸法: {data['dimensions']}\n"
            if data.get('weight'):
                output += f"⚖️ 重量: {data['weight']}\n"
            if data.get('price'):
                output += f"💰 価格: {data['price']}\n"
            if data.get('stock'):
                output += f"📦 在庫: {data['stock']}\n"
            if data.get('delivery'):
                output += f"🚚 納期: {data['delivery']}\n"
            if data.get('datasheet'):
                output += f"📄 データシート: {data['datasheet']}\n"
            
            output += "\n※ この情報をデータベースに保存する場合は「DB更新」ボタンを押してください。"
        
        self.result_text.insert(tk.END, output)
        self.current_scrape_data = {part_number: data}  # 更新用に保存
    
    def update_database(self):
        """スクレイピング結果をデータベースに保存"""
        if not hasattr(self, 'current_scrape_data'):
            messagebox.showwarning("更新エラー", "更新するデータがありません。先にWeb検索を実行してください。")
            return
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # テーブル構造を確認
            cursor.execute("PRAGMA table_info(part_specifications)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"テーブルのカラム: {columns}")
            
            for part_number, data in self.current_scrape_data.items():
                # 検索URLをJSON文字列として保存
                search_urls_str = str(data.get('search_urls', []))
                
                if 'last_updated' in columns:
                    # last_updatedカラムがある場合
                    cursor.execute("""
                        INSERT OR REPLACE INTO part_specifications 
                        (part_number, voltage, current_rating, temperature_range, dimensions, weight, 
                         price, stock, delivery, datasheet_url, search_urls, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        part_number,
                        data.get('voltage'),
                        data.get('current_rating'),
                        data.get('temperature_range'),
                        data.get('dimensions'),
                        data.get('weight'),
                        data.get('price'),
                        data.get('stock'),
                        data.get('delivery'),
                        data.get('datasheet'),
                        search_urls_str
                    ))
                else:
                    # last_updatedカラムがない場合
                    cursor.execute("""
                        INSERT OR REPLACE INTO part_specifications 
                        (part_number, voltage, current_rating, temperature_range, dimensions, weight, 
                         price, stock, delivery, datasheet_url, search_urls)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        part_number,
                        data.get('voltage'),
                        data.get('current_rating'),
                        data.get('temperature_range'),
                        data.get('dimensions'),
                        data.get('weight'),
                        data.get('price'),
                        data.get('stock'),
                        data.get('delivery'),
                        data.get('datasheet'),
                        search_urls_str
                    ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("更新完了", f"データベースが更新されました。\n品番: {', '.join(self.current_scrape_data.keys())}")
            del self.current_scrape_data  # 保存後に削除
            
        except Exception as e:
            messagebox.showerror("データベースエラー", f"更新に失敗しました:\n{e}")
            print(f"DB更新エラー詳細: {e}")  # デバッグ用
    
    def display_result(self, result, source):
        """検索結果を表示"""
        if not result:
            return
            
        output = f"🔍 {source}検索結果\n"
        output += "=" * 50 + "\n"
        output += f"🔧 品番: {result[1]}\n"
        
        if result[2]:  # voltage
            output += f"🔌 電圧: {result[2]}\n"
        if result[3]:  # current
            output += f"⚡ 電流: {result[3]}\n"
        if result[4]:  # temperature
            output += f"🌡️ 動作温度: {result[4]}\n"
        if result[5]:  # dimensions
            output += f"📏 寸法: {result[5]}\n"
        if result[6]:  # weight
            output += f"⚖️ 重量: {result[6]}\n"
        if result[7]:  # price
            output += f"💰 価格: {result[7]}\n"
        if result[8]:  # stock
            output += f"📦 在庫: {result[8]}\n"
        if result[9]:  # delivery
            output += f"🚚 納期: {result[9]}\n"
        if result[10]:  # datasheet_url
            output += f"📄 データシート: {result[10]}\n"
        if result[11]:  # remarks
            output += f"📝 備考: {result[11]}\n"
        if result[12]:  # last_updated
            output += f"🕐 最終更新: {result[12]}\n"
        
        self.result_text.insert(tk.END, output)

if __name__ == "__main__":
    root = tk.Tk()
    app = PartsSearchApp(root)
    root.mainloop()