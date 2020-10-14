from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView
from rest_framework import routers

from trader import views
from trader.schema import schema


router = routers.DefaultRouter()
router.register(r'tickers', views.TickerViewSet)
router.register(r'executions', views.ExecutionViewSet)
router.register(r'trades', views.TraderViewSet)

# router.register(r'rh', views.RobinhoodLoginView)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/robinhood', views.RobinhoodLoginView.as_view()),
    path('api/robinhood/code', views.RobinhoodLogin2FAView.as_view()),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]