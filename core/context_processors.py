from catalog.models import Brand


def nav_brands(request):
    return {"nav_brands": Brand.objects.filter(is_active=True)}
