from django.db import models
from django.utils import timezone
from decimal import Decimal

EMP_TYPE_CHOICES = [
    ("PERMANENT", "Permanent"),
    ("CONTRACT", "Contract"),
    ("TEMP", "Temporary"),
]


class Department(models.Model):
    name = models.CharField("Department", max_length=100, unique=True)

    head = models.ForeignKey(
        "Employee",
        verbose_name="Department Head",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="headed_departments",
    )

    def __str__(self):
        return self.name


class Employee(models.Model):
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,   # allow null for existing rows
        help_text="Employee code / ID shown on screens",
    )

    prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text="Mr / Mrs / Ms etc.",
    )

    # make these nullable for migration
    first_name = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    full_name = models.CharField(max_length=255, blank=True)

    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    emp_dob = models.DateField(null=True, blank=True)
    joining_date = models.DateField(default=timezone.now)

    emp_type = models.CharField(
        max_length=20,
        choices=EMP_TYPE_CHOICES,
        default="PERMANENT",
    )

    current_branch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Branch name the employee currently belongs to",
    )

    department = models.ForeignKey(
        "Department",
        on_delete=models.PROTECT,
        related_name="employees",
        null=True,       # allow null for existing rows
        blank=True,
    )

    designation = models.CharField(max_length=100, blank=True, null=True)

    username = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,       # allow null for now
    )
    password = models.CharField(
        max_length=128,
        blank=True,      # don’t force it at DB level for old rows
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # keep full_name in sync
        if not self.full_name:
            parts = [self.prefix, self.first_name, self.middle_name, self.last_name]
            self.full_name = " ".join(p for p in parts if p).strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name or self.first_name or ''}"
    
class Unit(models.Model):
    name = models.CharField("Unit", max_length=50, unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField("Product Name", max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

class ProductMaster(models.Model):
    """
    Detailed product settings:
    - selling & purchase info
    - pack qty / unit
    - stock & density
    """
    INVENTORY_TYPE_FINISHED = "FG"
    INVENTORY_TYPE_PACKING = "PM"
    INVENTORY_TYPE_RAW = "RM"

    INVENTORY_TYPE_CHOICES = [
        (INVENTORY_TYPE_FINISHED, "Finished Goods"),
        (INVENTORY_TYPE_PACKING, "Packing Material"),
        (INVENTORY_TYPE_RAW, "Raw Material"),
    ]

    base_product = models.ForeignKey(
        "Product",
        on_delete=models.PROTECT,
        related_name="master_records",
        verbose_name="Select Product",
    )

    unit = models.ForeignKey(
        "Unit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Unit",
    )

    pack_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Pack Qty",
    )

    incentive = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal("0.00"),
    )

    solid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal("0.00"),
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Selling Price",
    )

    packed_in = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Packed In",
        help_text="e.g. Tin / Bucket / Drum",
    )

    min_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Min Stock Level",
    )

    raw_material_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Raw Material Cost",
    )

    density = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )

    company_name = models.CharField(
        max_length=255,
        default="DMOR PAINTS",
        blank=True,
    )

    inventory_type = models.CharField(
        max_length=2,
        choices=INVENTORY_TYPE_CHOICES,
        default=INVENTORY_TYPE_FINISHED,
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Master"
        verbose_name_plural = "Product Masters"

    def __str__(self):
        return f"{self.base_product.name} ({self.get_inventory_type_display()})"
    
class TermCondition(models.Model):
    term_name = models.CharField("Term", max_length=200)
    description = models.TextField("Conditions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Term & Condition"
        verbose_name_plural = "Terms & Conditions"
        ordering = ["id"]

    def __str__(self):
        return self.term_name
    
COMPANY_SIZE_CHOICES = [
    ("SMALL", "Small"),
    ("MEDIUM", "Medium"),
    ("LARGE", "Large"),
]


class Customer(models.Model):
    company_name = models.CharField("Company", max_length=200)

    sales_person = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
        verbose_name="Sales Person",
    )

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    landline_no = models.CharField("Landline No", max_length=20, blank=True)
    manager_name = models.CharField("Manager", max_length=150, blank=True)
    email = models.EmailField("Email ID", blank=True)
    proprietor_dob = models.DateField("Proprietor DOB", null=True, blank=True)

    company_size = models.CharField(
        "Company Size",
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True,
    )
    location = models.CharField("Location", max_length=100, blank=True)
    gst_no = models.CharField("GST No", max_length=30, blank=True)
    proprietor_name = models.CharField("Proprietor Name", max_length=150, blank=True)
    mobile_no1 = models.CharField("Mobile No 1", max_length=20, blank=True)
    mobile_no2 = models.CharField("Mobile No 2", max_length=20, blank=True)
    reference_name = models.CharField("Refrance Name", max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name
    
class ProductBOM(models.Model):
    """
    Product BOM Master
    - Category = which base product/category this BOM line is for
    - per_percent = Per % (e.g. 100, 50, etc.)
    - density = density value
    - hours = production hours
    """
    category = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="bom_records",
        verbose_name="Category",
    )
    per_percent = models.DecimalField("Per %", max_digits=6, decimal_places=2)
    density = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Product BOM"
        verbose_name_plural = "Product BOM Master"
        unique_together = ("category",)

    def __str__(self):
        return f"{self.category.name} – {self.per_percent}%"
    
class ProductDevelopment(models.Model):
    """
    Product Development master record.
    This is the header-level info: which category we are developing,
    what Per %, density and hours are used.
    """
    category = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="developments",
        verbose_name="Category",
    )
    per_percent = models.DecimalField("Per %", max_digits=6, decimal_places=2)
    density = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Product Development"
        verbose_name_plural = "Product Development"

        # one development record per category (similar to BOM), tweak if you want multiples
        unique_together = ("category",)

    def __str__(self):
        return f"{self.category.name} – {self.per_percent}%"