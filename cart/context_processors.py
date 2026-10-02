from .models import Cart


def cart(request):
    if not request.user.is_authenticated:
        return {"nav_cart_count": 0}
    cart_obj = Cart.objects.filter(user=request.user).first()
    return {"nav_cart_count": cart_obj.total_items if cart_obj else 0}
