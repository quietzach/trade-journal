import pandas as pd
from trader.models import Ticker, Execution, Side
import decimal


class CSVImporter:

    def __init__(self, filepath):
        self.filepath = filepath

    def load_data(self):
        df = pd.read_csv(self.filepath)

        # convert timestamp to datetime object
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], infer_datetime_format=True)
        df['Timestamp'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

        # sort dataframe with earliest first
        df = df.sort_values(by='Timestamp')

        num_new_tickers = 0
        num_new_executions = 0
        for entry in df.itertuples(index=False):
            # get csv entry values
            e_timestamp = entry.Timestamp
            e_ticker = entry.Symbol
            e_quantity = entry.Quantity
            e_price = entry.Price
            e_side = entry.Side
            e_commission = entry.Commission
            e_fee = entry.Fee
            e_type = entry.Type # TODO: Add type (crypto support)

            # print(entry)

            # get/create ticker from db
            ticker, created = Ticker.objects.get_or_create(name=e_ticker,
                                                           defaults={'name': e_ticker})
            if created:
                num_new_tickers += 1
            #     print(f'New Ticker Created: {e_ticker}')
            # else:
            #     print(f'Ticker Found: {e_ticker}')

            # get side
            side = Side.BUY if e_side.upper() == Side.BUY.name.upper() else Side.SELL

            # create execution and save to db
            execution = Execution.objects.create(ticker=ticker,
                                                 side=side,
                                                 traded_price=e_price,
                                                 traded_quantity=e_quantity,
                                                 execution_date=e_timestamp,
                                                 fee=e_fee,
                                                 commission=e_commission)
            # print(f'Execution created: {execution}')
            num_new_executions += 1

        print(f'{num_new_tickers} New Tickers Added.')
        print(f'{num_new_executions} New Executions Added.')
        return True