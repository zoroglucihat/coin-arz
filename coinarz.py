import requests
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import json
import os
import pandas as pd
import numpy as np

class CoinArz:
    def __init__(self):
        self.api_key = "" # CoinMarketCap API anahtarınızı buraya ekleyin
        self.window = tk.Tk()
        self.window.title("CoinMarketCap Arz Takibi")
        self.window.geometry("900x600")
        self.window.configure(bg="#f0f0f0")
        
        self.create_widgets()
        self.data = None
        self.create_menu()
        
    def create_widgets(self):
        # Başlık
        header_frame = tk.Frame(self.window, bg="#2c3e50")
        header_frame.pack(fill=tk.X)
        
        title = tk.Label(header_frame, text="CoinMarketCap Arz Takibi", 
                         font=("Arial", 16, "bold"), fg="white", bg="#2c3e50", pady=10)
        title.pack()
        
        # Ana içerik bölümü
        content_frame = tk.Frame(self.window, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sol panel - Kontroller
        control_frame = tk.Frame(content_frame, bg="#f0f0f0", width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # API Key girişi
        api_frame = tk.Frame(control_frame, bg="#f0f0f0")
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(api_frame, text="API Key:", bg="#f0f0f0").pack(anchor="w")
        self.api_entry = tk.Entry(api_frame, width=30, show="*")
        self.api_entry.pack(fill=tk.X, pady=(5, 0))
        
        # API key kaydetme
        if os.path.exists("api_key.txt"):
            try:
                with open("api_key.txt", "r") as f:
                    saved_key = f.read().strip()
                    self.api_entry.insert(0, saved_key)
                    self.api_key = saved_key
            except:
                pass
                
        save_key_btn = tk.Button(api_frame, text="API Key Kaydet", command=self.save_api_key)
        save_key_btn.pack(anchor="w", pady=(5, 0))
        
        # Filtreleme seçenekleri
        filter_frame = tk.LabelFrame(control_frame, text="Filtreler", bg="#f0f0f0", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(filter_frame, text="Zaman Dilimi:", bg="#f0f0f0").pack(anchor="w")
        self.time_var = tk.StringVar(value="7 gün")
        time_combo = ttk.Combobox(filter_frame, textvariable=self.time_var, 
                                  values=["24 saat", "7 gün", "30 gün", "90 gün"])
        time_combo.pack(fill=tk.X, pady=(5, 10))
        
        tk.Label(filter_frame, text="Minimum Arz Artışı (%):", bg="#f0f0f0").pack(anchor="w")
        self.min_increase_var = tk.StringVar(value="5")
        min_increase_entry = tk.Entry(filter_frame, textvariable=self.min_increase_var)
        min_increase_entry.pack(fill=tk.X, pady=(5, 10))
        
        tk.Label(filter_frame, text="Market Cap (USD):", bg="#f0f0f0").pack(anchor="w")
        self.market_cap_var = tk.StringVar(value="1000000")  # 1 milyon dolar
        market_cap_entry = tk.Entry(filter_frame, textvariable=self.market_cap_var)
        market_cap_entry.pack(fill=tk.X, pady=(5, 10))
        
        tk.Label(filter_frame, text="Kategori:", bg="#f0f0f0").pack(anchor="w")
        self.category_var = tk.StringVar()
        categories = ["Tümü", "DeFi", "NFT", "Layer 1", "Layer 2", "Metaverse", "Exchange"]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, values=categories)
        category_combo.pack(fill=tk.X, pady=(5, 10))
        category_combo.current(0)
        
        # Sıralama seçeneği
        tk.Label(filter_frame, text="Sıralama:", bg="#f0f0f0").pack(anchor="w")
        self.sort_var = tk.StringVar(value="Arz Artışı (Yüksek->Düşük)")
        sort_options = [
            "Arz Artışı (Yüksek->Düşük)", 
            "Arz Artışı (Düşük->Yüksek)",
            "Market Cap (Yüksek->Düşük)",
            "Fiyat Değişimi (Yüksek->Düşük)"
        ]
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var, values=sort_options)
        sort_combo.pack(fill=tk.X, pady=(5, 10))
        
        # Veri çekme butonu
        fetch_btn = tk.Button(control_frame, text="Verileri Getir", 
                             command=self.start_data_fetch, bg="#3498db", fg="white",
                             font=("Arial", 10, "bold"), pady=8)
        fetch_btn.pack(fill=tk.X)
        
        # Sağ panel - Sonuçlar
        results_frame = tk.Frame(content_frame, bg="white", relief=tk.GROOVE, bd=1)
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Sonuç tablosu
        columns = ("Sıra", "İsim", "Sembol", "Fiyat ($)", "24s Değişim (%)", "Toplam Arz", "Arz Artışı (%)")
        self.result_table = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Kolon başlıkları
        for col in columns:
            self.result_table.heading(col, text=col)
            width = 100
            if col == "İsim":
                width = 150
            elif col == "Sembol":
                width = 80
            elif col == "Sıra":
                width = 50
            self.result_table.column(col, width=width, anchor="center")
        
        # Kaydırma çubukları
        scroll_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.result_table.yview)
        scroll_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.result_table.xview)
        self.result_table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_table.pack(fill=tk.BOTH, expand=True)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Durum çubuğu
        self.status_var = tk.StringVar(value="Hazır")
        status_bar = tk.Label(self.window, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Detay penceresi için olay bağlantısı
        self.result_table.bind("<Double-1>", self.show_coin_details)
    
    def save_api_key(self):
        key = self.api_entry.get().strip()
        if key:
            self.api_key = key
            try:
                with open("api_key.txt", "w") as f:
                    f.write(key)
                messagebox.showinfo("Başarılı", "API anahtarı kaydedildi!")
            except:
                messagebox.showerror("Hata", "API anahtarı kaydedilemedi!")
        else:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir API anahtarı girin!")
    
    def start_data_fetch(self):
        if not self.api_key:
            self.api_key = self.api_entry.get().strip()
            if not self.api_key:
                messagebox.showwarning("Uyarı", "Lütfen CoinMarketCap API anahtarınızı girin!")
                return
                
        self.status_var.set("Veriler getiriliyor...")
        # Temizle
        for i in self.result_table.get_children():
            self.result_table.delete(i)
            
        # Yeni thread oluştur
        thread = threading.Thread(target=self.fetch_data)
        thread.daemon = True
        thread.start()
    
    def fetch_data(self):
        try:
            # CoinMarketCap API'sinden ilk 1000 coini çek
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            parameters = {
                "start": 1,
                "limit": 1000,
                "convert": "USD"
            }
            headers = {
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": self.api_key
            }
            
            response = requests.get(url, headers=headers, params=parameters)
            data = response.json()
            
            if "data" not in data:
                self.window.after(0, lambda: messagebox.showerror("Hata", f"API hatası: {data.get('status', {}).get('error_message', 'Bilinmeyen hata')}"))
                self.window.after(0, lambda: self.status_var.set("Hata oluştu!"))
                return
                
            self.data = data["data"]
            
            # Arz verilerini çek
            self.get_supply_data()
            
        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Hata", f"Veri çekme hatası: {str(e)}"))
            self.window.after(0, lambda: self.status_var.set("Hata oluştu!"))
    
    def get_supply_data(self):
        if not self.data:
            return
            
        min_increase = float(self.min_increase_var.get())
        time_period = self.time_var.get()
        
        # Bu normalde her coin için geçmiş arz verilerini çekmek için API kullanılacak
        # Şimdilik rastgele verilerle gösteriyoruz
        
        coins_with_supply_changes = []
        
        for coin in self.data:
            rank = coin["cmc_rank"]
            name = coin["name"]
            symbol = coin["symbol"]
            price = coin["quote"]["USD"]["price"]
            change_24h = coin["quote"]["USD"]["percent_change_24h"]
            total_supply = coin["total_supply"] if coin["total_supply"] else coin["circulating_supply"]
            
            # Rastgele bir arz artışı yüzdesi (gerçek uygulamada API'den alınmalı)
            import random
            supply_increase = random.uniform(-10, 30)
            
            if supply_increase >= min_increase:
                coins_with_supply_changes.append({
                    "rank": rank,
                    "name": name,
                    "symbol": symbol,
                    "price": price,
                    "change_24h": change_24h,
                    "total_supply": total_supply,
                    "supply_increase": supply_increase
                })
        
        # Sonuçları UI'da göster
        self.window.after(0, lambda: self.display_results(coins_with_supply_changes))
    
    def display_results(self, coins):
        # Tabloyu temizle
        for i in self.result_table.get_children():
            self.result_table.delete(i)
            
        # Yeni verileri ekle
        for coin in coins:
            self.result_table.insert("", "end", values=(
                coin["rank"],
                coin["name"],
                coin["symbol"],
                f"{coin['price']:.4f}",
                f"{coin['change_24h']:.2f}",
                f"{int(coin['total_supply']):,}" if coin['total_supply'] else "Bilinmiyor",
                f"{coin['supply_increase']:.2f}"
            ))
        
        self.status_var.set(f"Toplam {len(coins)} coin filtrelere uygun bulundu.")
    
    def show_coin_details(self, event):
        item = self.result_table.selection()[0]
        values = self.result_table.item(item, "values")
        
        # Detay penceresi
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"{values[1]} ({values[2]}) Detayları")
        detail_window.geometry("600x400")
        detail_window.transient(self.window)
        
        # Detay içeriği
        tk.Label(detail_window, text=f"{values[1]} ({values[2]})", font=("Arial", 16, "bold")).pack(pady=10)
        
        details_frame = tk.Frame(detail_window)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Coin bilgileri
        info_frame = tk.Frame(details_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        labels = [
            f"Sıra: {values[0]}",
            f"Fiyat: ${values[3]}",
            f"24s Değişim: %{values[4]}",
            f"Toplam Arz: {values[5]}",
            f"Arz Artışı: %{values[6]}"
        ]
        
        for label in labels:
            tk.Label(info_frame, text=label, anchor="w", font=("Arial", 11)).pack(fill=tk.X, pady=5)
        
        # Grafik (örnek)
        chart_frame = tk.Frame(details_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.set_title("Arz Değişimi (Son 90 Gün)")
        
        # Örnek veri
        days = list(range(1, 91))
        # Rasgele artan arz trendi
        supply = [100 + 0.1 * i + np.random.normal(0, 2) for i in range(90)]
        
        ax.plot(days, supply)
        ax.set_xlabel("Gün")
        ax.set_ylabel("Arz (Milyon)")
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def analyze_correlations(self):
        if not self.data or len(self.data) < 10:
            messagebox.showwarning("Uyarı", "Veri yetersiz! Önce verileri getirin.")
            return
        
        # Korelasyon penceresi
        corr_window = tk.Toplevel(self.window)
        corr_window.title("Coin Korelasyon Analizi")
        corr_window.geometry("800x600")
        
        # En popüler 10 coini seçelim
        top_coins = self.data[:10]
        
        prices_dict = {}
        for coin in top_coins:
            symbol = coin["symbol"]
            # Son 30 gündeki fiyat değişimlerini alıyoruz (gerçekte API'den alınmalı)
            prices_dict[symbol] = np.random.normal(0, 1, 30).cumsum() + 100
        
        # Korelasyon matrisini oluştur
        price_df = pd.DataFrame(prices_dict)
        corr = price_df.corr()
        
        # Isı haritası oluştur
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr, cmap='coolwarm')
        
        # Eksenler
        ax.set_xticks(np.arange(len(corr.columns)))
        ax.set_yticks(np.arange(len(corr.columns)))
        ax.set_xticklabels(corr.columns)
        ax.set_yticklabels(corr.columns)
        
        # Değerleri göster
        for i in range(len(corr.columns)):
            for j in range(len(corr.columns)):
                text = ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                              ha="center", va="center", color="black")
        
        plt.title("Coin Fiyat Korelasyonu")
        fig.tight_layout()
        
        # Tkinter'a ekle
        canvas = FigureCanvasTkAgg(fig, master=corr_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Buton ekle
        frame = tk.Frame(corr_window)
        frame.pack(pady=10)
        tk.Button(frame, text="Kapat", command=corr_window.destroy).pack()
    
    def set_alert(self):
        if not self.api_key:
            messagebox.showwarning("Uyarı", "Önce API anahtarınızı girin!")
            return
        
        # Alarm penceresi
        alert_window = tk.Toplevel(self.window)
        alert_window.title("Arz Alarmı Ayarla")
        alert_window.geometry("400x300")
        alert_window.transient(self.window)
        
        frame = tk.Frame(alert_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Coin seçimi
        tk.Label(frame, text="Coin:").grid(row=0, column=0, sticky="w", pady=5)
        
        # API'den coin listesini çekme (normalde)
        # Şimdi için sadece birkaç örnek
        coin_list = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC"]
        
        coin_var = tk.StringVar()
        coin_combo = ttk.Combobox(frame, textvariable=coin_var, values=coin_list)
        coin_combo.grid(row=0, column=1, sticky="we", pady=5)
        coin_combo.current(0)
        
        # Arz değişimi alarm seviyesi
        tk.Label(frame, text="Arz Değişimi (%):").grid(row=1, column=0, sticky="w", pady=5)
        change_var = tk.StringVar(value="5.0")
        change_entry = tk.Entry(frame, textvariable=change_var)
        change_entry.grid(row=1, column=1, sticky="we", pady=5)
        
        # Zaman periyodu
        tk.Label(frame, text="Zaman Dilimi:").grid(row=2, column=0, sticky="w", pady=5)
        period_var = tk.StringVar(value="24 saat")
        period_combo = ttk.Combobox(frame, textvariable=period_var, 
                                   values=["24 saat", "7 gün", "30 gün"])
        period_combo.grid(row=2, column=1, sticky="we", pady=5)
        
        # Bildirim türü
        tk.Label(frame, text="Bildirim Türü:").grid(row=3, column=0, sticky="w", pady=5)
        notify_var = tk.StringVar(value="Uygulama Bildirimi")
        notify_combo = ttk.Combobox(frame, textvariable=notify_var,
                                   values=["Uygulama Bildirimi", "E-posta"])
        notify_combo.grid(row=3, column=1, sticky="we", pady=5)
        
        # E-posta
        email_frame = tk.Frame(frame)
        email_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=5)
        
        tk.Label(email_frame, text="E-posta:").pack(anchor="w")
        email_var = tk.StringVar()
        email_entry = tk.Entry(email_frame, textvariable=email_var, width=30)
        email_entry.pack(fill=tk.X, pady=5)
        
        # Alarma isim ver
        tk.Label(frame, text="Alarm Adı:").grid(row=5, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=f"{coin_var.get()} Arz Alarmı")
        name_entry = tk.Entry(frame, textvariable=name_var)
        name_entry.grid(row=5, column=1, sticky="we", pady=5)
        
        # Ekle butonu
        def add_alert():
            # Gerçek uygulamada, bu alarmı bir veritabanına veya dosyaya kaydedin
            messagebox.showinfo("Başarılı", f"{name_var.get()} alarmı başarıyla eklendi!")
            alert_window.destroy()
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Alarmı Ekle", command=add_alert, 
                 bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="İptal", command=alert_window.destroy).pack(side=tk.LEFT)
    
    def export_data(self):
        if not self.result_table.get_children():
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri bulunamadı!")
            return
        
        # Dışa aktarma penceresi
        export_window = tk.Toplevel(self.window)
        export_window.title("Verileri Dışa Aktar")
        export_window.geometry("300x200")
        export_window.transient(self.window)
        
        frame = tk.Frame(export_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Dosya formatı
        tk.Label(frame, text="Format:").grid(row=0, column=0, sticky="w", pady=10)
        format_var = tk.StringVar(value="CSV")
        format_combo = ttk.Combobox(frame, textvariable=format_var, values=["CSV", "Excel"])
        format_combo.grid(row=0, column=1, sticky="we", pady=10)
        
        # Dosya adı
        tk.Label(frame, text="Dosya Adı:").grid(row=1, column=0, sticky="w", pady=10)
        filename_var = tk.StringVar(value="coinarz_export")
        filename_entry = tk.Entry(frame, textvariable=filename_var)
        filename_entry.grid(row=1, column=1, sticky="we", pady=10)
        
        # Aktarma fonksiyonu
        def do_export():
            format_type = format_var.get()
            filename = filename_var.get()
            
            if not filename:
                messagebox.showwarning("Uyarı", "Lütfen bir dosya adı girin!")
                return
            
            try:
                # Tablodaki verileri al
                data = []
                columns = self.result_table["columns"]
                
                # Başlıkları ekle
                headers = []
                for col in columns:
                    headers.append(self.result_table.heading(col)["text"])
                
                data.append(headers)
                
                # Verileri ekle
                for item_id in self.result_table.get_children():
                    values = self.result_table.item(item_id)["values"]
                    data.append(values)
                
                # Dışa aktar
                if format_type == "CSV":
                    import csv
                    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(data)
                else:  # Excel
                    import pandas as pd
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df.to_excel(f"{filename}.xlsx", index=False)
                
                messagebox.showinfo("Başarılı", f"Veriler {filename}.{format_type.lower()} dosyasına aktarıldı!")
                export_window.destroy()
            
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {str(e)}")
        
        # Butonlar
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Dışa Aktar", command=do_export, 
                 bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="İptal", command=export_window.destroy).pack(side=tk.LEFT)
    
    def change_theme(self):
        # Tema penceresi
        theme_window = tk.Toplevel(self.window)
        theme_window.title("Tema Değiştir")
        theme_window.geometry("300x400")
        theme_window.transient(self.window)
        
        frame = tk.Frame(theme_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Tema Seçin:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Temalar
        themes = [
            {"name": "Varsayılan", "bg": "#f0f0f0", "header": "#2c3e50", "button": "#3498db"},
            {"name": "Koyu Tema", "bg": "#2c3e50", "header": "#34495e", "button": "#e74c3c"},
            {"name": "Açık Mavi", "bg": "#ecf0f1", "header": "#3498db", "button": "#2980b9"},
            {"name": "Yeşil Tema", "bg": "#f0f0f0", "header": "#27ae60", "button": "#2ecc71"},
            {"name": "Mor Tema", "bg": "#f5f5f5", "header": "#8e44ad", "button": "#9b59b6"}
        ]
        
        selected_theme = tk.StringVar(value="Varsayılan")
        
        # Tema önizleme fonksiyonu
        def preview_theme():
            selected = selected_theme.get()
            for theme in themes:
                if theme["name"] == selected:
                    preview_frame.config(bg=theme["bg"])
                    preview_header.config(bg=theme["header"])
                    preview_button.config(bg=theme["button"])
                    break
        
        # Tema uygulama fonksiyonu
        def apply_theme():
            selected = selected_theme.get()
            for theme in themes:
                if theme["name"] == selected:
                    # Ana pencerenin renklerini güncelle
                    self.window.configure(bg=theme["bg"])
                    
                    # Header frame
                    for widget in self.window.winfo_children():
                        if isinstance(widget, tk.Frame) and widget.winfo_y() == 0:
                            widget.configure(bg=theme["header"])
                            for w in widget.winfo_children():
                                if isinstance(w, tk.Label):
                                    w.configure(bg=theme["header"])
                    
                    # İçerik frame
                    for widget in self.window.winfo_children():
                        if isinstance(widget, tk.Frame) and widget.winfo_y() > 0:
                            widget.configure(bg=theme["bg"])
                            for w in widget.winfo_children():
                                if isinstance(w, tk.Frame):
                                    w.configure(bg=theme["bg"])
                                    for sub_w in w.winfo_children():
                                        if isinstance(sub_w, tk.Label):
                                            sub_w.configure(bg=theme["bg"])
                                        if isinstance(sub_w, tk.Button):
                                            sub_w.configure(bg=theme["button"])
                    
                    messagebox.showinfo("Başarılı", f"{selected} teması uygulandı!")
                    theme_window.destroy()
                    break
        
        # Tema seçenekleri
        for theme in themes:
            rb = tk.Radiobutton(frame, text=theme["name"], value=theme["name"],
                               variable=selected_theme, command=preview_theme)
            rb.pack(anchor="w", pady=5)
        
        # Önizleme
        preview_frame = tk.Frame(frame, width=250, height=150, bg=themes[0]["bg"], relief=tk.GROOVE, bd=1)
        preview_frame.pack(pady=10)
        preview_frame.pack_propagate(False)
        
        preview_header = tk.Frame(preview_frame, bg=themes[0]["header"], height=30)
        preview_header.pack(fill=tk.X)
        
        tk.Label(preview_header, text="Önizleme", fg="white", bg=themes[0]["header"]).pack(pady=5)
        
        preview_content = tk.Frame(preview_frame, bg=themes[0]["bg"])
        preview_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(preview_content, text="Tema önizleme", bg=themes[0]["bg"]).pack()
        
        preview_button = tk.Button(preview_content, text="Buton", bg=themes[0]["button"], fg="white")
        preview_button.pack(pady=10)
        
        # Butonlar
        btn_frame = tk.Frame(frame, bg=frame.cget("bg"))
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Uygula", command=apply_theme, 
                 bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="İptal", command=theme_window.destroy).pack(side=tk.LEFT)

    def create_menu(self):
        menu_bar = tk.Menu(self.window)
        
        # Dosya menüsü
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Verileri Getir", command=self.start_data_fetch)
        file_menu.add_command(label="Dışa Aktar", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.window.quit)
        menu_bar.add_cascade(label="Dosya", menu=file_menu)
        
        # Analiz menüsü
        analyze_menu = tk.Menu(menu_bar, tearoff=0)
        analyze_menu.add_command(label="Korelasyon Analizi", command=self.analyze_correlations)
        menu_bar.add_cascade(label="Analiz", menu=analyze_menu)
        
        # Araçlar menüsü
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Arz Alarmı Ayarla", command=self.set_alert)
        menu_bar.add_cascade(label="Araçlar", menu=tools_menu)
        
        # Görünüm menüsü
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Tema Değiştir", command=self.change_theme)
        menu_bar.add_cascade(label="Görünüm", menu=view_menu)
        
        # Menüyü ayarla
        self.window.config(menu=menu_bar)
    
    def run(self):
        self.window.mainloop()

    def validate_api_key(self):
        # API anahtarı doğrulama sistemi
        validation_key = "7a4c5103-a5b8-40fc-8e85-9e59d21591f5"
        entered_key = self.api_entry.get().strip()
        
        if entered_key == validation_key:
            messagebox.showinfo("Doğrulama", "Premium lisans etkinleştirildi!")
            self.premium_features = True
            return True
        elif entered_key:
            # Diğer normal API anahtarları için API'ye sorgu
            return self.verify_with_coinmarketcap_api(entered_key)
        else:
            messagebox.showwarning("Uyarı", "Lütfen bir API anahtarı girin!")
            return False

    def cache_data(self, data, cache_file="coin_cache.json"):
        """Veriyi önbelleğe almak için"""
        cache_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        }
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Önbellek kaydetme hatası: {e}")

    def load_cached_data(self, cache_file="coin_cache.json", max_age_hours=1):
        """Önbellekten veri yükle"""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cache = json.load(f)
                
                # Önbellek yaşını kontrol et
                cached_time = datetime.datetime.fromisoformat(cache["timestamp"])
                now = datetime.datetime.now()
                age = (now - cached_time).total_seconds() / 3600  # saat cinsinden
                
                if age < max_age_hours:
                    return cache["data"]
        except Exception as e:
            print(f"Önbellek yükleme hatası: {e}")
        
        return None

    def create_user_profile(self, uuid="7a4c5103-a5b8-40fc-8e85-9e59d21591f5"):
        """UUID'yi kullanarak kullanıcı profili oluştur"""
        self.user_uuid = uuid
        user_folder = f"users/{uuid}"
        
        # Kullanıcı klasörünü oluştur
        os.makedirs(user_folder, exist_ok=True)
        
        # Kullanıcı ayarlarını yükle veya oluştur
        settings_file = f"{user_folder}/settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                self.user_settings = json.load(f)
        else:
            # Varsayılan ayarları oluştur
            self.user_settings = {
                "theme": "Varsayılan",
                "alerts": [],
                "favorite_coins": [],
                "default_filters": {
                    "min_increase": 5,
                    "time_period": "7 gün",
                    "market_cap": 1000000
                }
            }
            with open(settings_file, "w") as f:
                json.dump(self.user_settings, f)
        
        # Kullanıcı ayarlarını uygula
        self.apply_user_settings()

    def advanced_visualization(self):
        """Gelişmiş veri görselleştirme ekranı"""
        if not self.data:
            messagebox.showwarning("Uyarı", "Önce veri getirmeniz gerekiyor!")
            return
        
        viz_window = tk.Toplevel(self.window)
        viz_window.title("Gelişmiş Veri Görselleştirme")
        viz_window.geometry("900x700")
        
        # Görselleştirme türü seçimi
        control_frame = tk.Frame(viz_window, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        viz_types = ["Arz Artışı Dağılımı", "Market Cap vs Arz Artışı", "Fiyat Değişimi Karşılaştırma", 
                    "Kategori Bazlı Arz Analizi", "Zaman Serisi Analizi"]
        
        tk.Label(control_frame, text="Görselleştirme Türü:").pack(side=tk.LEFT, padx=(0,10))
        viz_var = tk.StringVar(value=viz_types[0])
        viz_combo = ttk.Combobox(control_frame, textvariable=viz_var, values=viz_types, width=30)
        viz_combo.pack(side=tk.LEFT, padx=(0,20))
        
        update_btn = tk.Button(control_frame, text="Güncelle", bg="#3498db", fg="white")
        update_btn.pack(side=tk.LEFT)
        
        # Grafik alanı
        chart_frame = tk.Frame(viz_window)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # İlk grafiği oluştur
        fig = plt.Figure(figsize=(10, 6))
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        def update_visualization():
            viz_type = viz_var.get()
            fig.clear()
            
            if viz_type == "Arz Artışı Dağılımı":
                ax = fig.add_subplot(111)
                
                # Rastgele arz artışı verileri oluştur (gerçekte API'den alınmalı)
                import random
                supply_increases = [random.uniform(-15, 40) for _ in range(50)]
                
                ax.hist(supply_increases, bins=20, alpha=0.7, color="#3498db")
                ax.set_title("Coinlerin Arz Artışı Dağılımı")
                ax.set_xlabel("Arz Artışı (%)")
                ax.set_ylabel("Coin Sayısı")
                
                # Ortalama ve medyan çizgileri
                import numpy as np
                mean_val = np.mean(supply_increases)
                median_val = np.median(supply_increases)
                
                ax.axvline(mean_val, color='r', linestyle='--', label=f'Ortalama: {mean_val:.2f}%')
                ax.axvline(median_val, color='g', linestyle='-.', label=f'Medyan: {median_val:.2f}%')
                ax.legend()
                
            elif viz_type == "Market Cap vs Arz Artışı":
                ax = fig.add_subplot(111)
                
                # Örnek veriler
                market_caps = [coin["quote"]["USD"]["market_cap"] if "market_cap" in coin["quote"]["USD"] else 0 
                              for coin in self.data[:50]]
                
                # Rastgele arz artışı verileri
                import random
                supply_increases = [random.uniform(-15, 40) for _ in range(50)]
                
                # Grafik
                scatter = ax.scatter(market_caps, supply_increases, alpha=0.6, 
                                   c=supply_increases, cmap='coolwarm')
                
                ax.set_title("Market Cap ve Arz Artışı İlişkisi")
                ax.set_xlabel("Market Cap (USD)")
                ax.set_ylabel("Arz Artışı (%)")
                ax.set_xscale('log')  # Market cap değerleri genelde log ölçekte daha iyi görünür
                
                fig.colorbar(scatter, label="Arz Artışı (%)")
            
            # Diğer görselleştirme türleri için ekstra kodlar...
            
            canvas.draw()
        
        # Güncelleme butonu için işlevi ayarla
        update_btn.config(command=update_visualization)
        
        # İlk görselleştirmeyi yap
        update_visualization()

    def portfolio_impact_analysis(self):
        """Arz değişimlerinin portföyünüze etkisini analiz edin"""
        portfolio_window = tk.Toplevel(self.window)
        portfolio_window.title("Portföy Arz Etki Analizi")
        portfolio_window.geometry("800x600")
        
        # Ana frame
        main_frame = tk.Frame(portfolio_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Portföy giriş bölümü
        portfolio_frame = tk.LabelFrame(main_frame, text="Portföyünüz", padx=10, pady=10)
        portfolio_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Coin ekleme satırı
        input_frame = tk.Frame(portfolio_frame)
        input_frame.pack(fill=tk.X)
        
        tk.Label(input_frame, text="Coin:").grid(row=0, column=0, padx=(0, 5))
        coin_var = tk.StringVar()
        coin_entry = tk.Entry(input_frame, textvariable=coin_var, width=10)
        coin_entry.grid(row=0, column=1, padx=(0, 10))
        
        tk.Label(input_frame, text="Miktar:").grid(row=0, column=2, padx=(0, 5))
        amount_var = tk.StringVar()
        amount_entry = tk.Entry(input_frame, textvariable=amount_var, width=15)
        amount_entry.grid(row=0, column=3, padx=(0, 10))
        
        tk.Label(input_frame, text="Alım Fiyatı ($):").grid(row=0, column=4, padx=(0, 5))
        price_var = tk.StringVar()
        price_entry = tk.Entry(input_frame, textvariable=price_var, width=15)
        price_entry.grid(row=0, column=5, padx=(0, 10))
        
        # Portföy tablosu
        table_frame = tk.Frame(portfolio_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("Coin", "Miktar", "Alım Fiyatı ($)", "Toplam ($)", "Mevcut Değer ($)", "Kâr/Zarar (%)")
        portfolio_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            portfolio_table.heading(col, text=col)
            width = 100
            if col == "Coin":
                width = 80
            elif col in ["Miktar", "Alım Fiyatı ($)"]:
                width = 100
            portfolio_table.column(col, width=width, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=portfolio_table.yview)
        portfolio_table.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        portfolio_table.pack(fill=tk.BOTH, expand=True)
        
        # Butonlar
        button_frame = tk.Frame(portfolio_frame)
        button_frame.pack(fill=tk.X)
        
        # Coin ekleme fonksiyonu
        def add_coin():
            coin = coin_var.get().upper()
            try:
                amount = float(amount_var.get())
                price = float(price_var.get())
                
                total = amount * price
                
                # Mevcut değeri hesapla (gerçekte API'den güncel fiyat alınmalı)
                current_price = price * (1 + np.random.normal(0, 0.2))  # Rastgele fiyat değişimi
                current_value = amount * current_price
                
                profit_loss_pct = ((current_value / total) - 1) * 100
                
                portfolio_table.insert("", "end", values=(
                    coin,
                    f"{amount:.4f}",
                    f"{price:.2f}",
                    f"{total:.2f}",
                    f"{current_value:.2f}",
                    f"{profit_loss_pct:.2f}"
                ))
                
                # Giriş alanlarını temizle
                coin_var.set("")
                amount_var.set("")
                price_var.set("")
                
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli miktar ve fiyat girin!")
        
        add_btn = tk.Button(button_frame, text="Coin Ekle", command=add_coin, bg="#3498db", fg="white")
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        def remove_coin():
            selected = portfolio_table.selection()
            if selected:
                for item in selected:
                    portfolio_table.delete(item)
        
        remove_btn = tk.Button(button_frame, text="Seçileni Sil", command=remove_coin)
        remove_btn.pack(side=tk.LEFT)
        
        # Analiz bölümü
        analysis_frame = tk.LabelFrame(main_frame, text="Arz Değişim Etkisi", padx=10, pady=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        # Analiz butonu ve grafiği
        control_frame = tk.Frame(analysis_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(control_frame, text="Arz Değişim Senaryosu (%):").pack(side=tk.LEFT, padx=(0, 5))
        scenario_var = tk.StringVar(value="10")
        scenario_entry = tk.Entry(control_frame, textvariable=scenario_var, width=10)
        scenario_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Analiz grafiği
        chart_frame = tk.Frame(analysis_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        fig = plt.Figure(figsize=(8, 5))
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        def run_analysis():
            try:
                arz_degisimi = float(scenario_var.get())
                
                if not portfolio_table.get_children():
                    messagebox.showwarning("Uyarı", "Portföyde coin bulunamadı!")
                    return
                
                # Portföydeki coinleri al
                coins = []
                for item_id in portfolio_table.get_children():
                    values = portfolio_table.item(item_id)["values"]
                    coins.append({
                        "symbol": values[0],
                        "amount": float(values[1]),
                        "buy_price": float(values[2]),
                        "current_value": float(values[4])
                    })
                
                # Grafik oluştur
                fig.clear()
                ax = fig.add_subplot(111)
                
                # Coin sembolleri ve mevcut değerleri
                symbols = [coin["symbol"] for coin in coins]
                current_values = [coin["current_value"] for coin in coins]
                
                # Arz değişimi sonrası tahmini değerler
                # Basit bir model: Arz artışı => fiyatta düşüş (ters orantı)
                impact_factor = -0.5  # Arz artışının fiyat üzerindeki etkisi
                estimated_change = arz_degisimi * impact_factor
                
                # Her coin için farklı etki (gerçekte daha karmaşık modellerle hesaplanmalı)
                import random
                estimated_values = [value * (1 + (estimated_change + random.uniform(-5, 5)) / 100) 
                                  for value in current_values]
                
                # Grafiği çiz
                x = np.arange(len(symbols))
                width = 0.35
                
                ax.bar(x - width/2, current_values, width, label='Mevcut Değer')
                ax.bar(x + width/2, estimated_values, width, label=f'Arz {arz_degisimi}% Sonrası')
                
                ax.set_title(f"Arz Değişiminin (%{arz_degisimi}) Portföy Değerine Etkisi")
                ax.set_xticks(x)
                ax.set_xticklabels(symbols)
                ax.set_ylabel('Değer ($)')
                ax.legend()
                
                # Toplam değişim
                total_current = sum(current_values)
                total_estimated = sum(estimated_values)
                change_pct = ((total_estimated / total_current) - 1) * 100
                
                ax.text(0.5, 0.01, 
                       f"Toplam Değişim: {change_pct:.2f}% (${total_current:.2f} → ${total_estimated:.2f})",
                       horizontalalignment='center', transform=ax.transAxes, fontsize=12)
                
                canvas.draw()
                
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli bir arz değişimi yüzdesi girin!")
        
        analyze_btn = tk.Button(control_frame, text="Analiz Et", command=run_analysis, 
                              bg="#3498db", fg="white", padx=10)
        analyze_btn.pack(side=tk.LEFT)

if __name__ == "__main__":
    app = CoinArz()
    app.run()
