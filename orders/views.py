from datetime import datetime
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Cart 
from product.models import Product, ProductChildVariant, ProductInventory
from user.models import Address, OrderDetails, User, Wallet
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.shortcuts import render
from .models import Product, Cart, User, Coupon,AppliedCoupon
from django.contrib import messages
from .forms import CouponForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from django.db.models import Case, When, DecimalField


# Create your views here.








def view_cart(request):
    """
    View function for displaying the user's shopping cart.

    Retrieves the cart items from the session and calculates the total price for each item,
    considering any discounts applied at different levels (child variant, parent variant, product, or category).
    Also computes the subtotal for all items in the cart.

    Parameters:
    - request: HttpRequest object representing the request from the client.

    Returns:
    - HttpResponse: Renders the 'view_cart.html' template with the cart details,
                    including product name, size, color, price, quantity, and subtotal.
                    If the user is not logged in, redirects to the login page.
    """
    session_data = dict(request.session)

   
 

    if 'username' in request.session:
        username = request.session['username']
        user = User.objects.get(username=username)

        all_child_variant_ids = Cart.objects.filter(user=user).values_list('child_variant_id', flat=True)

        child_with_cart = ProductChildVariant.objects.filter(id__in=all_child_variant_ids).prefetch_related('cart_set')

        product_details = []
        subtotal = 0  # Initialize subtotal

        for product in child_with_cart:
            # Initialize total price for the product
            total_price = 0

            # Initialize discount details for the product
            discount_type = ''
            discount_amount = 0

            # Check for discounts in child variant
            if product.discount is not None:
                if product.discount.is_percentage:
                    discount_percentage = product.discount.disc_value
                    discount_amount = (discount_percentage / 100) * product.price
                    discount_type = '%'
                else:
                    discount_amount = product.discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in child variant, check for discounts in parent variant
            elif product.parent_variant.discount is not None:
                parent_discount = product.parent_variant.discount
                if parent_discount.is_percentage:
                    discount_percentage = parent_discount.disc_value
                    discount_amount = (discount_percentage / 100) * product.price
                    discount_type = '%'
                else:
                    discount_amount = parent_discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in parent variant, check for discounts in product
            elif product.parent_variant.product.discount is not None:
                product_discount = product.parent_variant.product.discount
                if product_discount.is_percentage:
                    discount_percentage = product_discount.disc_value
                    discount_amount = (discount_percentage / 100) * product.price
                    discount_type = '%'
                else:
                    discount_amount = product_discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in product, check for discounts in category
            elif product.parent_variant.product.category.discount is not None:
                category_discount = product.parent_variant.product.category.discount
                if category_discount.is_percentage:
                    discount_percentage = category_discount.disc_value
                    discount_amount = (discount_percentage / 100) * product.price
                    discount_type = '%'
                else:
                    discount_amount = category_discount.disc_value
                    discount_type = 'Rs.'

            # Calculate the discounted price
            discounted_price = product.price - discount_amount

            # Multiply discounted price by quantity
            total_price = discounted_price * product.cart_set.first().quantity

            # Append product details to the list
            product_details.append({
                'cart_id': product.cart_set.first().id,
                'id': product.id,
                'name': product.parent_variant.product.name,
                'size': product.inventory_child.size,
                'color': product.parent_variant.inventory_parent.color,
                'price': format(total_price, ".2f"),  # Format to two decimal places
                'image': product.parent_variant.main_image,
                'quantity': product.cart_set.first().quantity,
                'status': product.cart_set.first().status,
                'p_p_price': product.price,
            })

            # Accumulate total_price for subtotal
            subtotal += total_price

        context = {'products': product_details, 'subtotal': format(subtotal, ".2f")}  # Format subtotal to two decimal places
        return render(request, 'view_cart.html', context)
    else:
        return render(request, 'user_login.html')
    
def add_to_cart(request):
    """
    View function for adding a product to the user's shopping cart.

    Retrieves the logged-in user from the session and the product's child variant ID from the request parameters.
    Checks if the product is already in the user's cart, and if not, creates a new entry in the Cart model.
    Redirects the user to the 'view_cart' page after adding the product to the cart.

    Parameters:
    - request: HttpRequest object representing the request from the client.

    Returns:
    - HttpResponseRedirect: Redirects the user to the 'view_cart' page after adding the product to the cart.
    """
    
   
    if 'username' in request.session:
        username = request.session['username']
        user = User.objects.get(username=username)
        
        if request.GET.get('child_variant'):
        
            child_id = request.GET.get('child_variant')
      
            variant = ProductChildVariant.objects.get(id = child_id)
            if Cart.objects.filter(user = user, child_variant_id = child_id).exists():
                return redirect('view_cart')
            
            Cart.objects.create(user = user, child_variant_id = child_id,quantity=1)


        
        
        # Check if the product is already in the cart
        if Cart.objects.filter(user=user, child_variant_id=child_id).exists():
            # Handle the case where the product is already in the cart
            return redirect('view_cart')
        
        # Create a new entry in the Cart model
        Cart.objects.create(user=user, child_variant_id=child_id, quantity = 1)
        
        # # Retrieve the added product
        # product = get_object_or_404(Product, id=product_id)
        
        # # Pass the product to the template
        # context = {'product': product}
        return redirect('view_cart')    

@csrf_exempt
def update_quantity(request):
    """
    View function for updating the quantity of a product in the user's cart.

    Retrieves the product ID and new quantity from the POST request.
    Checks if the user is authenticated and retrieves the user's cart entry for the specified product.
    Validates the requested quantity against the available inventory and updates the cart entry accordingly.
    Calculates the discounted price, product price, and subtotal after updating the quantity.
    Returns a JSON response with the updated quantity, product price, and subtotal.

    Parameters:
    - request: HttpRequest object representing the request from the client.

    Returns:
    - JsonResponse: JSON response with the updated quantity, product price, and subtotal.
    """
 

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_quantity = int(request.POST.get('new_quantity', 0))
        username = request.session.get('username')
        
        if not username:
            return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

        user = get_object_or_404(User, username=username)
        user_id = user.id

        try:
            cart_entry = Cart.objects.get(user_id=user_id, child_variant_id=product_id, status=True)
            if new_quantity == 0:
                cart_entry.status = False
                cart_entry.save()
            # Update quantity and save cart entry
           
            
            cart_entry.quantity = new_quantity
            cart_entry.save()
            
            # Check if the requested quantity is higher than the inventory
            if new_quantity > cart_entry.child_variant.inventory_child.quantity:
                return JsonResponse({'status': 'error', 'message': 'Requested quantity exceeds available inventory'})

            # Initialize discount details
            discount_type = ''
            discount_amount = 0

            # Check for discounts in child variant
            if cart_entry.child_variant.discount is not None:
                if cart_entry.child_variant.discount.is_percentage:
                    discount_percentage = cart_entry.child_variant.discount.disc_value
                    discount_amount = (discount_percentage / 100) * cart_entry.child_variant.price
                    discount_type = '%'
                else:
                    discount_amount = cart_entry.child_variant.discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in child variant, check for discounts in parent variant
            elif cart_entry.child_variant.parent_variant.discount is not None:
                parent_discount = cart_entry.child_variant.parent_variant.discount
                if parent_discount.is_percentage:
                    discount_percentage = parent_discount.disc_value
                    discount_amount = (discount_percentage / 100) * cart_entry.child_variant.price
                    discount_type = '%'
                else:
                    discount_amount = parent_discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in parent variant, check for discounts in product
            elif cart_entry.child_variant.parent_variant.product.discount is not None:
                product_discount = cart_entry.child_variant.parent_variant.product.discount
                if product_discount.is_percentage:
                    discount_percentage = product_discount.disc_value
                    discount_amount = (discount_percentage / 100) * cart_entry.child_variant.price
                    discount_type = '%'
                else:
                    discount_amount = product_discount.disc_value
                    discount_type = 'Rs.'

            # If no discount found in product, check for discounts in category
            elif cart_entry.child_variant.parent_variant.product.category.discount is not None:
                category_discount = cart_entry.child_variant.parent_variant.product.category.discount
                if category_discount.is_percentage:
                    discount_percentage = category_discount.disc_value
                    discount_amount = (discount_percentage / 100) * cart_entry.child_variant.price
                    discount_type = '%'
                else:
                    discount_amount = category_discount.disc_value
                    discount_type = 'Rs.'

            # Calculate the discounted price
            discounted_price = cart_entry.child_variant.price - discount_amount

            

            # Set status to False if new quantity is 0
            

            # Calculate product price
            product_price = (Decimal(cart_entry.quantity) * discounted_price).quantize(Decimal('0.00'))

            # Calculate subtotal
            subtotal = calculate_subtotal(user_id)
            
            
            
            return JsonResponse({
                'status': 'success',
                'quantity': cart_entry.quantity,
                'product_price': product_price,
                'subtotal': subtotal
            })
        except Cart.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cart entry not found'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def calculate_subtotal(user_id):
    """
    Calculate the subtotal of all products in the user's cart.

    Retrieves the IDs of all products in the user's cart with status=True.
    Retrieves product details for each cart entry and calculates the discounted price for each product.
    Accumulates the total price for all products to compute the subtotal.
    
    Parameters:
    - user_id (int): The ID of the user whose cart subtotal is to be calculated.

    Returns:
    - Decimal: The subtotal of all products in the user's cart, considering discounts and quantities.
    """
    all_product_ids = Cart.objects.filter(user_id=user_id, status=True).values_list('child_variant_id', flat=True)

    products_with_cart = ProductChildVariant.objects.filter(id__in=all_product_ids).prefetch_related('cart_set', 'parent_variant__product__category__discount', 'parent_variant__product__discount', 'parent_variant__discount', 'discount')

    subtotal = 0  # Initialize subtotal
   
   

    for product in products_with_cart:
        # Initialize discount details
        discount_type = ''
        discount_amount = 0

        # Check for discounts in child variant
        if product.discount is not None:
            if product.discount.is_percentage:
                discount_percentage = product.discount.disc_value
                discount_amount = (discount_percentage / 100) * product.price
                discount_type = '%'
            else:
                discount_amount = product.discount.disc_value
                discount_type = 'Rs.'

        # If no discount found in child variant, check for discounts in parent variant
        elif product.parent_variant.discount is not None:
            parent_discount = product.parent_variant.discount
            if parent_discount.is_percentage:
                discount_percentage = parent_discount.disc_value
                discount_amount = (discount_percentage / 100) * product.price
                discount_type = '%'
            else:
                discount_amount = parent_discount.disc_value
                discount_type = 'Rs.'

        # If no discount found in parent variant, check for discounts in product
        elif product.parent_variant.product.discount is not None:
            product_discount = product.parent_variant.product.discount
            if product_discount.is_percentage:
                discount_percentage = product_discount.disc_value
                discount_amount = (discount_percentage / 100) * product.price
                discount_type = '%'
            else:
                discount_amount = product_discount.disc_value
                discount_type = 'Rs.'

        # If no discount found in product, check for discounts in category
        elif product.parent_variant.product.category.discount is not None:
            category_discount = product.parent_variant.product.category.discount
            if category_discount.is_percentage:
                discount_percentage = category_discount.disc_value
                discount_amount = (discount_percentage / 100) * product.price
                discount_type = '%'
            else:
                discount_amount = category_discount.disc_value
                discount_type = 'Rs.'

        # Calculate the discounted price
        discounted_price = product.price - discount_amount
     
     

        # Accumulate total_price for subtotal
        subtotal += product.cart_set.first().quantity * discounted_price.quantize(Decimal('0.00'))
        
      
      
    return subtotal



def toggle_product(request):
    """
    Toggle the status of a product in the user's cart.

    This function handles POST requests to toggle the status (checked/unchecked) of a product in the user's cart.
    It expects 'product_id' and 'is_checked' parameters in the request.
    If 'is_checked' is 'true', the product's status will be set to True (checked); otherwise, it will be set to False (unchecked).
    The status update is applied to the Cart model.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the product ID and status information.

    Returns:
    - JsonResponse: A JSON response indicating the success or failure of the operation.
                    If successful, returns {'status': 'success'}.
                    If the request method is not POST, returns {'status': 'error'}.
    """
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        is_checked = request.POST.get('is_checked')
     
        if is_checked == 'true':
            is_checked = True
        else:
            is_checked = False
        
        Cart.objects.filter(product_id=product_id).update(status=is_checked)
      
        

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'})
    



def delete_cart_product(request):
    """
    Delete a product from the user's cart.

    This function handles POST requests to delete a product from the user's cart.
    It expects the 'product_id' parameter in the request, which represents the ID of the product to be deleted.
    The product is identified in the Cart model by its 'child_variant_id'.
    If the product is found in the cart, it is deleted from the database.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the product ID.

    Returns:
    - JsonResponse: A JSON response indicating the success or failure of the operation.
                    If successful, returns {'success': True}.
                    If the request method is not POST, returns {'success': False, 'error': 'Invalid request method'}.
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        cart_product = get_object_or_404(Cart, child_variant_id=product_id)
        cart_product.delete()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    


def add_button(request, cart_id):
    cart_entry = get_object_or_404(Cart, id=cart_id)
    product_inventory = get_object_or_404(ProductInventory, id=cart_entry.product_id)

   
    if cart_entry.quantity + 1 > product_inventory.quantity:
        messages.error(request, "Requirement exceeds the limit. Cannot add more to the cart.")
    else:
        cart_entry.quantity += 1
        cart_entry.save()
        messages.success(request, "Item added to the cart successfully.")

    return redirect('view_cart')

def sub_button(request,cart_id):

    cart_entry = get_object_or_404(Cart, id=cart_id)
    
    
    if cart_entry.quantity > 1:
        cart_entry.quantity -= 1
        cart_entry.save()
    
    return redirect('view_cart')

def delete_button(request, cart_id):
    cart_entry = get_object_or_404(Cart, id=cart_id)
    cart_entry.delete()
  
    return redirect('view_cart')





from django.db.models import Sum, F

def check_out(request):
    """
    Process the checkout procedure for the user.

    This function handles the checkout process for the user. It retrieves the necessary information from the session
    and database to calculate the subtotal, delivery charges, savings, total amount, and user wallet balance. It also
    retrieves the user's addresses for delivery options.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - HttpResponse: A rendered HTML page displaying the checkout details and options.
    - HttpResponseRediect: If the user is not authenticated, redirects to the login page.
    """
    if 'username' not in request.session:
        return redirect('user_login')

    username = request.session['username']
    user = User.objects.get(username=username)

    user_id = user.id

    addinfo = Address.objects.filter(user_id=user_id)

    all_product_ids = Cart.objects.filter(user=user).values_list('child_variant_id', flat=True)

    products_with_cart = ProductChildVariant.objects.filter(id__in=all_product_ids).prefetch_related('cart_set', 'parent_variant__product__category__discount', 'parent_variant__product__discount', 'parent_variant__discount', 'discount')

    # Integrate discount calculations into the annotation
    products_with_cart = products_with_cart.annotate(
        discount_amount=Case(
            # Check for discount at child variant level
            When(discount__is_percentage=True, then=F('cart__quantity') * F('price') * (F('discount__disc_value') / 100)),
            When(discount__is_percentage=False, then=F('cart__quantity') * F('discount__disc_value')),
            # If no discount at child variant level, check for parent variant level discount
            When(parent_variant__discount__is_percentage=True, then=F('cart__quantity') * F('price') * (F('parent_variant__discount__disc_value') / 100)),
            When(parent_variant__discount__is_percentage=False, then=F('cart__quantity') * F('parent_variant__discount__disc_value')),
            # If no discount at parent variant level, check for product level discount
            When(parent_variant__product__discount__is_percentage=True, then=F('cart__quantity') * F('price') * (F('parent_variant__product__discount__disc_value') / 100)),
            When(parent_variant__product__discount__is_percentage=False, then=F('cart__quantity') * F('parent_variant__product__discount__disc_value')),
            # If no discount at product level, check for category level discount
            When(parent_variant__product__category__discount__is_percentage=True, then=F('cart__quantity') * F('price') * (F('parent_variant__product__category__discount__disc_value') / 100)),
            When(parent_variant__product__category__discount__is_percentage=False, then=F('cart__quantity') * F('parent_variant__product__category__discount__disc_value')),
            default=0,
            output_field=DecimalField()
        ),
        total_price=Sum(F('cart__quantity') * F('price') - F('discount_amount'))
    )

    # Print each product with its discount amount and total price
    

    savings = round(sum(product.discount_amount or 0 for product in products_with_cart), 2)
    subtotal = calculate_subtotal(user_id)
    delivery = 50

    total = round(subtotal + delivery , 2)
    

    try:
        user_wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        # If no wallet found, create one
        user_wallet = Wallet.objects.create(user=user)
    balance = user_wallet.balance

    address = 0

    if address != 0:
        address = Address.objects.get(id=address)

   
    context = {
        'infos': addinfo,
        'subtotal': subtotal,
        'delivery': delivery,
        'savings': savings,
        'total': total,
        'balance': balance,
        'address': address
    }

    return render(request, 'check_out.html', context)




@require_GET
def select_address_ajax(request):
    address_id = request.GET.get('address_id')

    # Perform any additional validation if needed

    address = get_object_or_404(Address, id=address_id)

    # Assuming you have a method to serialize the address details, adjust as needed
    phone_number = str(address.mobile) if address.mobile else None
    address_id = str(address.id) if address.id else None
    address_details = {
        'Id':address_id,
        'Name': address.Name,
        'address_line_1': address.address_line_1,
        'address_line_2': address.address_line_2,
        'city': address.city,
        'country': address.country,
        'pincode': address.pincode,
        'mobile': phone_number,
    }

    response_data = {
        'success': True,
        'addressDetails': address_details,
        'message': 'Address selected successfully.',
    }

    return JsonResponse(response_data)


# from django.http import JsonResponse
# from django.shortcuts import redirect
# from django.contrib import messages
# from datetime import datetime
# from .models import User, Coupon, AppliedCoupon

def validate_coupon(request):
 
    if request.method == 'POST':
        username = request.session['username']
        coupon_code = request.POST.get('coupon_code')

        subtotal = float(request.POST.get('subtotal'))
        savings = float(request.POST.get('savings', 0))  # Default to 0 if not provided
        delivery = 50

        user = User.objects.get(username=username)
        user_id = user.id

       
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
            except Coupon.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

            current_datetime = datetime.now().date()
            if coupon.exp_date < current_datetime:
                return JsonResponse({'success': False, 'message': 'Coupon has expired.'})
            
            if coupon.count >= coupon.max_user:
                return JsonResponse({'success': False, 'message': 'Coupon reached its user limit.'})
            
           
           


            # total = subtotal + delivery
            tot = subtotal+delivery
            if coupon.min_order >= tot:
                
                return JsonResponse({'success': False, 'message': f'Coupon requires a minimum order of {coupon.min_order}.'})

           
            coupon_id = coupon.id
            if AppliedCoupon.objects.filter(user_id=user_id, coupon_id=coupon_id).exists():
                
                return JsonResponse({'success': False, 'message': f'Coupon Already Claimed.'})
                return redirect('check_out')

            # Calculate coupon value based on the type
            coupon_type = coupon.coupon_type
            if coupon_type == '%':
                # Calculate coupon value as a percentage of the subtotal
                coupon_value = (coupon.coupon_value / 100) * subtotal
            elif coupon_type == '$':
                # Coupon value is a fixed amount
                coupon_value = coupon.coupon_value
            else:
                return JsonResponse({'success': False, 'message': 'Invalid coupon type.'})

            # Calculate the total after applying the coupon
            total = (subtotal + delivery) - (coupon_value)

            response_data = {
                'success': True,
                'couponValue': coupon_value,
                'savings': savings + coupon_value,
                'total': total,
                'couponCode': coupon_code,
                'message': 'Coupon applied successfully.',
            }

        else:
            # If no coupon code provided, calculate total without reducing coupon value
            total = subtotal + delivery - savings

            response_data = {
                'success': True,
                'couponValue': 0,  # No coupon applied
                'savings': savings,
                'total': total,
                'couponCode': '',
                'message': 'No coupon applied.',
            }

        return JsonResponse(response_data)

    return JsonResponse({'success': False, 'message': 'Invalid request.'})









def check_out_delete_address(request,id):
    address = get_object_or_404(Address, id=id)
    address.delete()

    return redirect('check_out')

def check_out_edit_address(request,id):
    
    address = get_object_or_404(Address, id=id, user__username=request.session['username'])

    if request.method == 'POST':
       
        address.Name = request.POST.get('name')
        address.address_line_1 = request.POST.get('address_l1')
        address.address_line_2 = request.POST.get('address_l2')
        address.pincode = request.POST.get('pincode')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.mobile = request.POST.get('mobile')

        
        address.save()

        return redirect(reverse('check_out'))  

    return render(request, 'check_out_edit_address.html', {'address': address})

    return redirect(request,'address' )

# admin coupon






def coupon_create(request):
    if request.method == "POST":
        code = request.POST.get('code')
        coupon_type = request.POST.get('coupon_type')
        coupon_value = request.POST.get('coupon_value')
        min_order = request.POST.get('min_order')
        max_user = request.POST.get('max_user')
        count = request.POST.get('count')
        exp_date = request.POST.get('exp_date')
        if Coupon.objects.filter(code = code):
            messages.error(request, " Coupon code exist")
        else:
            try:
                coupon = Coupon(
                    code=code,
                    coupon_type=coupon_type,
                    coupon_value=coupon_value,
                    min_order=min_order,
                    max_user=max_user,
                    count=count,
                    exp_date=exp_date
             )
                coupon.full_clean()  
                coupon.save()
                messages.success(request, "Coupon successfully created")
            except ValidationError as e:
                messages.error(request, _(str((e.get('__all__', [])[0]))))
            

        return redirect('coupon_admin')
    else:
        
        return render(request, 'coupon_admin.html')  




def coupon_edit(request, id):
    if request.method == "POST":
        code = request.POST.get('code')
        coupon_type = request.POST.get('coupon_type')
        coupon_value = request.POST.get('coupon_value')
        min_order = request.POST.get('min_order')
        max_user = request.POST.get('max_user')
        count = request.POST.get('count')
        exp_date = request.POST.get('exp_date')

 
        try:
            coupon = Coupon.objects.get(id=id)
            if Coupon.objects.filter(code = code):
                messages.error(request, "Coupon name already  exist")
            else:
                coupon.code = code
                coupon.coupon_type = coupon_type
                coupon.coupon_value = coupon_value
                coupon.min_order = min_order
                coupon.max_user = max_user
                coupon.count = count
                coupon.exp_date = exp_date

                coupon.full_clean()  # Validate model fields, including custom clean method
                coupon.save()
                messages.success(request, "Coupon successfully updated")
        except Coupon.DoesNotExist:
                messages.error(request, "Coupon does not exist")
        except ValidationError as e:
            messages.error(request, _(str(e.get('__all__', [])[0])))
           

        return redirect('coupon_admin')
    else:
        # Handle GET request if needed
        return render(request, 'coupon_admin.html')  # Replace 'your_template.html' with your actual template


def coupon_delete(request, id):
    try:
        coupon = Coupon.objects.get(id=id)
        coupon.delete()
        messages.success(request, "Coupon successfully deleted")
    except Coupon.DoesNotExist:
        messages.error(request, "Coupon does not exist")

    return redirect('coupon_admin')


def coupon_admin(request):
    if 'admin' not in request.session:
        return redirect('admin_login') 

    coupons = Coupon.objects.all()
    # date = coupons.date
    # date.strftime("%d-%m-%y")

    context = {
        'coupons': coupons,
    }

    return render(request, 'coupon_admin.html', context)

def check_out_add_address(request):
    if 'username' in request.session:
        username = request.session['username']
        name = request.POST.get('name')
        address_l1 = request.POST.get('address_l1')
        address_l2 = request.POST.get('address_l2')
        is_default = request.POST.get('is_default')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        mobile = request.POST.get('mobile')
        pincode = request.POST.get('pincode')  

        user = User.objects.get(username=username)
        
     
        address = Address.objects.create(
            user=user,
            Name=name,
            address_line_1=address_l1,
            address_line_2=address_l2,
            pincode=pincode,  
            
            city=city,
            state=state,
            country=country,
            mobile=mobile
        )

       
        if is_default == 'on':
                is_default = True
            
                Address.objects.filter(user=user).exclude(id=address.id).update(is_default=False)
               
        

    return redirect('check_out')




# def check_out_test(request):
#     if 'username' not in request.session:
#         redirect('user_login')

    













