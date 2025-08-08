from .models import Cart

def get_or_create_cart(request):
    """
    Retrieves or creates a cart for the current request's user/session.
    Handles both authenticated and anonymous users.
    """
    # For authenticated users, try to get their cart.
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # If the user also had an anonymous cart, we can merge them here (optional advanced logic)
        return cart

    # For anonymous users, use the session key.
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart