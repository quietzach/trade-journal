import graphene
from graphene.relay import Node
from graphene_django import DjangoObjectType
# from graphene_django.filter import DjangoFilterConnectionField

from trader.models import Ticker, Execution, Trade, Side, Status


class TickerType(DjangoObjectType):
    class Meta:
        model = Ticker
        fields = ('name', 'trades', 'executions')
        # django filters
        filter_fields = ('name', 'trades', 'executions')
        # interfaces = (Node,)


class ExecutionType(DjangoObjectType):
    # override side with enum string
    side = graphene.String()

    def resolve_side(self, info):
        return Side(self.side).name

    class Meta:
        model = Execution
        fields = ('ticker', 'side', 'traded_price', 'traded_quantity', 'execution_date',
                  'fee', 'value', 'commission', 'trade')
        # django filters
        filter_fields = ('ticker', 'side', 'traded_price', 'traded_quantity', 'execution_date',
                  'fee', 'value', 'commission', 'trade')
        # interfaces = (Node,)


class TradeType(DjangoObjectType):
    # override side with enum string
    status = graphene.String()
    hold_time = graphene.Field(type=graphene.Int, required=False, description='Hold-time in seconds')

    def resolve_status(self, info):
        return Status(self.status).name

    def resolve_hold_time(self, info):
        return self.hold_time.total_seconds() if self.hold_time is not None else self.hold_time

    class Meta:
        model = Trade
        fields = ('ticker', 'net_position', 'avg_open_price', 'avg_close_price', 'net_investment',
                  'open_date', 'close_date', 'hold_time', 'realized_pnl', 'unrealized_pnl', 'total_pnl', 'is_open',
                  'max_size', 'status', 'total_fees', 'total_commissions', 'executions')
        # django filters
        filter_fields = ('ticker', 'net_position', 'avg_open_price', 'avg_close_price', 'net_investment',
                  'open_date', 'close_date', 'hold_time', 'realized_pnl', 'unrealized_pnl', 'total_pnl', 'is_open',
                  'max_size', 'status', 'total_fees', 'total_commissions', 'executions')
        # interfaces = (Node,)


class Query(graphene.ObjectType):
    # custom filters without edges and nodes
    all_tickers = graphene.List(TickerType,
                                name=graphene.String(required=False, description='Ticker Name')
                                )
    all_executions = graphene.List(ExecutionType,
                                   side=graphene.String(required=False, description='Execution Side: (BUY/SELL)')
                                   )
    all_trades = graphene.List(TradeType,
                               is_open=graphene.Boolean(required=False, description='Open Trades'),
                               status=graphene.String(required=False, description='Trade Status: (OPEN/BE/WIN/LOSS)')
                               )

    # DjangoFilterConnectionField applies django_filters with standard edges and nodes
    # all_tickers = DjangoFilterConnectionField(TickerType)
    # all_executions = DjangoFilterConnectionField(ExecutionType)
    # all_trades = DjangoFilterConnectionField(TradeType)

    # def resolve_all_tickers(root, info):
    #     # We can easily optimize query count in the resolve method
    #     return TickerType.objects.select_related("category").all()

    def resolve_all_tickers(root, info, name=None):
        return Ticker.objects.filter(name=name).all() if name is not None else Ticker.objects.all()

    def resolve_all_executions(root, info, side=None):
        side_dict = {s[1]: s[0] for s in Side.choices}
        return Execution.objects.filter(side=side_dict[side.upper()]).all() if side is not None else Execution.objects.all()

    def resolve_all_trades(root, info, is_open=None, status=None):
        status_dict = {s[1]: s[0] for s in Status.choices}
        ret = Trade.objects.filter(is_open=is_open).all() if is_open is not None else Trade.objects.all()

        if status is not None:
            ret = ret.filter(status=status_dict[status.upper()]).all()

        return ret


schema = graphene.Schema(query=Query)