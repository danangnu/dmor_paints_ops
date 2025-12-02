# operations/models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone



phone_validator = RegexValidator(
    regex=r"^\d{7,15}$",
    message="Enter a valid mobile number (7–15 digits).",
)


class Order(models.Model):
    # HEADER INFO
    company = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)

    mobile1 = models.CharField(max_length=20, validators=[phone_validator])
    mobile2 = models.CharField(max_length=20, validators=[phone_validator])

    sales_person = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    # PRODUCT / PRICE
    product_name = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )

    remark = models.TextField(blank=True)

    # PAYMENT CLEARANCE FIELDS
    bill_no = models.CharField(max_length=50, blank=True, null=True)
    payment_cleared = models.BooleanField(default=False)
    payment_remark = models.CharField(max_length=300, blank=True, null=True)
    on_hold = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company} - {self.product_name or 'Order'}"

    def time_since_created(self):
        """Return 'X Months Y Days H Hours M Minutes' like the screenshot."""
        diff = timezone.now() - self.created_at
        days = diff.days
        months = days // 30
        d = days % 30
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{months} Months {d} Days {hours} Hours {minutes} Minutes"

class FactoryOrder(models.Model):
    order_id = models.IntegerField(unique=True)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    sales_person = models.CharField(max_length=255)
    order_created = models.DateTimeField()
    delivery_expected_date = models.DateField(null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    factory_accepted = models.BooleanField(default=False)

    def time_span(self):
        """Return a string like '14 Hours 55 Minutes 48 Seconds' / 'X Days ...'."""
        delta = timezone.now() - self.order_created

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days} Days {hours} Hours {minutes} Minutes"

    def __str__(self):
        return f"{self.order_id} - {self.company_name}"
    
class Batch(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("FINISHED", "Finished"),
        ("CANCELLED", "Cancelled"),
    ]

    supervisor = models.CharField(max_length=100)
    labour = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total labour hours or cost"
    )

    category = models.CharField(max_length=100)
    base_qty = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base Qty from BOM"
    )
    production_qty = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Planned production quantity"
    )

    remark = models.TextField(blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # simple computed fields to show in grid
    def time_required(self):
        """Dummy computation: 1 hour per 100 units of production."""
        if not self.production_qty:
            return 0
        return float(self.production_qty) / 100.0

    def std_density(self):
        return 1.0  # placeholder

    def actual_density(self):
        return 1.0  # placeholder

    def density_diff(self):
        return self.actual_density() - self.std_density()

    def __str__(self):
        return f"Batch {self.id} - {self.supervisor}"


class BatchItem(models.Model):
    batch = models.ForeignKey(
        Batch, related_name="items", on_delete=models.CASCADE
    )
    product = models.CharField(max_length=150)
    qty = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.product} ({self.qty})"