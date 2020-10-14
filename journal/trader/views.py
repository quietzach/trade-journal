from django.shortcuts import render

# from django.contrib.auth.models import User, Group
from trader.models import Ticker, Execution, Trade, Side, Status

from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from trader.serializers import TickerSerializer, ExecutionSerializer, TradeSerializer, RobinhoodLoginSerializer, RobinhoodLogin2FASerializer
from trader.data import robinhood_importer


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


class RobinhoodLoginView(APIView):
    def post(self, request, format=None):
        serializer = RobinhoodLoginSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.save()
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            print(f'Logging in')
            print(f'Username: {username}')
            print(f'Password: {password}')
            response = robinhood_importer.login(username, password)
            if 'detail' in response['login_response']:
                return Response({
                    'status': 'Login Error',
                    'message': response['login_response']['detail']
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'status': 'Login Received',
                    'message': response
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RobinhoodLogin2FAView(APIView):
    def post(self, request, format=None):
        serializer = RobinhoodLogin2FASerializer(data=request.data)
        if serializer.is_valid():
            # serializer.save()
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            code = serializer.validated_data['code']
            # payload = serializer.validated_data['payload']
            device_token = serializer.validated_data['device_token']
            print(f'2FA Code')
            print(f'Username: {username}')
            print(f'Password: {password}')
            print(f'Code: {code}')
            # print(f'Payload: {payload}')
            print(f'Token: {device_token}')

            # response = robinhood_importer.respond_challenge(payload, code)
            response = robinhood_importer.respond_challenge(username, password, device_token, code)
            print(f'Response: {response}')

            if response['status'] != 'Success':
                return Response({
                    'status': 'Login Received',
                    'message': response['status']
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'status': 'Login Received',
                    'message': response
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)