from django.contrib import admin
from trader.models import Ticker, Execution, Trade

admin.site.register(Ticker)
admin.site.register(Execution)
admin.site.register(Trade)
