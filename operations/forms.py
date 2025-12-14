# operations/forms.py
from django import forms
from .models import Order, Batch, BatchItem, Dispatch, Vehicle, MaterialInward, MasterProduct, Supplier, MaterialDiscard
from masters.models import Employee, Product

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
    """
    BOM Production header form
    - supervisor: dropdown from masters.Employee
    - labour: text input
    - category: dropdown from masters.Product (BOM Category)
    - base_qty: number
    - production_qty: number
    """

    supervisor = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by("full_name", "id"),
        empty_label="Select",
        required=True,
        widget=forms.Select(attrs={"class": "form-control slim"}),
    )

    category = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by("name", "id"),
        empty_label="Select",
        required=True,
        widget=forms.Select(attrs={"class": "form-control slim"}),
    )

    labour = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control slim", "placeholder": "Enter Labour"}),
    )

    base_qty = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Qty"}),
    )

    production_qty = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Production Qty"}),
    )

    remark = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control slim", "rows": 2, "placeholder": "Remark"}),
    )

    class Meta:
        model = Batch
        fields = ["supervisor", "labour", "category", "production_qty", "remark"]

class BatchItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=MasterProduct.objects.order_by("name", "id"),
        empty_label="Select",
        widget=forms.Select(attrs={"class": "form-control slim"}),
        required=True,
    )

    class Meta:
        model = BatchItem
        fields = ["product", "qty"]
        widgets = {
            "qty": forms.NumberInput(attrs={"class": "form-control slim", "placeholder": "Qty"}),
        }

    def __init__(self, *args, **kwargs):
        product_qs = kwargs.pop("product_qs", None)
        super().__init__(*args, **kwargs)
        if product_qs is not None:
            self.fields["product"].queryset = product_qs

class DispatchHeaderForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = ["vehicle", "remark"]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-control slim"}),
            "remark": forms.Textarea(attrs={
                "class": "form-control slim",
                "rows": 3,
                "placeholder": "Dispatch Remark",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].empty_label = "Select"
        self.fields["vehicle"].required = True

class MaterialInwardForm(forms.ModelForm):
    class Meta:
        model = MaterialInward
        fields = ["master_product", "supplier", "inward_date", "bill_no", "remark"]
        widgets = {
            "master_product": forms.Select(attrs={"class": "form-control slim"}),
            "supplier": forms.Select(attrs={"class": "form-control slim", "placeholder": "Supplier"}),
            "inward_date": forms.DateInput(
                attrs={"class": "form-control slim", "type": "date"}
            ),
            "bill_no": forms.TextInput(
                attrs={"class": "form-control slim", "placeholder": "Bill No"}
            ),
            "remark": forms.Textarea(
                attrs={
                    "class": "form-control slim",
                    "rows": 3,
                    "placeholder": "Remark",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # red-star fields = required
        for name in ["master_product", "supplier", "inward_date", "bill_no"]:
            self.fields[name].required = True

        self.fields["master_product"].empty_label = "Select"
        self.fields["supplier"].empty_label = "Supplier"

class MaterialDiscardForm(forms.ModelForm):
    class Meta:
        model = MaterialDiscard
        fields = ["category", "remark"]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "remark": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Remark",
                }
            ),
        }
        labels = {
            "category": "Category",
            "remark": "Remark",
        }