import requests
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
import webbrowser
from datetime import datetime, timedelta
import numpy as np
import threading
from PIL import Image, ImageTk
from io import BytesIO
import time


class CryptoParser:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Parser")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0f1923')
        self.setup_styles()
        self.create_widgets()
        self.coins = []
        self.selected_coin = None
        self.update_in_progress = False
        self.load_data()
        self.root.after(60000, self.update_data)
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        bg_color = '#0f1923'
        card_color = '#1a2d3d'
        accent_color = '#1e3d59'
        text_color = 'white'
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, foreground=text_color)
        self.style.configure('Treeview',
                             background=card_color,
                             fieldbackground=card_color,
                             foreground=text_color,
                             rowheight=30,
                             font=('Helvetica', 10))
        self.style.configure('Treeview.Heading',
                             background=accent_color,
                             foreground=text_color,
                             font=('Helvetica', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', '#2a4d6e')])
        self.style.configure('TButton',
                             background=accent_color,
                             foreground=text_color,
                             font=('Helvetica', 10),
                             padding=5)
        self.style.map('TButton',
                       background=[('active', '#2a4d6e')])
        self.style.configure('TRadiobutton',
                             background=bg_color,
                             foreground=text_color,
                             font=('Helvetica', 9))
        self.style.configure('TEntry',
                             fieldbackground=card_color,
                             foreground=text_color,
                             insertcolor=text_color)
    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))

        self.logo_img = self.load_image_from_url(
            "https://cryptologos.cc/logos/versions/bitcoin-btc-logo-full.svg",
            size=(40, 40)
        )
        ttk.Label(header_frame, image=self.logo_img).pack(side='left')

        ttk.Label(
            header_frame,
            text="CRYPTO PARSER BINANCE",
            font=('Helvetica', 24, 'bold')
        ).pack(side='left', padx=5)
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side='right')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30,
            font=('Helvetica', 10)
        )
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', self.filter_coins)
        ttk.Button(
            search_frame,
            text="Search",
            command=self.filter_coins
        ).pack(side='left', padx=5)
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill='x', padx=20, pady=(0, 10))
        ttk.Label(filter_frame, text="Sort by:", font=('Helvetica', 10)).pack(side='left')
        self.sort_var = tk.StringVar(value='market_cap')
        sort_options = [
            ('Market Cap', 'market_cap'),
            ('Price ▲', 'price_asc'),
            ('Price ▼', 'price_desc'),
            ('24h % ▲', 'percent_asc'),
            ('24h % ▼', 'percent_desc'),
            ('Volume', 'volume'),
            ('A-Z', 'name_asc'),
            ('Z-A', 'name_desc')
        ]
        for text, mode in sort_options:
            ttk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.sort_var,
                value=mode,
                command=self.sort_coins
            ).pack(side='left', padx=5)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        list_frame = ttk.Frame(main_frame, width=450)
        list_frame.pack(side='left', fill='y')
        self.tree = ttk.Treeview(
            list_frame,
            columns=('name', 'price', 'change', 'volume'),
            show='headings',
            height=20
        )

        self.tree.heading('name', text='Coin', anchor='w')
        self.tree.heading('price', text='Price (USD)', anchor='center')
        self.tree.heading('change', text='24h %', anchor='center')
        self.tree.heading('volume', text='Volume (24h)', anchor='center')
        self.tree.column('name', width=180, anchor='w')
        self.tree.column('price', width=120, anchor='center')
        self.tree.column('change', width=80, anchor='center')
        self.tree.column('volume', width=120, anchor='center')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.show_coin_details)
        detail_frame = ttk.Frame(main_frame)
        detail_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        self.detail_header = ttk.Frame(detail_frame)
        self.detail_header.pack(fill='x', pady=(0, 10))
        self.price_frame = ttk.Frame(detail_frame)
        self.price_frame.pack(fill='x', pady=(0, 10))
        timeframe_frame = ttk.Frame(detail_frame)
        timeframe_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(timeframe_frame, text="Timeframe:").pack(side='left')
        self.timeframe_var = tk.StringVar(value='7d')
        timeframes = [
            ('1D', '1d'),
            ('7D', '7d'),
            ('1M', '30d'),
            ('3M', '90d'),
            ('1Y', '365d'),
            ('All', 'max')
        ]
        for text, mode in timeframes:
            ttk.Radiobutton(
                timeframe_frame,
                text=text,
                variable=self.timeframe_var,
                value=mode,
                command=self.update_chart
            ).pack(side='left', padx=5)

        self.chart_frame = ttk.Frame(detail_frame)
        self.chart_frame.pack(fill='both', expand=True)
        self.info_frame = ttk.Frame(detail_frame)
        self.info_frame.pack(fill='x', pady=(10, 0))
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            font=('Helvetica', 9)
        )
        status_bar.pack(fill='x', padx=20, pady=(0, 10))
    def load_image_from_url(self, url, size=(30, 30)):
        try:
            response = requests.get(url, timeout=5)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except:
            blank_img = Image.new('RGBA', size, (0, 0, 0, 0))
            return ImageTk.PhotoImage(blank_img)
    def load_data(self):
        if self.update_in_progress:
            return

        self.update_in_progress = True
        self.status_var.set("Loading data...")
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            response = requests.get(url, params=params)
            self.coins = response.json()
            self.update_coin_list()

            if self.selected_coin:
                coin_id = self.selected_coin['id']
                self.selected_coin = next((c for c in self.coins if c['id'] == coin_id), None)
                if self.selected_coin:
                    self.show_coin_details()
            self.status_var.set(f"Data updated at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.create_demo_data()
        finally:
            self.update_in_progress = False
    def get_historical_data(self, coin_id, days='max'):
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            response = requests.get(url, params=params)
            return response.json()['prices']
        except Exception as e:
            print(f"Error getting history for {coin_id}: {e}")
            return None

    def create_demo_data(self):
        self.coins = [
            {
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 50000 + np.random.randint(-2000, 2000),
                'price_change_percentage_24h': round(np.random.uniform(-5, 5), 2),
                'market_cap': 950000000000 + np.random.randint(-100000000000, 100000000000),
                'total_volume': 25000000000 + np.random.randint(-5000000000, 5000000000),
                'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png'
            },
            {
                'id': 'ethereum',
                'symbol': 'eth',
                'name': 'Ethereum',
                'current_price': 3000 + np.random.randint(-200, 200),
                'price_change_percentage_24h': round(np.random.uniform(-5, 5), 2),
                'market_cap': 350000000000 + np.random.randint(-50000000000, 50000000000),
                'total_volume': 18000000000 + np.random.randint(-3000000000, 3000000000),
                'image': 'https://assets.coingecko.com/coins/images/279/large/ethereum.png'
            }
        ]

        for coin in self.coins:
            coin['history'] = self.generate_demo_history(coin['current_price'])

        self.update_coin_list()

    def generate_demo_history(self, current_price):
        days = 365
        volatility = 0.05

        prices = []
        price = current_price * np.random.uniform(0.8, 1.2)
        now = time.time()

        for day in range(days, -1, -1):
            price = price * (1 + np.random.uniform(-volatility, volatility))
            timestamp = now - day * 86400
            prices.append([timestamp, price])

        return prices

    def update_data(self):
        threading.Thread(target=self.load_data, daemon=True).start()
        self.root.after(60000, self.update_data)

    def update_coin_list(self):
        self.tree.delete(*self.tree.get_children())

        for coin in self.coins:
            change = coin.get('price_change_percentage_24h', 0)
            change_text = f"{change:.2f}%" if change is not None else "N/A"
            change_color = 'green' if change and change >= 0 else 'red'

            self.tree.insert('', 'end',
                             values=(
                                 f"{coin['name']} ({coin['symbol'].upper()})",
                                 f"${coin['current_price']:,.2f}",
                                 change_text,
                                 f"${coin['total_volume'] / 1000000:,.0f}M"
                             ),
                             tags=(change_color,),
                             iid=coin['id']
                             )

        self.tree.tag_configure('green', foreground='#4CAF50')
        self.tree.tag_configure('red', foreground='#F44336')

    def filter_coins(self, event=None):
        query = self.search_var.get().lower()

        if not query:
            self.update_coin_list()
            return

        filtered = [
            c for c in self.coins
            if query in c['name'].lower()
               or query in c['symbol'].lower()
        ]

        self.tree.delete(*self.tree.get_children())
        for coin in filtered:
            change = coin.get('price_change_percentage_24h', 0)
            change_text = f"{change:.2f}%" if change is not None else "N/A"
            change_color = 'green' if change and change >= 0 else 'red'

            self.tree.insert('', 'end',
                             values=(
                                 f"{coin['name']} ({coin['symbol'].upper()})",
                                 f"${coin['current_price']:,.2f}",
                                 change_text,
                                 f"${coin['total_volume'] / 1000000:,.0f}M"
                             ),
                             tags=(change_color,),
                             iid=coin['id']
                             )

    def sort_coins(self, column=None):
        sort_mode = self.sort_var.get() if not column else column

        reverse_sort = False
        if sort_mode == 'market_cap':
            key = lambda x: x['market_cap']
            reverse_sort = True
        elif sort_mode == 'price_asc':
            key = lambda x: x['current_price']
        elif sort_mode == 'price_desc':
            key = lambda x: x['current_price']
            reverse_sort = True
        elif sort_mode == 'percent_asc':
            key = lambda x: x.get('price_change_percentage_24h', 0)
        elif sort_mode == 'percent_desc':
            key = lambda x: x.get('price_change_percentage_24h', 0)
            reverse_sort = True
        elif sort_mode == 'volume':
            key = lambda x: x['total_volume']
            reverse_sort = True
        elif sort_mode == 'name_asc':
            key = lambda x: x['name']
        elif sort_mode == 'name_desc':
            key = lambda x: x['name']
            reverse_sort = True
        elif sort_mode == 'name':
            key = lambda x: x['name']
        elif sort_mode == 'price':
            key = lambda x: x['current_price']
        elif sort_mode == 'change':
            key = lambda x: x.get('price_change_percentage_24h', 0)

        self.coins.sort(key=key, reverse=reverse_sort)
        self.update_coin_list()

    def show_coin_details(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        coin_id = selected[0]
        self.selected_coin = next((c for c in self.coins if c['id'] == coin_id), None)
        if not self.selected_coin:
            return

        for widget in self.detail_header.winfo_children():
            widget.destroy()

        for widget in self.price_frame.winfo_children():
            widget.destroy()

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        for widget in self.info_frame.winfo_children():
            widget.destroy()

        coin_img = self.load_image_from_url(
            self.selected_coin.get('image', ''),
            size=(50, 50)
        )

        img_label = ttk.Label(self.detail_header, image=coin_img)
        img_label.image = coin_img
        img_label.pack(side='left')

        info_frame = ttk.Frame(self.detail_header)
        info_frame.pack(side='left', padx=10, fill='x', expand=True)

        ttk.Label(
            info_frame,
            text=f"{self.selected_coin['name']} ({self.selected_coin['symbol'].upper()})",
            font=('Helvetica', 16, 'bold')
        ).pack(anchor='w')
        price = self.selected_coin['current_price']
        change = self.selected_coin.get('price_change_percentage_24h', 0)
        change_color = '#4CAF50' if change and change >= 0 else '#F44336'
        price_frame = ttk.Frame(info_frame)
        price_frame.pack(anchor='w')
        ttk.Label(
            price_frame,
            text=f"${price:,.2f}",
            font=('Helvetica', 14),
            foreground='white'
        ).pack(side='left')
        if change is not None:
            ttk.Label(
                price_frame,
                text=f" {change:+.2f}%",
                font=('Helvetica', 12),
                foreground=change_color
            ).pack(side='left')
        action_frame = ttk.Frame(self.price_frame)
        action_frame.pack(side='left', padx=5)
        buy_btn = ttk.Button(
            action_frame,
            text="Buy on Binance",
            command=lambda: self.open_binance(self.selected_coin['symbol'], 'buy')
        )
        buy_btn.pack(side='left', padx=5)
        sell_btn = ttk.Button(
            action_frame,
            text="Sell on Binance",
            command=lambda: self.open_binance(self.selected_coin['symbol'], 'sell')
        )
        sell_btn.pack(side='left', padx=5)
        stats_frame = ttk.Frame(self.price_frame)
        stats_frame.pack(side='right')
        ttk.Label(
            stats_frame,
            text=f"Market Cap: ${self.selected_coin['market_cap'] / 1000000000:,.2f}B",
            font=('Helvetica', 10)
        ).pack(anchor='e')
        ttk.Label(
            stats_frame,
            text=f"24h Volume: ${self.selected_coin['total_volume'] / 1000000:,.0f}M",
            font=('Helvetica', 10)
        ).pack(anchor='e')
        self.load_chart_data()
    def load_chart_data(self):
        if not self.selected_coin:
            return
        self.status_var.set("Loading chart data...")
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        loading_frame = ttk.Frame(self.chart_frame)
        loading_frame.pack(expand=True, fill='both')
        ttk.Label(
            loading_frame,
            text="Loading chart data...",
            font=('Helvetica', 12)
        ).pack(expand=True)
        threading.Thread(target=self._load_chart_data_thread, daemon=True).start()

    def _load_chart_data_thread(self):
        try:
            days_map = {
                '1d': '1',
                '7d': '7',
                '30d': '30',
                '90d': '90',
                '365d': '365',
                'max': 'max'
            }
            days = days_map.get(self.timeframe_var.get(), '7')
            history = self.get_historical_data(self.selected_coin['id'], days)

            if not history and 'history' in self.selected_coin:
                history = self.selected_coin['history']

            self.root.after(0, lambda: self.draw_chart(history))

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Chart error: {str(e)}"))
    def draw_chart(self, history_data):
        if not history_data:
            ttk.Label(
                self.chart_frame,
                text="No historical data available",
                foreground='gray'
            ).pack(expand=True)
            self.status_var.set("No chart data available")
            return
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        timestamps = [x[0] / 1000 for x in history_data]  # Convert to seconds
        prices = [x[1] for x in history_data]
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        fig = plt.Figure(figsize=(10, 5), dpi=100, facecolor='#0f1923')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f1923')
        for spine in ax.spines.values():
            spine.set_color('#1a2d3d')
        ax.tick_params(axis='both', colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        line_color = '#4fc3f7'
        ax.plot(dates, prices, color=line_color, linewidth=2)
        ax.fill_between(dates, prices, min(prices), color=line_color, alpha=0.1)
        date_format = DateFormatter('%Y-%m-%d')
        ax.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        ax.set_title(
            f"{self.selected_coin['name']} Price History",
            pad=20,
            fontsize=12
        )
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        self.show_additional_info()
        self.status_var.set(f"Data updated at {datetime.now().strftime('%H:%M:%S')}")
    def show_additional_info(self):
        if not self.selected_coin:
            return
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        stats_frame = ttk.Frame(self.info_frame)
        stats_frame.pack(fill='x', pady=(10, 0))
        high = self.selected_coin['current_price'] * 1.05  # Примерные данные
        low = self.selected_coin['current_price'] * 0.95  # Примерные данные
        ttk.Label(
            stats_frame,
            text=f"24h High: ${high:,.2f}",
            font=('Helvetica', 10),
            foreground='#4CAF50'
        ).pack(side='left', padx=10)
        ttk.Label(
            stats_frame,
            text=f"24h Low: ${low:,.2f}",
            font=('Helvetica', 10),
            foreground='#F44336'
        ).pack(side='left', padx=10)
        ttk.Label(
            stats_frame,
            text=f"Circulating Supply: {np.random.randint(10, 100)}M {self.selected_coin['symbol'].upper()}",
            font=('Helvetica', 10)
        ).pack(side='left', padx=10)
    def update_chart(self):
        if self.selected_coin:
            self.load_chart_data()
    def open_binance(self, symbol, action='buy'):
        webbrowser.open(f"https://www.binance.com/en/trade/{symbol.upper()}_USDT?type=spot")
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoParser(root)
    root.mainloop()
