# masters/models.py
from django.db import models

class Employee(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField("Department", max_length=100, unique=True)
    head = models.ForeignKey(
        Employee,
        verbose_name="Department Head",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="departments",
    )

    def __str__(self):
        return self.name