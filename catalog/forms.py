from django import forms

from .models import Brand, Category, Product


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ("newest", "Новинки"),
        ("price_asc", "Ціна: від низької"),
        ("price_desc", "Ціна: від високої"),
        ("name", "Назва А–Я"),
    ]

    q = forms.CharField(required=False, max_length=100)
    gender = forms.ChoiceField(
        required=False,
        choices=[("", "Усі")] + list(Product.Gender.choices),
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        to_field_name="slug",
        empty_label="Усі категорії",
    )
    brand = forms.ModelChoiceField(
        required=False,
        queryset=Brand.objects.filter(is_active=True),
        to_field_name="slug",
        empty_label="Усі бренди",
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, initial="newest")

    def filter_queryset(self, queryset):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data.get("q"):
            queryset = queryset.filter(name__icontains=data["q"])
        if data.get("gender"):
            queryset = queryset.filter(gender__in=[data["gender"], Product.Gender.UNISEX])
        if data.get("category"):
            queryset = queryset.filter(category=data["category"])
        if data.get("brand"):
            queryset = queryset.filter(brand=data["brand"])
        ordering = {
            "newest": "-created_at",
            "price_asc": "price",
            "price_desc": "-price",
            "name": "name",
        }[data.get("sort") or "newest"]
        return queryset.order_by(ordering)
