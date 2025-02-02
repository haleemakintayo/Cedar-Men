# cart/context_processors.py
from .utils import get_cart

def cart_summary(request):
    """
    Injects the current cart into the context for all templates.
    """
    return {
        'cart': get_cart(request)
    }
