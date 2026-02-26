from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dseapp.models import Order, Portfolio
from dseapp.forms import OrderForm
from decimal import Decimal  
from django.http import JsonResponse
import requests
import datetime
import time
from django.utils import timezone

# 🏠 Home Page View
def home(request):
    """Public home page"""
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

# 📊 Portfolio Page (Requires Login)
@login_required
def portfolio(request):
    orders = Order.objects.filter(is_closed=False).order_by('-created_at')
    portfolio, _ = Portfolio.objects.get_or_create(id=1)

    total_unrealized = sum(
        o.unrealized_profit - o.unrealized_loss for o in orders if not o.is_closed
    )

    instruments = orders.values_list("instrument", flat=True).distinct()

    total_deposit = portfolio.total_deposit
    total_withdraw = portfolio.total_withdrawal

    context = {
        "orders": orders,
        "portfolio": portfolio,
        "unrealized_pnl": total_unrealized,
        "instruments": instruments,
        "total_deposit": total_deposit,
        "total_withdraw": total_withdraw,
    }
    return render(request, "portfolio.html", context)

# ➕ Create Order
@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            portfolio, _ = Portfolio.objects.get_or_create(id=1)

            charge_rate = Decimal('0.005')
            total_value = order.quantity * order.cost_price
            charge = total_value * charge_rate
            total_deduction = total_value + charge

            order.cost_price = order.cost_price * (Decimal('1.00') + charge_rate)

            if portfolio.balance >= total_deduction:
                portfolio.balance -= total_deduction  # এটা ছিল না, যোগ করুন
                portfolio.total_withdrawal += total_deduction
                portfolio.save()
                order.save()

                messages.success(
                    request,
                    f"✅ Order created for {order.instrument}! ৳{total_deduction:.2f} deducted (including 0.5% charge)."
                )
                return redirect('portfolio')
            else:
                messages.error(
                    request,
                    f"❌ Insufficient balance! Need ৳{total_deduction:.2f}, but available ৳{portfolio.balance:.2f}."
                )
                return redirect('portfolio')
        else:
            messages.error(request, '⚠️ Please fix the errors below.')
    else:
        form = OrderForm()

    return render(request, 'order_form.html', {'form': form})

# 💹 Update Market Price
@login_required
@require_POST
def update_market_price(request):
    instrument = request.POST.get("instrument")
    market_price = request.POST.get("market_price")

    if instrument and market_price:
        try:
            market_price = float(market_price)
            Order.objects.filter(instrument=instrument, is_closed=False).update(market_price=market_price)
            messages.success(request, f'💰 Market price updated for {instrument} → ৳{market_price:.2f}')
        except ValueError:
            messages.error(request, '⚠️ Invalid market price format!')
    else:
        messages.error(request, '⚠️ Please provide both instrument and market price.')

    return redirect("portfolio")

# 💰 Execute Order
@login_required
def execute_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    portfolio, _ = Portfolio.objects.get_or_create(id=1)

    total_cost = order.quantity * order.cost_price

    if portfolio.balance >= total_cost:
        portfolio.balance -= total_cost
        portfolio.save()
        order.is_closed = False
        order.save()
        messages.success(request, f'✅ Order executed for {order.instrument}! ৳{total_cost:.2f} deducted from balance.')
    else:
        messages.error(request, f'❌ Insufficient balance! You need ৳{total_cost:.2f}, but have only ৳{portfolio.balance:.2f}.')

    return redirect('portfolio')

# ❌ Close an Order
@login_required
def close_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if not order.is_closed:
        exit_price = order.market_price or order.cost_price
        order.close_order(exit_price)
        messages.success(request, f'✅ Order for {order.instrument} closed successfully!')
    else:
        messages.warning(request, '⚠️ Order is already closed!')

    return redirect("portfolio")

# 🧮 Add Closed Orders' Profit to Balance
@login_required
def update_closed_order_balance(request):
    portfolio, _ = Portfolio.objects.get_or_create(id=1)
    closed_orders = Order.objects.filter(is_closed=True)

    total_closed_profit = sum(o.realized_profit - o.realized_loss for o in closed_orders)

    portfolio.balance += total_closed_profit
    portfolio.save()

    messages.success(request, f'💰 Added ৳{total_closed_profit:.2f} from closed orders to balance!')
    return redirect('portfolio')

# 💵 Deposit Money
@login_required
@require_POST
def deposit(request):
    amount = request.POST.get("amount")
    if amount:
        portfolio, _ = Portfolio.objects.get_or_create(id=1)
        amount = Decimal(amount)
        portfolio.total_deposit += amount
        portfolio.balance += amount
        portfolio.save()
        messages.success(request, f"✅ Deposited ৳{amount:.2f} successfully!")
    else:
        messages.error(request, "⚠️ Please enter a valid deposit amount.")
    return redirect("portfolio")

# 💸 Withdraw Money
@login_required
@require_POST
def withdraw(request):
    amount = request.POST.get("amount")
    if amount:
        portfolio, _ = Portfolio.objects.get_or_create(id=1)
        amount = Decimal(amount)
        if portfolio.balance >= amount:
            portfolio.total_withdrawal += amount
            portfolio.balance -= amount
            portfolio.save()
            messages.success(request, f"💸 Withdrawn ৳{amount:.2f} successfully!")
        else:
            messages.error(request, "❌ Not enough balance to withdraw.")
    else:
        messages.error(request, "⚠️ Please enter a valid withdraw amount.")
    return redirect("portfolio")

# 🧑‍💻 User Registration
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'🎉 Account created successfully! Welcome, {user.username}!')
            return redirect('portfolio')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# 🔐 User Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'👋 Welcome back, {user.username}!')
            return redirect('portfolio')
        else:
            messages.error(request, '❌ Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

# 🚪 User Logout
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '👋 You have been logged out successfully.')
    return redirect('login')

# 📉 Chart Page
def chart(request):
    return render(request, "chart.html")

def live_prices(request):
    # Simplified version for now
    return JsonResponse({
        "EURUSD": "1.0875",
        "XAGUSD": "23.45",
        "GOLD": "1952.30",
        "BTCUSD": "51250.00",
    })

def silver_history(request):
    # Simplified version
    return JsonResponse([], safe=False)

# 📈 Analysis Page
@login_required
def analysis(request):
    """Simple analysis page"""
    from .models import Portfolio, Order
    
    portfolio, _ = Portfolio.objects.get_or_create(id=1)
    orders = Order.objects.all()
    
    context = {
        'portfolio': portfolio,
        'orders': orders,
        'total_orders': orders.count(),
        'open_orders': orders.filter(is_closed=False).count(),
        'closed_orders': orders.filter(is_closed=True).count(),
    }
    
    return render(request, 'analysis.html', context)

# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from dseapp.models import Candle

class CandleDataView(APIView):

    def get(self, request):
        symbol = request.GET.get("symbol", "XAUUSD")
        tf = request.GET.get("tf", "15m")

        candles = Candle.objects.filter(
            symbol=symbol,
            timeframe=tf
        ).order_by("time")[:300]

        data = []

        for c in candles:
            data.append({
                "time": int(c.time.timestamp()),
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
            })

        return Response(data)