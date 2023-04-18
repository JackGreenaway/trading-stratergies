import yfinance as yf
import matplotlib.pyplot as plt
import ta
import numpy as np
import pandas as pd
from termcolor import colored

class mean_reversion_bt:
    
    def __init__(self, symbol, start):
        self.symbol = symbol
        self.start = start
        self.df = yf.download(self.symbol, start=self.start)
        if self.df.empty:
            print('No pulled data')
        else:
            self.keltner_band()
            self.signals()
            self.loop_bt()
            self.buyHold = self.calc_buyhold()
            self.profit = self.calc_profit()
            self.cum_profit = (self.profit + 1).prod() - 1 
            #self.plot_bands()
            self.plot_signals()
    
    def keltner_band(self):
        self.df['HighBand'] = ta.volatility.keltner_channel_hband(self.df.High, self.df.Low, self.df.Close, original_version=False)
        self.df['MiddleBand'] = ta.volatility.keltner_channel_mband(self.df.High, self.df.Low, self.df.Close, original_version=False)
        self.df['LowBand'] = ta.volatility.keltner_channel_lband(self.df.High, self.df.Low, self.df.Close, original_version=False)
        self.df['rsi'] = ta.momentum.rsi(self.df.Close, window=6)
        self.df['shifted_close'] = self.df.Close.shift()
        
    def plot_bands(self):
        plt.figure(figsize=(15,5))
        plt.plot(self.df['2022':][['Close', 'HighBand', 'MiddleBand', 'LowBand']], label=['Close', 'Upper', 'Middle', 'Lower'])
        #plt.fill_between(df.index, df.HighBand, df.LowBand, color='grey', alpha=0.3)
        plt.legend(loc='lower left') 
        
    def signals(self):
        conditions = [(self.df.rsi < 30) & (self.df.Close < self.df.LowBand),
                      (self.df.rsi > 70) & (self.df.Close > self.df.HighBand)]
        choices = ['Buy', 'Sell']
        self.df['signal'] = np.select(conditions, choices)
        self.df.signal = self.df.signal.shift()
        self.df.dropna(inplace=True)
        
    def plot_signals(self):
        plt.figure(figsize=(12, 5))
        plt.plot(self.df.Open, label = 'Open Price')
        plt.scatter(self.buy_arr.index, self.buy_arr.values, marker='^', color='g', label = 'Buy')
        plt.scatter(self.sell_arr.index, self.sell_arr.values, marker='v', color='r', label = 'Sell')
        plt.legend()
        
    def current_signal(self):
        from termcolor import colored
        signal = self.df.signal[len(self.df) - 1]
        print(f'Current signal as of {self.df.index[len(self.df) - 1]}:\n')
        print(colored(signal, 'yellow', attrs=['bold']))
        
    def loop_bt(self):
        position = False
        buydate, selldate = [], []

        for index, row in self.df.iterrows():
            if not position:
                if row['signal'] == 'Buy':
                    buydate.append(index)
                    position = True
            if position:
                if row['signal'] == 'Sell' or row['shifted_close'] < 0.97 * self.df.loc[buydate[-1]].Open:
                    selldate.append(index)
                    position = False
            
        self.buy_arr = self.df.loc[buydate].Open
        self.sell_arr = self.df.loc[selldate].Open
        
    def calc_profit(self):
        try:
            if self.buy_arr.index[-1] > self.sell_arr.index[-1]:
                self.buy_arr = self.buy_arr[:-1]
            return (self.sell_arr.values - self.buy_arr.values) / self.buy_arr.values
        except:
            print(colored('\nNo buy/sell signals', 'yellow'))
            print(colored(f'Buy: {self.buy_arr}\nSell: {self.sell_arr}', 'yellow'))
            return 0
        
    def trade_breakdown(self):
        df = pd.DataFrame([self.buy_arr.values, self.sell_arr.values, self.profit])
        df = df.T
        df.columns = ['Buy', 'Sell', '% Profit/Loss']
        return df
    
    def calc_buyhold(self):
        buyHold = (self.df['Adj Close'].pct_change() + 1).prod() - 1
        return buyHold