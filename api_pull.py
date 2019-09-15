import pandas as pd
import requests
import datetime, time
import re, json

class YahooDailyReader():

    def __init__(self, symbol=None, start=None, end=None):
        self.symbol = symbol

        # initialize start/end dates if not provided
        if end is None:
            end = datetime.datetime.today()
        if start is None:
            start = end.replace(year=end.year if end.month > 1 else end.year - 1, month=end.month - 1 if end.month >1 else 12)

        self.start = start
        self.end = end

        # convert dates to unix time strings
        unix_start = int(time.mktime(self.start.timetuple()))
        day_end = self.end.replace(hour=23, minute=59, second=59)
        unix_end = int(time.mktime(day_end.timetuple()))

        url = 'https://finance.yahoo.com/quote/{}/history?'
        url += 'period1={}&period2={}'
        url += '&filter=history'
        url += '&interval=1d'
        url += '&frequency=1d'
        self.url = url.format(self.symbol, unix_start, unix_end)

    def read(self):
        r = requests.get(self.url)

        ptrn = r'root\.App\.main = (.*?);\n}\(this\)\);'
        txt = re.search(ptrn, r.text, re.DOTALL).group(1)
        jsn = json.loads(txt)
        df = pd.DataFrame(
                jsn['context']['dispatcher']['stores']
                ['HistoricalPriceStore']['prices']
                )
        df.insert(0, 'symbol', self.symbol)
        df['date'] = pd.to_datetime(df['date'], unit='s').dt.date

        # drop rows that aren't prices
        df = df.dropna(subset=['close'])

        df = df[['symbol', 'date', 'high', 'low', 'open', 'close',
                 'volume', 'adjclose']]
        df = df.set_index('symbol')
        return df
    
def get_data(ticker):
    df = YahooDailyReader(ticker).read()
    try:
        df = df.set_index(['date'])
        df.index = pd.to_datetime(df.index)
        #df = df['close']
        return df
    except Exception as e:
        df = []
        return df
