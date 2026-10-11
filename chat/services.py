from django.conf import settings
from django.utils.translation import get_language
from openai import OpenAI

from catalog.models import Brand, Category


class AIUnavailable(Exception):
    pass


_LANGUAGE_NAMES = {"uk": "українською", "en": "in English"}


def build_system_prompt() -> str:
    brands = ", ".join(Brand.objects.filter(is_active=True).values_list("name", flat=True))
    categories = ", ".join(Category.objects.values_list("name", flat=True))
    language_instruction = _LANGUAGE_NAMES.get(get_language(), _LANGUAGE_NAMES["uk"])
    return (
        "Ти — помічник інтернет-магазину Velore (брендовий одяг, взуття та парфуми). "
        f"Відповідай {language_instruction}, коротко і ввічливо. "
        f"Бренди в магазині: {brands}. Категорії: {categories}. "
        "Клієнт може оформити замовлення в кошику; оплата в магазині демонстраційна; "
        "статус замовлення видно в розділі «Замовлення». "
        "Не вигадуй умови доставки, повернення, знижок чи наявності товарів. "
        "Якщо питання про це, порадь звернутися до консультанта в цьому ж віджеті."
    )


def ai_reply(history: list[dict]) -> str:
    if not settings.OPENAI_API_KEY:
        raise AIUnavailable("OPENAI_API_KEY is not configured")
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "system", "content": build_system_prompt()}, *history],
        max_tokens=500,
    )
    return response.choices[0].message.content or ""
