import pandas as pd
from trader.models import Ticker, Execution, Side, Trade
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError


class GenericImporter:

    def __init__(self):
        self.df = None

    def load_csv(self, filepath):
        self.df = pd.read_csv(filepath)

    def load_dataframe(self, dataframe):
        self.df = dataframe

    def import_data(self):
        if self.df is None:
            print(f'No data loaded to import')
            return {
                'num_new_tickers': 0,
                'num_new_trades': 0,
                'num_new_executions': 0,
            }

        # convert timestamp to datetime object
        self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'], infer_datetime_format=True)
        self.df['Timestamp'] = self.df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

        # sort dataframe with earliest first
        self.df = self.df.sort_values(by='Timestamp')

        num_trades_pre = Trade.objects.count()

        num_new_tickers = 0
        num_new_executions = 0
        for entry in self.df.itertuples(index=False):
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

            try:
                # get_or_create execution (atomic) to prevent from making duplicates
                execution, created = Execution.objects.get_or_create(ticker=ticker,
                                                                     side=side,
                                                                     traded_price=e_price,
                                                                     traded_quantity=e_quantity,
                                                                     execution_date=e_timestamp,
                                                                     fee=e_fee,
                                                                     commission=e_commission,
                                                                     defaults={
                                                                        'ticker': ticker,
                                                                        'side': side,
                                                                        'traded_price': e_price,
                                                                        'traded_quantity': e_quantity,
                                                                        'execution_date': e_timestamp,
                                                                        'fee': e_fee,
                                                                        'commission': e_commission
                                                                     })
                # print(f'Execution created: {execution}')
                num_new_executions += 1 if created else 0
            except MultipleObjectsReturned:
                print(f'Multiple existing executions found!')
            except IntegrityError:
                print(f'Attmpted to create an already existing key in the database!')

        num_trades_post = Trade.objects.count()
        num_new_trades = num_trades_post - num_trades_pre
        print(f'{num_new_tickers} New Tickers Added.')
        print(f'{num_new_trades} New Trades Added.')
        print(f'{num_new_executions} New Executions Added.')
        return {
            'num_new_tickers': num_new_tickers,
            'num_new_trades': num_new_trades,
            'num_new_executions': num_new_executions,
        }