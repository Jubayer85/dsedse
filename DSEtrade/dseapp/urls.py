from django.urls import path
from dseapp.api import CurrentSignalView

#from dseapp.api import current_signal 
from . import views
app_name = "dseapp"

urlpatterns = [
    path('', views.home, name='home'),
    path("about/", views.about, name="about"),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('order/create/', views.order_create, name='order_create'),
    path('update_market_price/', views.update_market_price, name='update_market_price'),
    path('close_order/<int:order_id>/', views.close_order, name='close_order'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    path('execute_order/<int:order_id>/', views.execute_order, name='execute_order'),
    path('update_closed_order_balance/', views.update_closed_order_balance, name='update_closed_order_balance'),
    path('chart/', views.chart, name='chart'),
    path('analysis/', views.analysis, name='analysis'), 
     #path("api/signal/", current_signal), 
    path("api/signal/", CurrentSignalView.as_view(), name="current-signal"),




]
