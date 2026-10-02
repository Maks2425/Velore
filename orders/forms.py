from django import forms

from .models import Payment


class CheckoutForm(forms.Form):
    shipping_full_name = forms.CharField(label="Повне ім'я", max_length=150)
    shipping_address = forms.CharField(label="Адреса доставки", max_length=255)
    shipping_city = forms.CharField(label="Місто", max_length=100)
    shipping_postal_code = forms.CharField(label="Поштовий індекс", max_length=20)
    shipping_phone = forms.CharField(label="Телефон", max_length=32)
    payment_method = forms.ChoiceField(label="Спосіб оплати", choices=Payment.Method.choices)
    # Demo-only card fields: never collect real card data. These are not
    # validated against any processor and are not stored — only the last
    # 4 characters typed here become `masked_reference` on the Payment row.
    demo_card_number = forms.CharField(
        label="Номер картки (демо)", max_length=19, required=False,
        widget=forms.TextInput(attrs={"placeholder": "4242 4242 4242 4242", "autocomplete": "off"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_method") == Payment.Method.MOCK_CARD and not cleaned.get("demo_card_number"):
            self.add_error("demo_card_number", "Введіть демо-номер картки для цього способу оплати.")
        return cleaned
