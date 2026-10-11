from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Brand, Category, Product, Review


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ("newest", _("Новинки")),
        ("price_asc", _("Ціна: від низької")),
        ("price_desc", _("Ціна: від високої")),
        ("name", _("Назва А–Я")),
    ]

    q = forms.CharField(required=False, max_length=100)
    gender = forms.ChoiceField(
        required=False,
        choices=[("", _("Усі"))] + list(Product.Gender.choices),
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        to_field_name="slug",
        empty_label=_("Усі категорії"),
    )
    brand = forms.ModelChoiceField(
        required=False,
        queryset=Brand.objects.filter(is_active=True),
        to_field_name="slug",
        empty_label=_("Усі бренди"),
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


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "body")
        widgets = {
            "rating": forms.Select(choices=Review.RATING_CHOICES),
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": _("Поділіться враженням про товар (необов'язково)")}),
        }
