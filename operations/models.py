# operations/models.py

from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone

# -------------------------------------------------------------------
# Common validators
# -------------------------------------------------------------------

phone_validator = RegexValidator(
    regex=r"^\d{7,15}$",
    message="Enter a valid mobile number (7–15 digits).",
)

non_negative = [MinValueValidator(0)]


class Order(models.Model):
    # === ORIGINAL FIELDS USED BY OrderForm ===
    company = models.CharField(max_length=200, null=True)
    address = models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    sales_person = models.CharField(max_length=200, null=True)

    # extra but safe (used in grids like factory / dispatch / split)
    location = models.CharField(max_length=200, blank=True, null=True)

    mobile1 = models.CharField(
        max_length=20,
        validators=[phone_validator],
        null=True,
    )
    mobile2 = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        null=True,
    )

    product_name = models.CharField(max_length=200, null=True)

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        default=Decimal("0"),
        null=True,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        default=Decimal("0"),
        null=True,
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=non_negative,
        null=True,
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=non_negative,
        null=True,
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        default=Decimal("0"),
        null=True,
    )

    remark = models.TextField(blank=True, null=True)

    # === TECHNICAL FIELDS FOR FLOWS (PAYMENT / FACTORY / DISPATCH) ===
    order_created = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        null=True,
    )
    # <<< IMPORTANT: allow existing NULLs in DB >>>
    bill_no = models.CharField(max_length=50, blank=True, null=True)

    # payment screen flags
    payment_cleared = models.BooleanField(default=False)
    on_hold = models.BooleanField(
        default=False,
        help_text="If true, order is kept on hold in payment status screen.",
    )

    # factory status flag
    factory_accepted = models.BooleanField(
        default=False,
        help_text="Marked true when factory has accepted the order.",
    )

    # quantities for factory/dispatch screens
    available_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=non_negative,
        null=True,
    )
    dispatch_date = models.DateField(null=True, blank=True)
    time_span_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Pre-calculated human readable time span text.",
    )

    # === NEW FLAGS FOR SPLIT / CANCEL ===
    is_split = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    def time_span(self):
        """
        Live 'time span since order_created', e.g. '2 Days 5 Hours 12 Minutes'.
        Safe with timezone-aware datetimes.
        """
        if not self.order_created:
            return ""
        now = timezone.now()
        delta = now - timezone.localtime(self.order_created)

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days:
            return f"{days} Days {hours} Hours {minutes} Minutes"
        return f"{hours} Hours {minutes} Minutes"

    def __str__(self):
        return f"{self.company or ''} - {self.product_name or ''}"

# -------------------------------------------------------------------
# Factory Status model
# -------------------------------------------------------------------

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
        """Return a string like '14 Days 5 Hours 48 Minutes'."""
        delta = timezone.now() - timezone.localtime(self.order_created)

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days} Days {hours} Hours {minutes} Minutes"

    def __str__(self):
        return f"{self.order_id} - {self.company_name}"


# -------------------------------------------------------------------
# Batch / Production models
# -------------------------------------------------------------------

class Batch(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("FINISHED", "Finished"),
        ("CANCELLED", "Cancelled"),
    ]

    supervisor = models.CharField(max_length=100)
    labour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=non_negative,
        help_text="Total labour hours or cost",
    )

    category = models.CharField(max_length=100)
    base_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        help_text="Base Qty from BOM",
    )
    production_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        help_text="Planned production quantity",
    )

    remark = models.TextField(blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

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
        Batch,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.CharField(max_length=150)
    qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
    )

    def __str__(self):
        return f"{self.product} ({self.qty})"


# -------------------------------------------------------------------
# Dispatch / Logistics models
# -------------------------------------------------------------------

class Vehicle(models.Model):
    number = models.CharField(max_length=50, unique=True)
    capacity_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
        help_text="Max load capacity (e.g. in litres or cartons).",
    )

    def __str__(self):
        return self.number


class Dispatch(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    remark = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def total_qty(self):
        total = Decimal("0")
        for item in self.items.all():
            total += item.qty
        return total

    def load_percentage(self):
        if not self.vehicle.capacity_qty:
            return 0
        return float(self.total_qty()) / float(self.vehicle.capacity_qty) * 100

    def __str__(self):
        return f"Dispatch {self.id} - {self.vehicle.number}"


class DispatchItem(models.Model):
    # null dispatch means "pending", not yet assigned to a dispatch
    dispatch = models.ForeignKey(
        Dispatch,
        related_name="items",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    order_id = models.IntegerField()
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    product = models.CharField(max_length=255)

    available_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
    )
    qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=non_negative,
    )

    ready_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this load became ready for dispatch.",
    )
    dispatch_date = models.DateField(null=True, blank=True)
    bill_no = models.CharField(max_length=50, blank=True, null=True)

    def delay_text(self):
        """
        Delay between 'ready_at' and now, shown like
        '25 Days 18 Hours 15 Minutes'.
        """
        end = timezone.now()
        delta = end - timezone.localtime(self.ready_at)

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days:
            return f"{days} Days {hours} Hours {minutes} Minutes"
        return f"{hours} Hours {minutes} Minutes"

    def __str__(self):
        return f"{self.order_id} - {self.company_name}"


# -------------------------------------------------------------------
# Raw Material Inward models
# -------------------------------------------------------------------
non_negative = [MinValueValidator(0)]

class MasterProduct(models.Model):
    PRODUCT_TYPES = [
        ("FG", "Finished Goods"),
        ("RM", "Raw Material"),
        ("PK", "Packing"),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)

    # NEW FIELDS
    product_type = models.CharField(
        max_length=2,
        choices=PRODUCT_TYPES,
        default="FG",
        db_index=True,
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=non_negative,
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=non_negative,
    )

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class MaterialInward(models.Model):
    master_product = models.ForeignKey(MasterProduct, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    inward_date = models.DateField(default=timezone.now)
    bill_no = models.CharField(max_length=50)

    remark = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Inward #{self.id} - {self.master_product} from {self.supplier}"
    
# -------------------------------------------------------------------
# Material Discard (RM or Finished Goods)
# -------------------------------------------------------------------

class MaterialDiscard(models.Model):
    CATEGORY_CHOICES = [
        ("RM", "Raw Material"),
        ("FG", "Finished Goods"),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
    )
    remark = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Discard {self.get_category_display()} #{self.id}"
    
class MaterialReturn(models.Model):
    order_id = models.IntegerField()
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    product = models.CharField(max_length=255)

    dispatched_qty = models.DecimalField(max_digits=10, decimal_places=2)
    returned_qty = models.DecimalField(max_digits=10, decimal_places=2)

    vehicle = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)

    returned_at = models.DateTimeField(default=timezone.now)

    def time_span(self):
        delta = timezone.now() - self.returned_at
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days} Days {hours} Hours {minutes} Minutes"

    def __str__(self):
        return f"Return {self.order_id} - {self.company_name}"