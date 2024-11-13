import tkinter as tk
from tkinter import ttk
import threading
from binance.client import Client
import pandas as pd
import ta
import numpy as np

class CryptoScanner:
    def __init__(self, master):
        self.master = master
        self.master.title("Crypto Scanner")
        self.master.geometry("1000x950")  # Pencere boyutunu biraz artırdım

        self.client = Client()

        self.create_widgets()

    def create_widgets(self):
        # Interval
        self.interval_label = ttk.Label(self.master, text="Interval:")
        self.interval_label.grid(row=0, column=0, padx=5, pady=5)

        self.interval_combo = ttk.Combobox(self.master, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.interval_combo.grid(row=0, column=1, padx=5, pady=5)
        self.interval_combo.set("1h")

        # SMA
        self.sma_var = tk.BooleanVar()
        self.sma_check = ttk.Checkbutton(self.master, text="SMA", variable=self.sma_var)
        self.sma_check.grid(row=1, column=0, padx=5, pady=5)

        self.sma_period_label = ttk.Label(self.master, text="SMA Period:")
        self.sma_period_label.grid(row=1, column=1, padx=5, pady=5)
        self.sma_period_entry = ttk.Entry(self.master)
        self.sma_period_entry.grid(row=1, column=2, padx=5, pady=5)
        self.sma_period_entry.insert(0, "50")

        self.sma_position_label = ttk.Label(self.master, text="SMA Position:")
        self.sma_position_label.grid(row=1, column=3, padx=5, pady=5)
        self.sma_position_combo = ttk.Combobox(self.master, values=["Above", "Below"])
        self.sma_position_combo.grid(row=1, column=4, padx=5, pady=5)
        self.sma_position_combo.set("Above")

        # Bollinger Bands
        self.bb_var = tk.BooleanVar()
        self.bb_check = ttk.Checkbutton(self.master, text="Bollinger Bands", variable=self.bb_var)
        self.bb_check.grid(row=2, column=0, padx=5, pady=5)

        self.bb_period_label = ttk.Label(self.master, text="BB Period:")
        self.bb_period_label.grid(row=2, column=1, padx=5, pady=5)
        self.bb_period_entry = ttk.Entry(self.master)
        self.bb_period_entry.grid(row=2, column=2, padx=5, pady=5)
        self.bb_period_entry.insert(0, "20")

        self.bb_position_label = ttk.Label(self.master, text="BB Position:")
        self.bb_position_label.grid(row=2, column=3, padx=5, pady=5)
        self.bb_position_combo = ttk.Combobox(self.master, values=["Above Upper", "Below Lower", "Between Bands"])
        self.bb_position_combo.grid(row=2, column=4, padx=5, pady=5)
        self.bb_position_combo.set("Above Upper")

        # RSI
        self.rsi_var = tk.BooleanVar()
        self.rsi_check = ttk.Checkbutton(self.master, text="RSI", variable=self.rsi_var)
        self.rsi_check.grid(row=3, column=0, padx=5, pady=5)

        self.rsi_period_label = ttk.Label(self.master, text="RSI Period:")
        self.rsi_period_label.grid(row=3, column=1, padx=5, pady=5)
        self.rsi_period_entry = ttk.Entry(self.master)
        self.rsi_period_entry.grid(row=3, column=2, padx=5, pady=5)
        self.rsi_period_entry.insert(0, "14")

        self.rsi_condition_label = ttk.Label(self.master, text="RSI Condition:")
        self.rsi_condition_label.grid(row=3, column=3, padx=5, pady=5)
        self.rsi_condition_combo = ttk.Combobox(self.master, values=["Overbought", "Oversold"])
        self.rsi_condition_combo.grid(row=3, column=4, padx=5, pady=5)
        self.rsi_condition_combo.set("Overbought")

        self.rsi_threshold_label = ttk.Label(self.master, text="RSI Threshold:")
        self.rsi_threshold_label.grid(row=3, column=5, padx=5, pady=5)
        self.rsi_threshold_entry = ttk.Entry(self.master)
        self.rsi_threshold_entry.grid(row=3, column=6, padx=5, pady=5)
        self.rsi_threshold_entry.insert(0, "70")

        # Smart Money Concepts
        self.smc_frame = ttk.LabelFrame(self.master, text="Smart Money Concepts")
        self.smc_frame.grid(row=4, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.smc_var = tk.BooleanVar()
        self.smc_check = ttk.Checkbutton(self.smc_frame, text="Enable SMC", variable=self.smc_var)
        self.smc_check.grid(row=0, column=0, padx=5, pady=5)

        self.smc_int_sens_label = ttk.Label(self.smc_frame, text="Internal Sensitivity:")
        self.smc_int_sens_label.grid(row=0, column=1, padx=5, pady=5)
        self.smc_int_sens_combo = ttk.Combobox(self.smc_frame, values=["3", "5", "8"])
        self.smc_int_sens_combo.grid(row=0, column=2, padx=5, pady=5)
        self.smc_int_sens_combo.set("3")

        self.smc_ext_sens_label = ttk.Label(self.smc_frame, text="External Sensitivity:")
        self.smc_ext_sens_label.grid(row=0, column=3, padx=5, pady=5)
        self.smc_ext_sens_combo = ttk.Combobox(self.smc_frame, values=["10", "25", "50"])
        self.smc_ext_sens_combo.grid(row=0, column=4, padx=5, pady=5)
        self.smc_ext_sens_combo.set("25")

        self.smc_structure_label = ttk.Label(self.smc_frame, text="Structure:")
        self.smc_structure_label.grid(row=1, column=0, padx=5, pady=5)
        self.smc_structure_combo = ttk.Combobox(self.smc_frame, values=["All", "BoS", "CHoCH"])
        self.smc_structure_combo.grid(row=1, column=1, padx=5, pady=5)
        self.smc_structure_combo.set("All")

        # Support Resistance Channels
        self.sr_frame = ttk.LabelFrame(self.master, text="Support Resistance Channels")
        self.sr_frame.grid(row=5, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.sr_var = tk.BooleanVar()
        self.sr_check = ttk.Checkbutton(self.sr_frame, text="Enable SR Channels", variable=self.sr_var)
        self.sr_check.grid(row=0, column=0, padx=5, pady=5)

        self.pivot_period_label = ttk.Label(self.sr_frame, text="Pivot Period:")
        self.pivot_period_label.grid(row=0, column=1, padx=5, pady=5)
        self.pivot_period_entry = ttk.Entry(self.sr_frame)
        self.pivot_period_entry.grid(row=0, column=2, padx=5, pady=5)
        self.pivot_period_entry.insert(0, "10")

        self.channel_width_label = ttk.Label(self.sr_frame, text="Max Channel Width %:")
        self.channel_width_label.grid(row=0, column=3, padx=5, pady=5)
        self.channel_width_entry = ttk.Entry(self.sr_frame)
        self.channel_width_entry.grid(row=0, column=4, padx=5, pady=5)
        self.channel_width_entry.insert(0, "5")

        self.min_strength_label = ttk.Label(self.sr_frame, text="Min Strength:")
        self.min_strength_label.grid(row=1, column=1, padx=5, pady=5)
        self.min_strength_entry = ttk.Entry(self.sr_frame)
        self.min_strength_entry.grid(row=1, column=2, padx=5, pady=5)
        self.min_strength_entry.insert(0, "2")

        self.max_sr_label = ttk.Label(self.sr_frame, text="Max SR Channels:")
        self.max_sr_label.grid(row=1, column=3, padx=5, pady=5)
        self.max_sr_entry = ttk.Entry(self.sr_frame)
        self.max_sr_entry.grid(row=1, column=4, padx=5, pady=5)
        self.max_sr_entry.insert(0, "6")

        self.sr_condition_label = ttk.Label(self.sr_frame, text="SR Condition:")
        self.sr_condition_label.grid(row=2, column=1, padx=5, pady=5)
        self.sr_condition_combo = ttk.Combobox(self.sr_frame, values=["Touching", "Near", "Between", "Above", "Below"])
        self.sr_condition_combo.grid(row=2, column=2, padx=5, pady=5)
        self.sr_condition_combo.set("Touching")

        self.sr_distance_label = ttk.Label(self.sr_frame, text="Distance (%):")
        self.sr_distance_label.grid(row=2, column=3, padx=5, pady=5)
        self.sr_distance_entry = ttk.Entry(self.sr_frame)
        self.sr_distance_entry.grid(row=2, column=4, padx=5, pady=5)
        self.sr_distance_entry.insert(0, "1")

        self.sr_channel_type_label = ttk.Label(self.sr_frame, text="Channel Type:")
        self.sr_channel_type_label.grid(row=3, column=1, padx=5, pady=5)
        self.sr_channel_type_combo = ttk.Combobox(self.sr_frame, values=["All", "Support", "Resistance"])
        self.sr_channel_type_combo.grid(row=3, column=2, padx=5, pady=5)
        self.sr_channel_type_combo.set("All")

        # ATR
        self.atr_frame = ttk.LabelFrame(self.master, text="Average True Range (ATR)")
        self.atr_frame.grid(row=6, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.atr_var = tk.BooleanVar()
        self.atr_check = ttk.Checkbutton(self.atr_frame, text="Enable ATR", variable=self.atr_var)
        self.atr_check.grid(row=0, column=0, padx=5, pady=5)

        self.atr_period_label = ttk.Label(self.atr_frame, text="ATR Period:")
        self.atr_period_label.grid(row=0, column=1, padx=5, pady=5)
        self.atr_period_entry = ttk.Entry(self.atr_frame)
        self.atr_period_entry.grid(row=0, column=2, padx=5, pady=5)
        self.atr_period_entry.insert(0, "14")

        self.atr_threshold_label = ttk.Label(self.atr_frame, text="ATR Threshold:")
        self.atr_threshold_label.grid(row=0, column=3, padx=5, pady=5)
        self.atr_threshold_entry = ttk.Entry(self.atr_frame)
        self.atr_threshold_entry.grid(row=0, column=4, padx=5, pady=5)
        self.atr_threshold_entry.insert(0, "0.5")

        self.atr_condition_label = ttk.Label(self.atr_frame, text="ATR Condition:")
        self.atr_condition_label.grid(row=0, column=5, padx=5, pady=5)
        self.atr_condition_combo = ttk.Combobox(self.atr_frame, values=["Above", "Below"])
        self.atr_condition_combo.grid(row=0, column=6, padx=5, pady=5)
        self.atr_condition_combo.set("Above")

        # Parabolic SAR
        self.sar_frame = ttk.LabelFrame(self.master, text="Parabolic SAR")
        self.sar_frame.grid(row=7, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.sar_var = tk.BooleanVar()
        self.sar_check = ttk.Checkbutton(self.sar_frame, text="Enable Parabolic SAR", variable=self.sar_var)
        self.sar_check.grid(row=0, column=0, padx=5, pady=5)

        self.sar_step_label = ttk.Label(self.sar_frame, text="Step:")
        self.sar_step_label.grid(row=0, column=1, padx=5, pady=5)
        self.sar_step_entry = ttk.Entry(self.sar_frame)
        self.sar_step_entry.grid(row=0, column=2, padx=5, pady=5)
        self.sar_step_entry.insert(0, "0.02")

        self.sar_max_label = ttk.Label(self.sar_frame, text="Max:")
        self.sar_max_label.grid(row=0, column=3, padx=5, pady=5)
        self.sar_max_entry = ttk.Entry(self.sar_frame)
        self.sar_max_entry.grid(row=0, column=4, padx=5, pady=5)
        self.sar_max_entry.insert(0, "0.2")

        # Pivot Points
        self.pivot_frame = ttk.LabelFrame(self.master, text="Pivot Points")
        self.pivot_frame.grid(row=8, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.pivot_var = tk.BooleanVar()
        self.pivot_check = ttk.Checkbutton(self.pivot_frame, text="Enable Pivot Points", variable=self.pivot_var)
        self.pivot_check.grid(row=0, column=0, padx=5, pady=5)

        self.pivot_period_label = ttk.Label(self.pivot_frame, text="Pivot Period:")
        self.pivot_period_label.grid(row=0, column=1, padx=5, pady=5)
        self.pivot_period_entry = ttk.Entry(self.pivot_frame)
        self.pivot_period_entry.grid(row=0, column=2, padx=5, pady=5)
        self.pivot_period_entry.insert(0, "10")

        # SuperTrend
        self.supertrend_frame = ttk.LabelFrame(self.master, text="SuperTrend")
        self.supertrend_frame.grid(row=9, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        self.supertrend_var = tk.BooleanVar()
        self.supertrend_check = ttk.Checkbutton(self.supertrend_frame, text="Enable SuperTrend", variable=self.supertrend_var)
        self.supertrend_check.grid(row=0, column=0, padx=5, pady=5)

        self.supertrend_period_label = ttk.Label(self.supertrend_frame, text="ATR Period:")
        self.supertrend_period_label.grid(row=0, column=1, padx=5, pady=5)
        self.supertrend_period_entry = ttk.Entry(self.supertrend_frame)
        self.supertrend_period_entry.grid(row=0, column=2, padx=5, pady=5)
        self.supertrend_period_entry.insert(0, "10")

        self.supertrend_factor_label = ttk.Label(self.supertrend_frame, text="Factor:")
        self.supertrend_factor_label.grid(row=0, column=3, padx=5, pady=5)
        self.supertrend_factor_entry = ttk.Entry(self.supertrend_frame)
        self.supertrend_factor_entry.grid(row=0, column=4, padx=5, pady=5)
        self.supertrend_factor_entry.insert(0, "3.0")

        # Scan button
        self.scan_button = ttk.Button(self.master, text="Tara", command=self.start_scan)
        self.scan_button.grid(row=10, column=0, columnspan=7, padx=5, pady=5)

        # Result text area
        self.result_text = tk.Text(self.master, height=20, width=120)
        self.result_text.grid(row=11, column=0, columnspan=7, padx=5, pady=5)

    def start_scan(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Tarama başlatılıyor...\n")
        threading.Thread(target=self.scan_coins).start()

    def scan_coins(self):
        futures = self.client.futures_exchange_info()
        symbols = [symbol['symbol'] for symbol in futures['symbols'] if symbol['status'] == 'TRADING']

        for symbol in symbols:
            self.analyze_coin(symbol)


    def analyze_coin(self, symbol):
        interval = self.interval_combo.get()

        klines = self.client.futures_klines(symbol=symbol, interval=interval)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        conditions = []

        if self.sma_var.get():
            sma_period = int(self.sma_period_entry.get())
            df['SMA'] = ta.trend.sma_indicator(df['close'], window=sma_period)
            if self.sma_position_combo.get() == "Above":
                conditions.append(df['close'].iloc[-1] > df['SMA'].iloc[-1])
            else:
                conditions.append(df['close'].iloc[-1] < df['SMA'].iloc[-1])

        if self.bb_var.get():
            bb_period = int(self.bb_period_entry.get())
            bollinger = ta.volatility.BollingerBands(df['close'], window=bb_period, window_dev=2)
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_lower'] = bollinger.bollinger_lband()
            df['BB_middle'] = bollinger.bollinger_mavg()

            if self.bb_position_combo.get() == "Above Upper":
                conditions.append(df['close'].iloc[-1] > df['BB_upper'].iloc[-1])
            elif self.bb_position_combo.get() == "Below Lower":
                conditions.append(df['close'].iloc[-1] < df['BB_lower'].iloc[-1])
            else:
                conditions.append((df['close'].iloc[-1] > df['BB_lower'].iloc[-1]) & (df['close'].iloc[-1] < df['BB_upper'].iloc[-1]))

        if self.rsi_var.get():
            rsi_period = int(self.rsi_period_entry.get())
            rsi_threshold = float(self.rsi_threshold_entry.get())
            df['RSI'] = ta.momentum.rsi(df['close'], window=rsi_period)

            if self.rsi_condition_combo.get() == "Overbought":
                conditions.append(df['RSI'].iloc[-1] > rsi_threshold)
            else:
                conditions.append(df['RSI'].iloc[-1] < rsi_threshold)

        if self.smc_var.get():
            int_sens = int(self.smc_int_sens_combo.get())
            ext_sens = int(self.smc_ext_sens_combo.get())
            structure = self.smc_structure_combo.get()

            df['smc_int_high'] = df['high'].rolling(window=int_sens).max()
            df['smc_int_low'] = df['low'].rolling(window=int_sens).min()
            df['smc_ext_high'] = df['high'].rolling(window=ext_sens).max()
            df['smc_ext_low'] = df['low'].rolling(window=ext_sens).min()

            if structure in ["All", "BoS"]:
                conditions.append((df['close'].iloc[-1] > df['smc_int_high'].iloc[-2]) | (df['close'].iloc[-1] < df['smc_int_low'].iloc[-2]))

            if structure in ["All", "CHoCH"]:
                conditions.append((df['high'].iloc[-1] > df['smc_ext_high'].iloc[-2]) | (df['low'].iloc[-1] < df['smc_ext_low'].iloc[-2]))

        # ATR koşulunu ekle
        if self.atr_var.get():
            atr_period = int(self.atr_period_entry.get())
            atr_threshold = float(self.atr_threshold_entry.get())
            df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=atr_period)

            if self.atr_condition_combo.get() == "Above":
                conditions.append(df['ATR'].iloc[-1] > atr_threshold)
            else:
                conditions.append(df['ATR'].iloc[-1] < atr_threshold)

        if all(conditions):
            result = f"{symbol}: Price: {df['close'].iloc[-1]}"
            # ... (diğer indikatörler için sonuç stringi aynı kalacak)
            if self.atr_var.get():
                result += f", ATR: {df['ATR'].iloc[-1]:.4f}"
            result += "\n"
            self.result_text.insert(tk.END, result)
            self.master.update_idletasks()

        # Parabolic SAR
        if self.sar_var.get():
            step = float(self.sar_step_entry.get())
            max_step = float(self.sar_max_entry.get())
            df['SAR'] = ta.trend.psar(df['high'], df['low'], step=step, max_step=max_step)
            conditions.append(df['close'].iloc[-1] > df['SAR'].iloc[-1])  # Price above SAR

        # Pivot Points
        if self.pivot_var.get():
            pivot_period = int(self.pivot_period_entry.get())
            df['pivot_high'] = df['high'].rolling(window=pivot_period*2+1, center=True).max()
            df['pivot_low'] = df['low'].rolling(window=pivot_period*2+1, center=True).min()
            df['is_resistance'] = (df['pivot_high'] == df['high']) & (df['pivot_high'].shift(1) != df['high'].shift(1))
            df['is_support'] = (df['pivot_low'] == df['low']) & (df['pivot_low'].shift(1) != df['low'].shift(1))

            last_resistance = df[df['is_resistance']].iloc[-1]['high'] if not df[df['is_resistance']].empty else np.inf
            last_support = df[df['is_support']].iloc[-1]['low'] if not df[df['is_support']].empty else 0

            conditions.append((df['close'].iloc[-1] > last_support) & (df['close'].iloc[-1] < last_resistance))

        # SuperTrend
        if self.supertrend_var.get():
            atr_period = int(self.supertrend_period_entry.get())
            factor = float(self.supertrend_factor_entry.get())

            # SuperTrend hesaplama
            atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=atr_period)

            hl2 = (df['high'] + df['low']) / 2
            final_upperband = hl2 + (factor * atr)
            final_lowerband = hl2 - (factor * atr)

            supertrend = pd.Series(index=df.index, dtype='float64')
            direction = pd.Series(index=df.index, dtype='int64')

            for i in range(1, len(df.index)):
                if df['close'][i] > final_upperband[i-1]:
                    supertrend[i] = final_lowerband[i]
                    direction[i] = 1
                elif df['close'][i] < final_lowerband[i-1]:
                    supertrend[i] = final_upperband[i]
                    direction[i] = -1
                else:
                    supertrend[i] = supertrend[i-1]
                    direction[i] = direction[i-1]

                    if direction[i] == 1 and final_lowerband[i] < supertrend[i]:
                        supertrend[i] = final_lowerband[i]
                    if direction[i] == -1 and final_upperband[i] > supertrend[i]:
                        supertrend[i] = final_upperband[i]

                    if direction[i] == 1 and df['close'][i] < supertrend[i]:
                        direction[i] = -1
                    if direction[i] == -1 and df['close'][i] > supertrend[i]:
                        direction[i] = 1

            df['SuperTrend'] = supertrend
            df['ST_Direction'] = direction

            conditions.append(df['ST_Direction'].iloc[-1] == 1)  # SuperTrend yukarı yönlü

        # Support Resistance Channels
        if self.sr_var.get():
            pivot_period = int(self.pivot_period_entry.get())
            channel_width = float(self.channel_width_entry.get())
            min_strength = int(self.min_strength_entry.get())
            max_sr = int(self.max_sr_entry.get())
            sr_condition = self.sr_condition_combo.get()
            sr_distance = float(self.sr_distance_entry.get()) / 100
            sr_channel_type = self.sr_channel_type_combo.get()

            sr_channels = self.calculate_sr_channels(df, pivot_period, channel_width, min_strength, max_sr)

            # Check if price meets the selected SR channel condition
            current_price = df['close'].iloc[-1]
            sr_condition_met = False

            for channel in sr_channels:
                if sr_channel_type == "All" or \
                   (sr_channel_type == "Support" and channel['high'] <= current_price) or \
                   (sr_channel_type == "Resistance" and channel['low'] >= current_price):

                    if sr_condition == "Touching":
                        if channel['low'] <= current_price <= channel['high']:
                            sr_condition_met = True
                            break
                    elif sr_condition == "Near":
                        if abs(current_price - channel['low']) / current_price <= sr_distance or \
                           abs(current_price - channel['high']) / current_price <= sr_distance:
                            sr_condition_met = True
                            break
                    elif sr_condition == "Between":
                        if channel['low'] <= current_price <= channel['high']:
                            sr_condition_met = True
                            break
                    elif sr_condition == "Above":
                        if current_price > channel['high']:
                            sr_condition_met = True
                            break
                    elif sr_condition == "Below":
                        if current_price < channel['low']:
                            sr_condition_met = True
                            break

            conditions.append(sr_condition_met)

        if all(conditions):
            result = f"{symbol}: Fiyat: {df['close'].iloc[-1]}"
            if self.sma_var.get():
                result += f", SMA: {df['SMA'].iloc[-1]:.2f}"
            if self.bb_var.get():
                result += f", BB Üst: {df['BB_upper'].iloc[-1]:.2f}, BB Orta: {df['BB_middle'].iloc[-1]:.2f}, BB Alt: {df['BB_lower'].iloc[-1]:.2f}"
            if self.rsi_var.get():
                result += f", RSI: {df['RSI'].iloc[-1]:.2f}"
            if self.smc_var.get():
                result += f", SMC Int High: {df['smc_int_high'].iloc[-1]:.2f}, SMC Int Low: {df['smc_int_low'].iloc[-1]:.2f}"
                result += f", SMC Ext High: {df['smc_ext_high'].iloc[-1]:.2f}, SMC Ext Low: {df['smc_ext_low'].iloc[-1]:.2f}"
            if self.sr_var.get():
                result += f", SR Channels: {len(sr_channels)}"
            if self.sar_var.get():
                result += f", SAR: {df['SAR'].iloc[-1]:.4f}"
            if self.pivot_var.get():
                result += f", Last Support: {last_support:.4f}, Last Resistance: {last_resistance:.4f}"
            if self.supertrend_var.get():
                result += f", SuperTrend: {df['SuperTrend'].iloc[-1]:.4f}, Direction: {'Up' if df['ST_Direction'].iloc[-1] == 1 else 'Down'}"

            result += "\n"
            self.result_text.insert(tk.END, result)
            self.master.update_idletasks()

    def calculate_sr_channels(self, df, pivot_period, channel_width, min_strength, max_sr):
        def get_pivots(src, left, right):
            pivots = []
            for i in range(left, len(src) - right):
                if all(src[i] >= src[j] for j in range(i - left, i + right + 1) if j != i):
                    pivots.append((i, src[i]))
            return pivots

        high_pivots = get_pivots(df['high'], pivot_period, pivot_period)
        low_pivots = get_pivots(df['low'], pivot_period, pivot_period)

        all_pivots = sorted(high_pivots + low_pivots, key=lambda x: x[0])

        max_price = df['high'].max()
        min_price = df['low'].min()
        price_range = max_price - min_price
        max_channel_width = price_range * channel_width / 100

        sr_channels = []
        for i, (_, pivot) in enumerate(all_pivots):
            channel = {'low': pivot, 'high': pivot, 'strength': 0}
            for j, (_, other_pivot) in enumerate(all_pivots[i:]):
                if other_pivot <= channel['high'] and other_pivot >= channel['low']:
                    channel['strength'] += 1
                elif other_pivot > channel['high'] and other_pivot - channel['low'] <= max_channel_width:
                    channel['high'] = other_pivot
                    channel['strength'] += 1
                elif other_pivot < channel['low'] and channel['high'] - other_pivot <= max_channel_width:
                    channel['low'] = other_pivot
                    channel['strength'] += 1
                else:
                    break
            if channel['strength'] >= min_strength:
                sr_channels.append(channel)

        sr_channels.sort(key=lambda x: x['strength'], reverse=True)
        return sr_channels[:max_sr]

root = tk.Tk()
app = CryptoScanner(root)
root.mainloop()
