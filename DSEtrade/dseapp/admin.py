from django.contrib import admin
from .models import Contact,Portfolio, Order
from .models import Candle

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'created_at']
    admin.site.register(Portfolio)
    admin.site.register(Order)


admin.site.register(Candle)