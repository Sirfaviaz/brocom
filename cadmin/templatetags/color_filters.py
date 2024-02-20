from django import template
from webcolors import hex_to_rgb, rgb_to_name
import matplotlib.colors as mcolors
from webcolors import CSS3_NAMES_TO_HEX

register = template.Library()

@register.filter(name='hex_to_color_name')




def get_color_name(hex_code):
    print(hex_code)
    try:
        rgb_normalized = mcolors.hex2color(hex_code)
        closest_color = min(CSS3_NAMES_TO_HEX, key=lambda name: mcolors.rgb2hex(mcolors.CSS4_COLORS[name]))
        return closest_color
    except ValueError:
        return 'Invalid Hex Code'
