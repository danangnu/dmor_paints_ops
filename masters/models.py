from django.db import models
from django.utils import timezone

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