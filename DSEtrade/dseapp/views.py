from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, Portfolio
from .forms import OrderForm
from decimal import Decimal  # 🧮 Decimal import করো
from django.http import JsonResponse
import requests
import datetime
import time

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

    # ✅ নতুন যোগ করা মোট deposit/withdraw ডেটা
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

            # 🔹 Safe Decimal হিসাব
            charge_rate = Decimal('0.005')  # 0.5% charge
            total_value = order.quantity * order.cost_price
            charge = total_value * charge_rate
            total_deduction = total_value + charge

            # 🔹 প্রতি ইউনিট cost_price-এ charge যোগ করো
            order.cost_price = order.cost_price * (Decimal('1.00') + charge_rate)

            # 🔹 ব্যালেন্স যথেষ্ট কিনা যাচাই
            if portfolio.balance >= total_deduction:
                # ব্যালেন্স থেকে মোট টাকা কাটা
                portfolio.total_withdrawal += total_deduction
                portfolio.save()

                # অর্ডার সেভ করো
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


# 💰 Execute Order (Balance থেকে টাকা কমানো)
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
        portfolio.balance += amount  # ✅ ব্যালেন্সেও যোগ করো
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
            portfolio.balance -= amount  # ✅ ব্যালেন্স থেকেও কমাও
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



# 📉 Chart Page (Requires Login)
def chart(request):
    return render(request, "chart.html")


def live_prices(request):
    # EURUSD
    eurusd = requests.get("https://www.freeforexapi.com/api/live?pairs=EURUSD").json()
    eurusd_price = eurusd["rates"]["EURUSD"]["rate"]

    # XAGUSD - Silver
    silver = requests.get(
        "https://metals-api.com/"
    ).json()
    silver_price = silver.get("price", "N/A")

    # GOLD
    gold = requests.get(
        "https://api.twelvedata.com/price?symbol=XAU/USD&apikey=YOUR_API_KEY"
    ).json()
    gold_price = gold.get("price", "N/A")

    # BTCUSD
    btc = requests.get(
        "https://api.twelvedata.com/price?symbol=BTC/USD&apikey=YOUR_API_KEY"
    ).json()
    btc_price = btc.get("price", "N/A")

    return JsonResponse({
        "EURUSD": eurusd_price,
        "XAGUSD": silver_price,
        "GOLD": gold_price,
        "BTCUSD": btc_price,
    })

def silver_history(request):
    # Fetch data from TwelveData
    url = "https://api.twelvedata.com/time_series?symbol=XAGUSD&interval=15min&outputsize=200&apikey=demo"

    response = requests.get(url).json()

    if "values" not in response:
        return JsonResponse({"error": "API Error", "details": response}, status=400)

    candles = []

    # Convert to LightweightCharts format
    for item in reversed(response["values"]):
        dt = datetime.datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(dt.timetuple()))

        candles.append({
            "time": timestamp,
            "open": float(item["open"]),
            "high": float(item["high"]),
            "low": float(item["low"]),
            "close": float(item["close"])
        })

    return JsonResponse(candles, safe=False)


# 📈 Analysis Page (Requires Login)
# সহজ version - শুধু analysis function যোগ করুন
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

