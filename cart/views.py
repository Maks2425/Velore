from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product

from .models import Cart, CartItem


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product", "product__brand").prefetch_related("product__images")
    return render(request, "cart/cart_detail.html", {"cart": cart, "items": items})


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product.objects.available(), pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()
    messages.success(request, f"«{product.name}» додано до кошика.")
    return redirect(request.POST.get("next") or "cart:view_cart")


@login_required
@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = min(quantity, item.product.stock or quantity)
        item.save()
    return redirect("cart:view_cart")


@login_required
@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Товар видалено з кошика.")
    return redirect("cart:view_cart")
