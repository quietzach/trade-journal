from django.db import models
from django.utils.translation import gettext_lazy as _


class Side(models.IntegerChoices):
    BUY = 1, _('BUY')
    SELL = -1, _('SELL')


class Status(models.IntegerChoices):
    OPEN = 0, _('OPEN')
    BE = 1, _('BE')
    WIN = 2, _('WIN')
    LOSS = 3, _('LOSS')


class Execution(models.Model):
    side = models.IntegerField(choices=Side.choices)
    traded_price = models.DecimalField(decimal_places=5, max_digits=12)
    traded_quantity = models.IntegerField()
    execution_date = models.DateTimeField()
    fees = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    value = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    commission = models.DecimalField(default=0, decimal_places=5, max_digits=12)

    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, related_name='executions')

    def save(self, *args, **kwargs):
        instance = super(Execution, self).save(*args, **kwargs)
        # https://docs.djangoproject.com/en/3.1/ref/models/instances/#specifying-which-fields-to-savez
        self.trade.save()
        return instance


class Trade(models.Model):
    ticker = models.CharField(max_length=8)
    net_position = models.IntegerField(default=0)
    avg_open_price = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    avg_close_price = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    net_investment = models.DecimalField(default=0, decimal_places=5, max_digits=12)

    realized_pnl = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    unrealized_pnl = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    total_pnl = models.DecimalField(default=0, decimal_places=5, max_digits=12)

    is_open = models.BooleanField(default=True)
    max_size = models.IntegerField(default=0)
    status = models.IntegerField(default=Status.OPEN, choices=Status.choices)
    total_fees = models.DecimalField(default=0, decimal_places=5, max_digits=12)
    total_commissions = models.DecimalField(default=0, decimal_places=5, max_digits=12)

    # executions
    # update_by_tradefeed