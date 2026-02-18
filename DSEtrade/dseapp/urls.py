from django.urls import path
from . import views
from .views.tv_views import TVSymbolInfoView, TVHistoryView
from .api_views import CurrentSignalView  

# app_name = "dseapp"  # যদি প্রয়োজন হয় তাহলে আনকমেন্ট করুন

urlpatterns = [
    # বেসিক পেজ ভিউ
    path('', views.home, name='home'),
    path("about/", views.about, name="about"),
    path('chart/', views.chart, name='chart'),
    path('analysis/', views.analysis, name='analysis'),
    
    # পোর্টফোলিও ও অর্ডার ম্যানেজমেন্ট
    path('portfolio/', views.portfolio, name='portfolio'),
    path('order/create/', views.order_create, name='order_create'),
    path('update_market_price/', views.update_market_price, name='update_market_price'),
    path('close_order/<int:order_id>/', views.close_order, name='close_order'),
    path('execute_order/<int:order_id>/', views.execute_order, name='execute_order'),
    path('update_closed_order_balance/', views.update_closed_order_balance, name='update_closed_order_balance'),
    
    # ব্যালেন্স ম্যানেজমেন্ট
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    
    # ইউজার অথেনটিকেশন
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path("api/signal/", CurrentSignalView.as_view(), name="current-signal"),
    path('api/tv/symbol-info/', TVSymbolInfoView.as_view(), name='tv-symbol-info'),
    path('api/tv/history/', TVHistoryView.as_view(), name='tv-history'),
]