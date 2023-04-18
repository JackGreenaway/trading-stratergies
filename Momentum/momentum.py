import numpy as np
import yfinance as yf
import pandas as pd
import datetime
from datetime import date 
import os
import matplotlib.pyplot as plt


class momentum_stratergy:
    def __init__(self) -> None:
        self.get_data()
        self.prepare_data()
        self.get_top_performers()
        self.backtest()

    def get_data(self):
        # get s&p500
        sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        sp = list(sp.Symbol)
        # get nasdaq
        nasdaq = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]
        nasdaq = list(nasdaq.Ticker)
        
        tickers = []
        for i in sp:
            if i not in tickers:
                tickers.append(i)
        for i in nasdaq:
            if i not in tickers:
                tickers.append(i)
        self.start_date = "2010-01-01"
        self.data = yf.download(tickers, start=self.start_date)["Adj Close"]
        
        # get data for backtesting comparison
        sp_returns = yf.download('^GSPC',start=self.start_date)['Adj Close']
        self.sp_returns = (sp_returns.pct_change() + 1).cumprod()[1:]
        
    def prepare_data(self):
        # put dataframe index into datetime format
        self.data.index = pd.to_datetime(self.data.index)
        # resample the data to monthly pct returns
        self.mtl_data = (self.data.pct_change() + 1)[1:].resample("M").prod() 
        
        # print(self.mtl_data)

    def get_rolling_returns(self, df, n):
        return df.rolling(n).apply(np.prod)
    
    def performance(self, date):
        portfolio = self.mtl_data.loc[date:, self.get_top_backtest(date)][1:2]
        return portfolio.mean(axis=1).values[0]   
    
    def get_top_performers(self):
        # get the rolling returns for the last month
        mtl = self.mtl_data
        ret_12, ret_6, ret_3 = self.get_rolling_returns(mtl,12), self.get_rolling_returns(mtl,6), self.get_rolling_returns(mtl,3)
        
        # get date of end of last month
        today = date.today()
        days = int(today.strftime("%d"))
        days = datetime.timedelta(days)
        
        last_month = today - days
        last_month = last_month.strftime("%Y-%m-%d")
        
        # work out the best performers
        top_50 = ret_12.loc[last_month].nlargest(50).index
        top_30 = ret_6.loc[last_month, top_50].nlargest(30).index
        top_10 = ret_3.loc[last_month, top_30].nlargest(10).index
        
        # present stocks for the month
        os.system("cls")
    
        print(f"{'---'*15} Stocks {'---'*15}")
        print(f"Stocks for month following {last_month}:\n")
        print(list(top_10))
        # print("\n")
        
        self.ret_12, self.ret_6, self.ret_3 = ret_12, ret_6, ret_3
    
    def get_top_backtest(self, date):
        top_50 = self.ret_12.loc[date].nlargest(50).index
        top_30 = self.ret_6.loc[date, top_50].nlargest(30).index
        top_10 = self.ret_3.loc[date, top_30].nlargest(10).index
        return(top_10) 
        
    def backtest(self):
        returns = []

        for date in self.mtl_data.index[:-1]:
            returns.append(self.performance(date))
            
        self.mon_prod_returns = list([i - 0.01 for i in returns])
        self.mon_cum_returns = pd.Series([i - 0.01 for i in returns], index=self.mtl_data.index[1:]).cumprod()
        
    def backtest_present(self):        
        print(f"{'---'*15} Historical Returns {'---'*15}")
        print(f"S&P500 market return since {self.start_date}: *{'%.2f' % self.sp_returns.values[-1]}")
        print(f"Momentum strategy return since {self.start_date}: *{'%.2f' % self.mon_cum_returns.values[-1]}\n")
        # print(f"\nLast 3 months of momentum returns: {self.mon_cum_returns.values[-3:]}")
        
        plt.plot(self.mon_cum_returns)
        plt.plot(self.sp_returns)
        plt.legend(["Momentum Strategy", "S&P500 Return"])
        plt.show()

    def capital_return(self, starting_capital, injection=0):        
        if injection == 0:
            money = starting_capital * self.mon_cum_returns.values[-1]
        else:
            returns = self.mon_prod_returns
            money = starting_capital
            for i in range(1, len(returns)):
                money = (money * returns[i]) + injection
        
        print(f"{'---'*15} Capital Returns {'---'*15}")
        print(f"Starting capital: £{starting_capital}")
        print(f"Monthly injection: £{injection}")
        print(f"Total investment: £{starting_capital + (len(returns * injection))}")
        print(f"\nFinal Capital: £{'%.2f' % money}\n")

instance = momentum_stratergy()
instance.backtest_present()
instance.capital_return(starting_capital=1000, injection=150)

