from django.shortcuts import render

# from django.contrib.auth.models import User, Group
from trader.models import Ticker, Execution, Trade, Side, Status
from rest_framework import viewsets
from rest_framework import permissions

from trader.serializers import TickerSerializer, ExecutionSerializer, TradeSerializer


class TickerViewSet(viewsets.ModelViewSet):
    """
    API endpoint of traded tickers.
    """
    # queryset = User.objects.all().order_by('-date_joined')
    queryset = Ticker.objects.all().order_by('name')
    serializer_class = TickerSerializer
    # permission_classes = [permissions.IsAuthenticated]


class ExecutionViewSet(viewsets.ModelViewSet):
    """
    API endpoint of executed orders.
    """
    queryset = Execution.objects.all().order_by('execution_date')
    serializer_class = ExecutionSerializer
    # permission_classes = [permissions.IsAuthenticated]


class TraderViewSet(viewsets.ModelViewSet):
    """
    API endpoint of Traded orders.
    """
    queryset = Trade.objects.all().order_by('close_date')
    serializer_class = TradeSerializer
    # permission_classes = [permissions.IsAuthenticated]