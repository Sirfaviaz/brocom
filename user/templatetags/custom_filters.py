from django import template

register = template.Library()

@register.filter(name='stars')
def stars(value):
    """
    Converts a numerical rating into a list representing stars.
    Assumes a rating between 1 and 5.
    """
    full_stars = int(value)
    half_star = 1 if value - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    return [1] * full_stars + [0.5] * half_star + [0] * empty_stars


@register.filter(name='apply_discount')
def apply_discount(price, discount):
    if discount is not None:
        if discount.is_percentage:
            discounted_price = price - (price * (discount.disc_value / 100))
        else:
            discounted_price = price - discount.disc_value

        return round(discounted_price, 2)

    return price