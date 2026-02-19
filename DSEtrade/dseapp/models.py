from decimal import Decimal
from django.db import models
from django.utils import timezone


# ------------------- Contact Model -------------------
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ------------------- Portfolio Model -------------------
class Portfolio(models.Model):
    total_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    realized_gain = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    realized_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance(self):
        """
        💰 Current available balance =
        Total Deposit − Total Withdrawal
        """
        return self.total_deposit - self.total_withdrawal

    @property
    def total_market_value(self):
        """
        📈 Sum of all open orders' market value
        """
        from .models import Order
        open_orders = Order.objects.filter(is_closed=False)
        total_market = sum((o.total_market_value for o in open_orders), Decimal('0.00'))
        return total_market

    @property
    def unrealized_pnl(self):
        """
        📊 Unrealized P/L from open positions
        """
        from .models import Order
        orders = Order.objects.filter(is_closed=False)
        total_pnl = sum([(o.unrealized_profit - o.unrealized_loss) for o in orders], Decimal('0'))
        return total_pnl

    @property
    def total_equity(self):
        """
        🧮 Total Equity = Balance + Market Value (of open trades)
        """
        return self.balance + self.total_market_value

    @property
    def net_realized_pnl(self):
        """
        ✅ Net realized profit/loss from all closed orders
        0.5% transaction charge already বাদ দেওয়া হবে।
        total_deposit কোনোভাবেই পরিবর্তন হবে না।
        """
        net_gain = self.realized_gain * Decimal('0.995')  # 0.5% charge minus
        net_loss = self.realized_loss  # loss 그대로
        return net_gain - net_loss

    def __str__(self):
        return f"Portfolio | Balance: {self.balance:.2f} | Equity: {self.total_equity:.2f}"


# ------------------- Order Model -------------------
class Order(models.Model):
    instrument = models.CharField(max_length=50)
    order_type = models.CharField(
        max_length=10,
        choices=[("BUY", "Buy"), ("SELL", "Sell")],
        default="BUY"
    )
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    realized_gain_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def total_market_value(self):
        """Market Value = Current Market Price × Quantity"""
        if self.market_price is not None:
            return self.market_price * self.quantity
        return Decimal('0.00')

    @property
    def total_closed_value(self):
        """Total value when order is closed"""
        if self.is_closed and self.exit_price:
            return self.exit_price * self.quantity
        return Decimal('0.00')

    @property
    def charge_amount(self):
        """0.5% transaction charge"""
        charge_rate = Decimal('0.005')
        return (self.cost_price * self.quantity) * charge_rate

    @property
    def total_cost(self):
        return self.cost_price * self.quantity

    @property
    def total_cost_with_charge(self):
        # cost/unit এ চার্জ আগেই আছে, তাই শুধু total cost রিটার্ন করবে
        return self.total_cost

    @property
    def unrealized_profit(self):
        if not self.is_closed and self.market_price is not None:
            profit = (self.market_price - self.cost_price) * self.quantity
            return profit if profit > 0 else Decimal('0')
        return Decimal('0')

    @property
    def unrealized_loss(self):
        if not self.is_closed and self.market_price is not None:
            loss = (self.cost_price - self.market_price) * self.quantity
            return loss if loss > 0 else Decimal('0')
        return Decimal('0')

    def close_order(self, exit_price):
        self.exit_price = Decimal(str(exit_price))
        self.is_closed = True
        self.closed_at = timezone.now()

        charge_rate = Decimal('0.005')
        total_sale_value = self.exit_price * self.quantity
        charge_amount = total_sale_value * charge_rate
        net_amount_after_charge = total_sale_value - charge_amount
        pnl = (self.exit_price - self.cost_price) * self.quantity

        portfolio, _ = Portfolio.objects.get_or_create(id=1)
        portfolio.total_deposit += net_amount_after_charge

        if pnl > 0:
            portfolio.realized_gain += pnl
        else:
            portfolio.realized_loss += abs(pnl)

        portfolio.save()

        self.realized_gain_loss = pnl
        self.save()

        return {
            'total_sale_value': total_sale_value,
            'charge_amount': charge_amount,
            'net_amount_after_charge': net_amount_after_charge,
            'pnl': pnl,
            'is_profit': pnl > 0
        }

    def __str__(self):
        return f"{self.instrument} | Qty: {self.quantity} | Cost: {self.cost_price} | Market: {self.market_price}"
    

class Candle(models.Model):
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10)
    time = models.DateTimeField()

    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField(default=0)

    def __str__(self):
        return f"{self.symbol} {self.timeframe} {self.time}"

    class Meta:
        unique_together = ("symbol", "timeframe", "time")