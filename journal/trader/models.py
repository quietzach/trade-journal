from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import decimal
import numpy as np


class Side(models.IntegerChoices):
    BUY = 1, _('BUY')
    SELL = -1, _('SELL')


class Status(models.IntegerChoices):
    OPEN = 0, _('OPEN')
    BE = 1, _('BE')
    WIN = 2, _('WIN')
    LOSS = 3, _('LOSS')


class Ticker(models.Model):
    name = models.CharField(max_length=8, unique=True, help_text='Ticker name')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        ordering = ['name']


class Execution(models.Model):
    ticker = models.ForeignKey('Ticker', to_field='name', default='NONE', on_delete=models.CASCADE, related_name='executions')
    side = models.IntegerField(choices=Side.choices, help_text='BUY/SELL Side')
    traded_price = models.DecimalField(decimal_places=10, max_digits=64, help_text='Executed trade price')
    traded_quantity = models.DecimalField(decimal_places=10, max_digits=64, help_text='Executed trade quantity')
    execution_date = models.DateTimeField(help_text='Executed Date/Time')
    fee = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Executed fee')
    value = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Executed order value')
    commission = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Executed commission value')

    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, related_name='executions')

    def save(self, *args, **kwargs):
        # ticker = Ticker.objects.filter(name=self.ticker).first()
        # self.ticker = ticker if ticker is not None else Ticker.objects.create(name=self.ticker)

        # compute updated statistics for the current trade here from newly added trade
        # by computing the running updates to avoid having the trade object model to pull all
        # executions from the database to recompute statistics

        # update investment value
        self.value = decimal.Decimal(-1) * decimal.Decimal(self.side.value) * decimal.Decimal(self.traded_price) * decimal.Decimal(self.traded_quantity)

        # get latest open trade or create trade if none are open
        open_trades = Trade.objects.filter(ticker=self.ticker, is_open=True).first()
        self.trade = open_trades if open_trades is not None else Trade.objects.create(ticker=self.ticker, open_date=self.execution_date)

        # update trade details
        self.trade.total_fees += decimal.Decimal(self.fee)
        self.trade.total_commissions += decimal.Decimal(self.commission)

        quantity_with_direction = decimal.Decimal(self.side.value) * decimal.Decimal(self.traded_quantity)

        self.trade.is_open = self.trade.net_position + quantity_with_direction > 0

        # realized pnl
        if not self.trade.is_open and self.trade.net_position != 0: # avoid divide by zero
            # Remember to keep the sign as the net position
            self.trade.realized_pnl += (decimal.Decimal(self.traded_price) - decimal.Decimal(self.trade.avg_open_price)) * decimal.Decimal(
                                            min(abs(quantity_with_direction), abs(self.trade.net_position))
                                        ) * (decimal.Decimal(abs(self.trade.net_position)) / decimal.Decimal(self.trade.net_position))
        # total pnl
        self.trade.total_pnl = self.trade.realized_pnl + self.trade.unrealized_pnl

        # avg open price
        if self.trade.is_open:
            self.trade.avg_open_price = ((self.trade.avg_open_price * self.trade.net_position) +
                                         (decimal.Decimal(self.traded_price) * quantity_with_direction)) / (decimal.Decimal(self.trade.net_position) + quantity_with_direction)
        else:
            # Check if it is close-and-open
            if decimal.Decimal(self.traded_quantity) > decimal.Decimal(abs(self.trade.net_position)):
                self.trade.avg_open_price = self.traded_price
            else:
                self.trade.status = Status.WIN if self.trade.total_pnl > 0 else (
                    Status.LOSS if self.trade.total_pnl < 0 else Status.BE
                )
                self.trade.close_date = self.execution_date

        # net position
        self.trade.net_position += quantity_with_direction

        # net investment
        self.trade.net_investment = max(decimal.Decimal(self.trade.net_investment), abs(decimal.Decimal(self.trade.net_position) * decimal.Decimal(self.trade.avg_open_price)))

        self.trade.max_size = max(self.trade.max_size, self.trade.net_position)

        # self.trade, created = Trade.objects.get_or_create(ticker=self.ticker, is_open=True,
        #                                                   defaults={
        #
        #                                                   })

        # save model
        instance = super(Execution, self).save(*args, **kwargs)
        # https://docs.djangoproject.com/en/3.1/ref/models/instances/#specifying-which-fields-to-savez

        # commit updates to db
        # (needs to be done after committing Execution in order to properly compute average closing price)
        self.trade.save()

        return instance

    def __str__(self):
        return (f'Execution [' +
                    f'Ticker: {self.ticker},' +
                    f'Side: {Side(self.side).name},' +
                    f'Price: {self.traded_price},' +
                    f'Quantity: {self.traded_quantity},' +
                    f'Date: {self.execution_date},' +
                    f'Fee: {self.fee},' +
                    f'Value: {self.value},' +
                    f'Commissions: {self.commission}' +
                f']')

    class Meta:
        ordering = ['execution_date']


class Trade(models.Model):
    ticker = models.ForeignKey('Ticker', to_field='name', default='NONE', on_delete=models.CASCADE, related_name='trades')
    net_position = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Number of shares')
    avg_open_price = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Average open price')
    avg_close_price = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Average close price')
    net_investment = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Investment value')

    open_date = models.DateTimeField(help_text='Open Date/Time')
    close_date = models.DateTimeField(null=True, help_text='Close Date/Time')
    hold_time = models.DurationField(null=True, help_text='Trade hold time')

    realized_pnl = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Realized PnL')
    unrealized_pnl = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Unrealized PnL')
    total_pnl = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Total PnL')

    is_open = models.BooleanField(default=True, help_text='IsTrade Open')
    max_size = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Maximum share size')
    status = models.IntegerField(default=Status.OPEN, choices=Status.choices, help_text='Trade result')
    total_fees = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Total trade fees')
    total_commissions = models.DecimalField(default=0, decimal_places=10, max_digits=64, help_text='Total trade commissions')

    def save(self, *args, **kwargs):

        # compute average close price if trade is closed
        if not self.is_open:
            self.avg_close_price = decimal.Decimal(np.mean([ex.traded_price for ex in self.executions.filter(side=Side.SELL)]))

            # update hold time
            if self.close_date:
                current_tz = timezone.get_current_timezone()
                self.hold_time = current_tz.normalize(self.close_date) - current_tz.normalize(self.open_date)

        # save model
        instance = super(Trade, self).save(*args, **kwargs)

        return instance

    def __str__(self):
        return (f'Trade [' +
                    f'Ticker: {self.ticker},' +
                    f'Net Position: {self.net_position},' +
                    f'Avg Open Price: {self.avg_open_price},' +
                    f'Avg Close Price: {self.avg_close_price},' +
                    f'Net Investment: {self.net_investment},' +
                    f'Realized PnL: {self.realized_pnl},' +
                    f'Unrealized PnL: {self.unrealized_pnl},' +
                    f'Total PnL: {self.total_pnl},' +
                    f'isOpen: {self.is_open},' +
                    f'Max Size: {self.max_size},' +
                    f'Status: {Status(self.status).name},' +
                    f'Total Fees: {self.total_fees},' +
                    f'Total Commissions: {self.total_commissions},' +
                    f'Open Date: {self.open_date},' +
                    f'Close Date: {self.close_date},' +
                f']')

    class Meta:
        ordering = ['open_date']