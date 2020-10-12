from django.contrib.auth.models import User, Group
from rest_framework import serializers
from trader.models import Ticker, Execution, Trade, Side, Status


class ChoiceField(serializers.Field):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ChoiceField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self._choices(obj).name  # obj is the first value

    def to_internal_value(self, data):
        # return getattr(self._choices, data)
        #TODO: Test fn
        return self._choices[data.upper()].value


# secondary serializer to avoid recursive calls to ticker, execution, and trades
class TickerSecondarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticker
        fields = ['name']


class ExecutionSecondarySerializer(serializers.ModelSerializer):
    side = ChoiceField(choices=Side)

    class Meta:
        model = Execution
        fields = ['side', 'traded_price', 'traded_quantity', 'execution_date',
                  'fee', 'value', 'commission']


class TradeSecondarySerializer(serializers.ModelSerializer):
    # status = serializers.ChoiceField(choices=Status.choices)
    status = ChoiceField(choices=Status)

    class Meta:
        model = Trade
        fields = ['net_position', 'avg_open_price', 'avg_close_price', 'net_investment',
                  'open_date', 'close_date', 'realized_pnl', 'unrealized_pnl', 'total_pnl', 'is_open',
                  'max_size', 'status', 'total_fees', 'total_commissions']


# primary serializers leveraging secondary serializers
class TickerSerializer(serializers.ModelSerializer):
    trades = TradeSecondarySerializer(many=True, read_only=True)
    executions = ExecutionSecondarySerializer(many=True, read_only=True)

    class Meta:
        model = Ticker
        fields = ['name', 'trades', 'executions']


class ExecutionSerializer(serializers.ModelSerializer):
    ticker = TickerSecondarySerializer(many=False, read_only=True)
    trade = TradeSecondarySerializer(many=False, read_only=True)
    side = ChoiceField(choices=Side)

    class Meta:
        model = Execution
        fields = ['ticker', 'side', 'traded_price', 'traded_quantity', 'execution_date',
                  'fee', 'value', 'commission', 'trade']


class TradeSerializer(serializers.ModelSerializer):
    ticker = TickerSecondarySerializer(many=False, read_only=True)
    executions = ExecutionSecondarySerializer(many=True, read_only=True)
    # status = serializers.ChoiceField(choices=Status.choices)
    status = ChoiceField(choices=Status)

    class Meta:
        model = Trade
        fields = ['ticker', 'net_position', 'avg_open_price', 'avg_close_price', 'net_investment',
                  'open_date', 'close_date', 'realized_pnl', 'unrealized_pnl', 'total_pnl', 'is_open',
                  'max_size', 'status', 'total_fees', 'total_commissions', 'executions']