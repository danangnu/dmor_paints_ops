# operations/forms.py
from django import forms
from .models import Order, Batch, BatchItem

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "company", "address", "city", "mobile2",
            "sales_person", "location", "mobile1",
            "product_name", "quantity", "discount_amount",
            "price", "discount", "total_price",
            "remark",
        ]
        widgets = {
            "company": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Company Name"
            }),
            "address": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Address"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "City"
            }),
            "mobile2": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Mobile 2"
            }),
            "sales_person": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Sales Person"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Location"
            }),
            "mobile1": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Mobile 1"
            }),
            "product_name": forms.TextInput(attrs={
                "class": "form-control slim", "placeholder": "Product Name"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control slim", "placeholder": "Quantity"
            }),
            "discount_amount": forms.NumberInput(attrs={
                "class": "form-control slim", "placeholder": "Discount Amount"
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control slim", "placeholder": "Price"
            }),
            "discount": forms.NumberInput(attrs={
                "class": "form-control slim", "placeholder": "Discount"
            }),
            "total_price": forms.NumberInput(attrs={
                "class": "form-control slim", "placeholder": "Total Price"
            }),
            "remark": forms.Textarea(attrs={
                "class": "form-control slim", "placeholder": "Remark", "rows": 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fields with * in the UI – make sure they are required
        for name in ["company", "address", "city",
                     "mobile1", "mobile2", "sales_person", "location"]:
            self.fields[name].required = True

        # optional numeric fields
        for name in ["quantity", "discount_amount", "price", "discount", "total_price"]:
            self.fields[name].required = False

    # --- Numeric validation helpers ---

    def _clean_non_negative_decimal(self, field_name, label):
        value = self.cleaned_data.get(field_name)
        if value is None:
            return value  # still optional
        if value < 0:
            raise forms.ValidationError(f"{label} cannot be negative.")
        return value

    def clean_quantity(self):
        return self._clean_non_negative_decimal("quantity", "Quantity")

    def clean_discount_amount(self):
        return self._clean_non_negative_decimal("discount_amount", "Discount amount")

    def clean_price(self):
        return self._clean_non_negative_decimal("price", "Price")

    def clean_discount(self):
        return self._clean_non_negative_decimal("discount", "Discount")

    def clean_total_price(self):
        return self._clean_non_negative_decimal("total_price", "Total price")

    def clean(self):
        cleaned = super().clean()

        # Example extra logic: if quantity and price are provided, suggest total_price
        qty = cleaned.get("quantity")
        price = cleaned.get("price")
        total = cleaned.get("total_price")
        if qty is not None and price is not None and total is not None:
            expected = qty * price
            # you can add tolerance if you want
            if total > expected + (cleaned.get("discount_amount") or 0):
                self.add_error("total_price",
                               "Total price seems too high for given quantity/price/discount.")

        return cleaned

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["supervisor", "labour", "category", "base_qty", "production_qty", "remark"]
        widgets = {
            "supervisor": forms.TextInput(attrs={"class": "form-control slim", "placeholder": "Select Supervisor"}),
            "labour": forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Enter Labour"}),
            "category": forms.TextInput(attrs={"class": "form-control slim", "placeholder": "Category"}),
            "base_qty": forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Qty"}),
            "production_qty": forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Production Qty"}),
            "remark": forms.Textarea(attrs={"class": "form-control slim", "rows": 2, "placeholder": "Remark"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # required like the red * in UI
        for name in ["supervisor", "labour", "category", "base_qty", "production_qty"]:
            self.fields[name].required = True


class BatchItemForm(forms.ModelForm):
    class Meta:
        model = BatchItem
        fields = ["product", "qty"]
        widgets = {
            "product": forms.TextInput(attrs={"class": "form-control slim", "placeholder": "Product"}),
            "qty": forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Qty"}),
        }