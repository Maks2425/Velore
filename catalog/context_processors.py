from .models import WishlistItem


def wishlist(request):
    if not request.user.is_authenticated:
        return {"nav_wishlist_count": 0, "wishlist_ids": set()}
    ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
    return {"nav_wishlist_count": len(ids), "wishlist_ids": ids}
