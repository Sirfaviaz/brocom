import base64
from decimal import Decimal, DecimalException
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from cadmin.forms import AddFieldForm, ProductVariantForm
from cadmin.models import  Banner, ReferralCodeHistory, ReferralRewardSchemes
from orders.models import Coupon
from product.models import Discount, Product, ProductCategory, ProductChildVariant, ProductChildVariantInventory, ProductInventory, ProductParentVariant, ProductParentVariantInventory, ProductVariantColorImages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db.models import Sum, F
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
import matplotlib.pyplot as plt
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta

from user.models import OrderDetails, OrderItems, User

# Create your views here.

def admin_index(request):
    """
    Renders the admin dashboard with statistics for the last day and the day before.
    Retrieves and calculates various metrics including user count, order count, total amount,
    sales data, revenue data, and customer count data for the last day and the day before.
    Calculates percentage changes for user count, count, and amount between the last day and the day before.
    Formats the data for JavaScript chart rendering.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Rendered admin index template with calculated statistics and formatted data.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 

    # Calculate the start and end dates for the last day
    end_date = timezone.now()
    start_date = end_date 

    # Query to get the user count for the last day
    user_count_last_day = User.objects.filter(orderdetails__created_at__date=start_date.date()).annotate(order_count=Count('orderdetails')).count()

    # Query to get the user count for the day before
    day_before_start_date = start_date - timedelta(days=1)
    user_count_day_before = User.objects.filter(orderdetails__created_at__date=day_before_start_date.date()).annotate(order_count=Count('orderdetails')).count()

    # Calculate the percentage change for user count
    if user_count_day_before == 0:
        user_percentage_change = 0
    else:
        user_percentage_change = ((user_count_last_day - user_count_day_before) / user_count_day_before) * 100

    # Query to get the total counts of entries for the last day
    last_day_count = OrderDetails.objects.filter(created_at__date=start_date.date()).count()

    # Query to get the total counts of entries for the day before
    day_before_count = OrderDetails.objects.filter(created_at__date=day_before_start_date.date()).count()

    # Calculate the percentage change for count
    if day_before_count == 0:
        count_percentage_change = 0
    else:
        count_percentage_change = ((last_day_count - day_before_count) / day_before_count) * 100

    # Query to get the sum of all amounts for the last day
    total_amount_last_day = OrderDetails.objects.filter(created_at__date=start_date.date()).aggregate(Sum('amount'))['amount__sum'] or 0

    # Query to get the sum of all amounts for the day before
    total_amount_day_before = OrderDetails.objects.filter(created_at__date=day_before_start_date.date()).aggregate(Sum('amount'))['amount__sum'] or 0

    # Calculate the percentage change for amount
    if total_amount_day_before == 0:
        amount_percentage_change = 0
    else:
        amount_percentage_change = ((total_amount_last_day - total_amount_day_before) / total_amount_day_before) * 100

    sales_data_last_day = OrderDetails.objects.filter(created_at__date=start_date.date()).values('created_at__hour').annotate(total_sales=Sum('amount')).order_by('created_at__hour')

    # Query to get revenue data for the last day
    revenue_data_last_day = OrderDetails.objects.filter(created_at__date=start_date.date()).values('created_at__hour').annotate(total_revenue=Sum('payment__amount')).order_by('created_at__hour')

    # Query to get customer count data for the last day
    customer_count_data_last_day = User.objects.filter(orderdetails__created_at__date=start_date.date()).values('orderdetails__created_at__hour').annotate(customer_count=Count('id')).order_by('orderdetails__created_at__hour')

    # Format the data for JavaScript
    formatted_sales_data = [{'x': entry['created_at__hour'], 'y': entry['total_sales']} for entry in sales_data_last_day]
    formatted_revenue_data = [{'x': entry['created_at__hour'], 'y': entry['total_revenue']} for entry in revenue_data_last_day]
    formatted_customer_count_data = [{'x': entry['orderdetails__created_at__hour'], 'y': entry['customer_count']} for entry in customer_count_data_last_day]

    context = {
        'last_day_count': last_day_count,
        'percentage_change': count_percentage_change,
        'total_amount_last_day': total_amount_last_day,
        'amount_percentage_change': amount_percentage_change,
        'user_count_last_day': user_count_last_day,
        'user_percentage_change': user_percentage_change,
        'formatted_sales_data': formatted_sales_data,
        'formatted_revenue_data': formatted_revenue_data,
        'formatted_customer_count_data': formatted_customer_count_data,
    }

    return render(request, 'adminindex.html', context)

def get_filtered_data(request):
    """
    Retrieves filtered data based on the filter type provided in the request.
    Accepts GET requests with a 'filter_type' parameter ('today', 'this-month', 'this-year').
    Calculates statistics such as counts and percentage changes for the specified time range.
    
    Parameters:
        request (HttpRequest): The HTTP request object containing the filter type.
        
    Returns:
        JsonResponse: JSON response containing the filtered data or an error message.
    """

    filter_type = request.GET.get('filter_type', None)

    end_date = timezone.now()

    if filter_type == 'today':
       
        start_date = end_date 
        last_day_count = OrderDetails.objects.filter(created_at__date=start_date.date()).count()

        day_before_start_date = start_date - timedelta(days=1)
        day_before_count = OrderDetails.objects.filter(created_at__date=day_before_start_date.date()).count()

        if day_before_count == 0:
            percentage_change = 0
        else:
            percentage_change = ((last_day_count - day_before_count) / day_before_count) * 100
            
   
        response_data = {
            'result': 'success',
            'filtered_data': {
                'count': last_day_count,
                'percentage_change': percentage_change,
            },
        }
    elif filter_type == 'this-month':

        start_date_month = end_date - timedelta(days=end_date.day )
        last_month_count = OrderDetails.objects.filter(created_at__date__range=(start_date_month.date(), end_date.date())).count()

        start_date_last_month = start_date_month - timedelta(days=start_date_month.day)
        last_month_before_count = OrderDetails.objects.filter(created_at__date__range=(start_date_last_month.date(), start_date_month.date() - timedelta(days=1))).count()

        if last_month_before_count == 0:
            percentage_change_month = 0
        else:
            percentage_change_month = ((last_month_count - last_month_before_count) / last_month_before_count) * 100
            

      
        response_data = {
            'result': 'success',
            'filtered_data': {
                'count': last_month_count,
                'percentage_change': percentage_change_month,
            },
        }
        
      
    elif filter_type == 'this-year':
        start_date_year = end_date - timedelta(days=end_date.timetuple().tm_yday)
        last_year_count = OrderDetails.objects.filter(created_at__date__range=(start_date_year.date(), end_date.date())).count()

        start_date_last_year = start_date_year - timedelta(days=start_date_year.timetuple().tm_yday)
        last_year_before_count = OrderDetails.objects.filter(created_at__date__range=(start_date_last_year.date(), start_date_year.date() - timedelta(days=1))).count()

        if last_year_before_count == 0:
            percentage_change_year = 0
        else:
            percentage_change_year = ((last_year_count - last_year_before_count) / last_year_before_count) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'count': last_year_count,
                'percentage_change': percentage_change_year,
            },
        }
    else:
        response_data = {
            'result': 'error',
            'message': 'Invalid filter_type',
        }

    return JsonResponse(response_data)

def get_filtered_data_amount(request):
    """
    Retrieves filtered data related to amounts based on the filter type provided in the request.
    Accepts GET requests with a 'filter_type' parameter ('Today', 'This Month', 'This Year').
    Calculates total amount and percentage change for the specified time range.
    
    Parameters:
        request (HttpRequest): The HTTP request object containing the filter type.
        
    Returns:
        JsonResponse: JSON response containing the filtered amount and its percentage change or an error message.
    """

    filter_type = request.GET.get('filter_type', None)
    end_date = timezone.now()
   

    if filter_type == 'Today':
        start_date = end_date 
        last_day_amount = OrderDetails.objects.filter(created_at__date=start_date.date()).aggregate(Sum('amount'))['amount__sum'] or 0

        day_before_start_date = start_date - timedelta(days=1)
        day_before_amount = OrderDetails.objects.filter(created_at__date=day_before_start_date.date()).aggregate(Sum('amount'))['amount__sum'] or 0

        if day_before_amount == 0:
            amount_percentage_change = 0
        else:
            amount_percentage_change = ((last_day_amount - day_before_amount) / day_before_amount) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'amount': last_day_amount,
                'percentage_change': amount_percentage_change,
            },
        }
    elif filter_type == 'This Month':
        start_date_month = end_date - timedelta(days=end_date.day )
        last_month_amount = OrderDetails.objects.filter(created_at__date__range=(start_date_month.date(), end_date.date())).aggregate(Sum('amount'))['amount__sum'] or 0

        start_date_last_month = start_date_month - timedelta(days=start_date_month.day)
        last_month_before_amount = OrderDetails.objects.filter(created_at__date__range=(start_date_last_month.date(), start_date_month.date() - timedelta(days=1))).aggregate(Sum('amount'))['amount__sum'] or 0

        if last_month_before_amount == 0:
            amount_percentage_change_month = 0
        else:
            amount_percentage_change_month = ((last_month_amount - last_month_before_amount) / last_month_before_amount) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'amount': last_month_amount,
                'percentage_change': amount_percentage_change_month,
            },
        }
    elif filter_type == 'This Year':
        start_date_year = end_date - timedelta(days=end_date.timetuple().tm_yday )
        last_year_amount = OrderDetails.objects.filter(created_at__date__range=(start_date_year.date(), end_date.date())).aggregate(Sum('amount'))['amount__sum'] or 0

        start_date_last_year = start_date_year - timedelta(days=start_date_year.timetuple().tm_yday)
        last_year_before_amount = OrderDetails.objects.filter(created_at__date__range=(start_date_last_year.date(), start_date_year.date() - timedelta(days=1))).aggregate(Sum('amount'))['amount__sum'] or 0

        if last_year_before_amount == 0:
            amount_percentage_change_year = 0
        else:
            amount_percentage_change_year = ((last_year_amount - last_year_before_amount) / last_year_before_amount) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'amount': last_year_amount,
                'percentage_change': amount_percentage_change_year,
            },
        }
    else:
        response_data = {
            'result': 'error',
            'message': 'Invalid filter_type',
        }

    return JsonResponse(response_data)



def get_filtered_data_user(request):
    """
    Retrieves filtered data related to user counts based on the filter type provided in the request.
    Accepts GET requests with a 'filter_type' parameter ('Today', 'This Month', 'This Year').
    Calculates user count and percentage change for the specified time range.
    
    Parameters:
        request (HttpRequest): The HTTP request object containing the filter type.
        
    Returns:
        JsonResponse: JSON response containing the filtered user count and its percentage change or an error message.
    """
 
    filter_type = request.GET.get('filter_type', None)
    end_date = timezone.now()
  

    if filter_type == 'Today':
        start_date = end_date 
        last_day_user_count = User.objects.filter(orderdetails__created_at__date=start_date.date()).annotate(order_count=Count('orderdetails')).count()

        day_before_start_date = start_date - timedelta(days=1)
        day_before_user_count = User.objects.filter(orderdetails__created_at__date=day_before_start_date.date()).annotate(order_count=Count('orderdetails')).count()

        if day_before_user_count == 0:
            user_percentage_change = 0
        else:
            user_percentage_change = ((last_day_user_count - day_before_user_count) / day_before_user_count) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'user_count': last_day_user_count,
                'percentage_change': user_percentage_change,
            },
        }
    elif filter_type == 'This Month':
        start_date_month = end_date - timedelta(days=end_date.day )
        last_month_user_count = User.objects.filter(orderdetails__created_at__date__range=(start_date_month.date(), end_date.date())).annotate(order_count=Count('orderdetails')).count()

        start_date_last_month = start_date_month - timedelta(days=start_date_month.day)
        last_month_before_user_count = User.objects.filter(orderdetails__created_at__date__range=(start_date_last_month.date(), start_date_month.date() - timedelta(days=1))).annotate(order_count=Count('orderdetails')).count()

        if last_month_before_user_count == 0:
            user_percentage_change_month = 0
        else:
            user_percentage_change_month = ((last_month_user_count - last_month_before_user_count) / last_month_before_user_count) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'user_count': last_month_user_count,
                'percentage_change': user_percentage_change_month,
            },
        }
    elif filter_type == 'This Year':
        start_date_year = end_date - timedelta(days=end_date.timetuple().tm_yday )
        last_year_user_count = User.objects.filter(orderdetails__created_at__date__range=(start_date_year.date(), end_date.date())).annotate(order_count=Count('orderdetails')).count()

        start_date_last_year = start_date_year - timedelta(days=start_date_year.timetuple().tm_yday)
        last_year_before_user_count = User.objects.filter(orderdetails__created_at__date__range=(start_date_last_year.date(), start_date_year.date() - timedelta(days=1))).annotate(order_count=Count('orderdetails')).count()

        if last_year_before_user_count == 0:
            user_percentage_change_year = 0
        else:
            user_percentage_change_year = ((last_year_user_count - last_year_before_user_count) / last_year_before_user_count) * 100

        response_data = {
            'result': 'success',
            'filtered_data': {
                'user_count': last_year_user_count,
                'percentage_change': user_percentage_change_year,
            },
        }
    else:
        response_data = {
            'result': 'error',
            'message': 'Invalid filter_type',
        }

    return JsonResponse(response_data)

def round_to_nearest_4_hours(dt):
    """
    Rounds a given datetime object to the nearest multiple of 4 hours.
    
    Parameters:
        dt (datetime.datetime): The datetime object to be rounded.
        
    Returns:
        datetime.datetime: The rounded datetime object.
    """
    return dt.replace(hour=(dt.hour // 4) * 4, minute=0, second=0, microsecond=0)

def chart_data(request, time_range):
    """
    Generates data for a chart based on the specified time range.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        time_range (str): The time range for which data is requested ('today', 'this_month', 'this_year').
        
    Returns:
        JsonResponse: JSON response containing the chart data.
    """
    end_date = timezone.now()

    if time_range == 'today':
        start_date = end_date - timedelta(days=1)
        trunc_function = TruncHour('created_at')

    elif time_range == 'this_month':
        start_date = end_date - timedelta(days=30)  # Adjust as needed
        trunc_function = TruncDay('created_at')

    elif time_range == 'this_year':
        start_date = end_date - timedelta(days=365)  # Adjust as needed
        trunc_function = TruncMonth('created_at')

    else:
        return JsonResponse({'error': 'Invalid time range'}, status=400)

    data = (
        OrderDetails.objects
        .filter(created_at__range=(start_date, end_date))
        .annotate(rounded_date=trunc_function)
        .values('rounded_date')
        .annotate(total_amount=Sum('amount'))
        .order_by('rounded_date')
    )

    # Adjust the rounded_date values based on the selected time range
    for entry in data:
        entry['rounded_date'] = round_to_nearest_4_hours(entry['rounded_date'])

    return JsonResponse(list(data), safe=False)




def admin_user(request):
    """
    Displays user information to an admin user.
    Redirects to the admin login page if the user is not logged in as an admin.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Rendered admin user template with user information.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    
    userinfo = User.objects.filter(adminstatus='user')
    
    context = {
        'userinfo': userinfo,
    }
    
    return render(request, 'admin_user.html', context)

def user_block(request, id):
    """
    Toggles the status of a user between "active" and "block".

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the user whose status is being toggled.

    Returns:
        HttpResponseRedirect: Redirects to the admin user page after the status update.
    """
    userinfo = get_object_or_404(User, id=id)

    if userinfo.status == 'active':
        userinfo.status = 'block'
    elif userinfo.status == 'block':
        userinfo.status = 'active'
    
    userinfo.save()  

    return redirect('admin_user')

def user_search(request):
    """
    Handles search queries for users in the admin interface.
    
    If the user is logged in as an admin, performs a case-insensitive search
    for users whose usernames contain the query string provided in the request.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Rendered admin user template with search results.
    """
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = User.objects.filter(username__icontains = query)
        context = {'userinfo':allPosts}
        return render(request, 'admin_user.html', context)
   

def admin_product(request):
    """
    Renders the admin product page with product information, categories, inventory, and parent variants.
    Redirects to the admin login page if the user is not logged in as an admin.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Rendered admin product template with product data.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 

    prodinfo = Product.objects.all()
    catinfo = ProductCategory.objects.all()
    invntinfo = ProductInventory.objects.all()

    # Retrieving ProductParentVariant instances
    parent_variants = ProductParentVariant.objects.all()

    # Pagination for Product instances
    paginator = Paginator(prodinfo, 10)  # Show 10 products per page
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'catinfo': catinfo,
        'invntinfo': invntinfo,
        'parent_variants': parent_variants,
    }

    return render(request, 'admin_product.html', context)
@csrf_exempt
def edit_main_image(request, product_id):
    """
    Handles the editing of the main image associated with a product.
    
    Accepts POST requests with base64-encoded image data.
    Decodes the image data, creates a file object, and saves it to the 'product_images' directory.
    Updates the main_image field of the product with the path of the newly saved image file.
    
    Parameters:
        request (HttpRequest): The HTTP request object.
        product_id (int): The ID of the product whose main image is being edited.
        
    Returns:
        JsonResponse: JSON response indicating success or error.
    """
    
    if request.method == 'POST':
       
        product = get_object_or_404(Product, id=product_id)

      
        cropped_image_data = request.POST.get('image_data', '')

        img_str = cropped_image_data.split(';base64,')[1]

        
        img_data = base64.b64decode(img_str)

      
        img_file = ContentFile(img_data, name=f'{product.id}_main_image.jpg')

     
        path = default_storage.save(f'product_images/{product.id}_main_image.jpg', img_file)

      
        product.main_image = path
        product.save()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request method'})


def get_child_variant_sizes(request):
    """
    Handles AJAX requests to retrieve child variant sizes based on a parent variant ID.
    
    Expects a GET request with a 'parent_variant_id' parameter representing the ID of the parent variant.
    Queries the ProductChildVariantInventory model to filter child variant sizes based on the provided parent variant ID.
    Formats the retrieved IDs and sizes into a list of dictionaries.
    Returns a JSON response containing the list of child variant sizes.
    
    Parameters:
        request (HttpRequest): The HTTP request object containing the parent variant ID.
        
    Returns:
        JsonResponse: JSON response containing the list of child variant sizes.
    """
    parent_variant_id = request.GET.get('parent_variant_id')
 

    sizes = ProductChildVariantInventory.objects.filter(parent_variant_id=parent_variant_id).values('id', 'size')

    return JsonResponse(list(sizes), safe=False)


def add_product(request):
    """
    Handles the addition of a new product.

    If the request method is POST, extracts product data from the request and performs validation.
    Creates a new Product instance with the extracted data and associated ProductParentVariant.
    Handles the addition of additional images for the product variant color.
    Adds success or error messages to the Django messages framework based on the outcome.
    Redirects to the admin product page after completion.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the admin product page.
    """
    if request.method == 'POST':
        name = request.POST['name']
        desc = request.POST['desc']
        color = request.POST['color']
        category_id = request.POST['category_id']
        inventory_id = request.POST['inventory_id'] 
        status = request.POST.get('inlineRadioOptionsStatus', 'active')
        has_variants = request.POST.get('variantinlineRadioOptionsStatus', False)
        default_value =request.POST.get('inlineRadioOptionsDefault') 
        parent_inv_id = request.POST.get('parent_inv_id')
       
        fields = [
            (name, 'Name'),
            (desc,'Description'),
            (color,'color'),

            
            
            
            
        ]

        for field, field_name in fields:
    
                error_message = validator(field, field_name)
        
                if error_message:
              
                    messages.error(request, error_message)
                    return redirect('admin_product') 
        product = Product.objects.create(
            name=name,
            description=desc,
           
            category_id=category_id,
            inventory_id=inventory_id,
            status = status,
            has_variants=has_variants,
            
        )

        # Create ProductParentVariant
        
    color = request.POST.get('color', None)
    main_image = request.FILES.get('image1', None)

    if color and main_image:
        inventory_parent = ProductParentVariantInventory.objects.get(id= parent_inv_id)

    product_parent_variant = ProductParentVariant.objects.create(
        product=product,
        inventory_parent=inventory_parent,
        color=color,
        main_image=main_image,
        
                )
    p_variant = get_object_or_404(ProductParentVariant, inventory_parent = inventory_parent)
            
    if default_value:        
        p_variant.default = default_value
        p_variant.save()

                # Create ProductVariantColorImages
    for i in range(2, 5):
       
        image_field_name = f'image{i}'
        image = request.FILES.get(image_field_name, None)
      

        if image:
            ProductVariantColorImages.objects.create(
                parent_variant=product_parent_variant,
                image=image
                        )

    messages.success(request, 'Product added successfully.')
    return redirect('admin_product')

    # Render the form on GET request
    catinfo = ProductCategory.objects.all()
    invntinfo = ProductInventory.objects.all()

    context = {
        'catinfo': catinfo,
        'invntinfo': invntinfo,
    }

    return render(request, 'add_product.html', context)
    

def validator(field, field_name):
    """
    Performs basic validation on a field value to ensure it is not empty or containing only spaces.

    Parameters:
        field (str): The value of the field to be validated.
        field_name (str): The name of the field, used in the error message.

    Returns:
        str or False: An error message if validation fails, otherwise False.
    """
    if not field.strip():

        return f'{field_name} cannot be empty or contain only spaces.'
    return False 


def search_product(request):
        """
    Handles product search based on a query string.

    Extracts the search query from the request and filters products based on the query.
    Retrieves associated category and inventory information for the filtered products.
    Sets up pagination for the filtered products and creates a context for rendering.
    Renders the admin product template with the search results.

    Parameters:
        request (HttpRequest): The HTTP request object containing the search query.

    Returns:
        HttpResponse: Rendered admin product template with search results.
    """
    # if 'admin' in request.session:
        query = request.GET['query']
        prodinfo = Product.objects.filter(name__icontains = query)
        
        cat_ids = ProductCategory.objects.filter(product__in=prodinfo).values_list('id', flat=True)
        invnt_ids = ProductInventory.objects.filter(product__in=prodinfo).values_list('id', flat=True)

        catinfo = ProductCategory.objects.filter(id__in=cat_ids)
        invntinfo = ProductInventory.objects.filter(id__in=invnt_ids)

        # Pagination
        paginator = Paginator(prodinfo, 10)  # Show 10 products per page
        page = request.GET.get('page')

        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        context = {
            'products': products,
            'catinfo': catinfo,
            'invntinfo': invntinfo,
        }

        return render(request, 'admin_product.html', context)

        context = {'catinfo':allPosts}
        return render(request, 'admin_product.html', context)
    
    



def edit_product(request,id):
    """
    Handles the editing of product details based on the provided ID.

    If the request method is POST, extracts product data from the request and performs validation.
    Retrieves the product object based on the provided ID and updates its fields if changes are detected.
    Saves the modified product object.
    Redirects to the admin product page after the product is successfully updated.

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the product to be edited.

    Returns:
        HttpResponseRedirect: Redirects to the admin product page.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
    if request.method == "POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        
        category_id = request.POST.get('category_id')
        discount_id = request.POST.get('discount_id')
        inventory_id = request.POST.get('inventory_id')
        status = request.POST.get('inlineRadioOptionsStatus')
      
    
        fields = [
            (name, 'Product name'),
            (desc, 'Product description'),
          
            
        ]

           
        for field, field_name in fields:
          
            error_message = validator(field, field_name)
       
            if error_message:
             
                messages.error(request, error_message)
                return redirect('admin_product')


    prod = Product.objects.get(id=id)

    if not name.strip():
     
        messages.error(request, 'This is wrong')
        return redirect('admin_product')
    if name is not None and prod.name != name:
        prod.name = name

    if desc is not None and prod.description != desc:
        prod.description = desc


    if category_id is not None and prod.category_id != category_id:
        prod.category = category_id
    
    if discount_id is not None and prod.discount_id != discount_id:
        prod.discount = discount_id
    
    if inventory_id is not None and prod.inventory_id != inventory_id:
        prod.inventory = inventory_id
   

    if status is not None and prod.status != status:
        prod.status = status


    
    prod.save()
            
        
    return redirect('admin_product')



@csrf_exempt
def edit_image(request, product_id, image_id):
    """
    Handles the editing of a product image associated with a specific product.

    This view function expects a POST request containing base64-encoded image data 
    in the 'image_data' parameter. It decodes the image data, saves it as a new image file,
    and updates the image field of the corresponding product image object.

    Parameters:
        request (HttpRequest): The HTTP request object.
        product_id (int): The ID of the product associated with the image.
        image_id (int): The ID of the product image to be edited.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of the operation.
            - {'success': True} if the image editing process is successful.
            - {'error': 'Invalid request method'} if the request method is not POST.
    """
    if request.method == 'POST':
       
        product = get_object_or_404(Product, id=product_id)

      
        image = get_object_or_404(ProductImage, id=image_id, product=product)

    
        cropped_image_data = request.POST.get('image_data', '')

        img_str = cropped_image_data.split(';base64,')[1]

      
        img_data = base64.b64decode(img_str)

     
        img_file = ContentFile(img_data, name=f'{product.id}_image{image.id}.jpg')


        path = default_storage.save(f'product_images/{product.id}_image{image.id}.jpg', img_file)

      
        image.image = path
        image.save()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request method'})


def product_inactive(request,id):
    """
    Sets a product's status to 'inactive'.

    This view function expects a product ID as a parameter and updates the status of the corresponding product to 'inactive'.
    It then redirects to the admin product page.

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the product to be set as inactive.

    Returns:
        HttpResponseRedirect: Redirects to the admin product page after updating the product status.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    prodinfo = Product.objects.filter(id=id)
    prodinfo.status = 'inactive'
    prodinfo.save()
    return redirect('admin_product')
        



def admin_category(request):
    """
    Renders the admin category page with information about product categories.

    This view function retrieves all product categories from the database and passes them to the template
    for rendering. If the user is not logged in as an admin, it redirects them to the admin login page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin category page with product category information.
        HttpResponseRedirect: Redirects to the admin login page if the user is not logged in as an admin.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
    catinfo = ProductCategory.objects.all()
    context = {
        'catinfo':catinfo,
    }
    return render(request, 'admin_category.html',context)



def add_category(request):
    """
    Handles the addition of a new product category.

    If the request method is POST, this view function attempts to create a new ProductCategory instance
    using the provided form data. If successful, it redirects to the admin category page with a success message.
    If unsuccessful, it redirects to the admin category page with an error message.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the admin category page after adding the category.
            - If the request method is POST and the category is successfully added.
            - If the request method is GET or if there are validation errors.
    """
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('desc')
        status = request.POST.get('inlineRadioOptionsStatus')

        # Validate input
        if not all([name.strip(), description.strip(), status.strip()]):
            messages.error(request, "Please fill in all the fields.")
            return redirect('admin_category')

        # Create the ProductCategory instance
        try:
            category = ProductCategory.objects.create(
                name=name.strip(),
                description=description.strip(),
                status=status.strip()
            )
            messages.success(request, "Category added successfully.")
            return redirect('admin_category')  # Redirect to the appropriate URL after adding the category
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('admin_category')

    # Handle GET request
    return redirect('admin_category')

def search_category(request):
    """
    Searches for product categories based on a query string.

    If the user is logged in as an admin, this view function retrieves product categories whose names contain
    the provided query string. It then renders the admin category page with the filtered category information.
    If the user is not logged in as an admin, it redirects to the admin login page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin category page with filtered category information if the user is logged in.
        HttpResponseRedirect: Redirects to the admin login page if the user is not logged in as an admin.
    """
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductCategory.objects.filter(name__icontains = query)
        context = {'catinfo':allPosts}
        return render(request, 'admin_category.html', context)
    else:
        return redirect('admin_login')

def edit_category(request,id):
    """
    Edits an existing product category.

    This view function allows an admin user to edit the details of an existing product category. If the user is not
    logged in as an admin, it redirects them to the login page. If the request method is POST, it retrieves the updated
    category information from the form data and validates it. If the provided name conflicts with an existing category,
    an error message is displayed. If the form data is valid and the category is successfully updated, it redirects to
    the admin category page with a success message. If the request method is GET, it redirects to the admin category
    page without performing any action.

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the product category to be edited.

    Returns:
        HttpResponseRedirect: Redirects to the admin category page after editing the category.
            - If the request method is POST and the category is successfully updated.
            - If the request method is GET.
        HttpResponseRedirect: Redirects to the login page if the user is not logged in as an admin.
    """
    if 'admin' not in request.session:
        return redirect('login') 
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('desc')
        status = request.POST.get('inlineRadioOptionsStatus')

    cat = ProductCategory.objects.get(id=id)

    fields = [
            (name, 'Category name'),
            (description, 'Category description'),
            
            
        ]

           
    for field, field_name in fields:
               
                error_message = validator(field, field_name)
             
                if error_message:
                  
                    messages.error(request, error_message)
                    return redirect('admin_category')

    if name is not None and name == cat.name :
            messages.error(request, 'Category with the same name already exists.')
            return redirect('admin_category')
    
    

    if name is not None and cat.name != name:
        cat.name = name

    if description is not None and cat.description != description:
        cat.description = description

   

    if status is not None and cat.status != status:
        cat.status = status


    
    cat.save()
            
       
    return redirect('admin_category')

def category_inactive(request,id):
    """
    Sets a product category as inactive.

    This view function allows an admin user to set a product category as inactive, thereby marking it as not currently
    available. If the user is not logged in as an admin, it redirects them to the admin login page. It retrieves the
    product category with the given ID and updates its status to 'inactive'. Upon successful update, it redirects to
    the admin category page with the updated category information.

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the product category to be marked as inactive.

    Returns:
        HttpResponseRedirect: Redirects to the admin category page after marking the category as inactive.
            - If the user is logged in as an admin and the category is successfully updated.
        HttpResponseRedirect: Redirects to the admin login page if the user is not logged in as an admin.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    catinfo = ProductCategory.objects.filter(id=id)
    catinfo.status = 'inactive'
    catinfo.save()
    return redirect('admin_category')



def admin_inventory(request):
    """
    Renders the admin inventory page.

    This view function retrieves all product inventory information from the database and renders the admin inventory
    page with the retrieved data. It retrieves all instances of ProductInventory model and passes them to the template
    for rendering.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin inventory page with the product inventory information.
    """
    
    invntinfo = ProductInventory.objects.all()
    context = {
        'invntinfo':invntinfo,
    }
    return render(request, 'admin_inventory.html',context)

def search_inventory(request):
    """
    Searches for product inventory based on the provided query.

    This view function handles the search for product inventory based on the query parameter provided in the GET
    request. If the user is logged in as an admin, it filters the ProductInventory instances based on the name
    containing the provided query string. It then renders the admin inventory page with the filtered inventory
    information. If the user is not logged in as an admin, it redirects to the admin login page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin inventory page with the filtered product inventory information.
            - If the user is logged in as an admin.
        HttpResponseRedirect: Redirects to the admin login page if the user is not logged in as an admin.
    """
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductInventory.objects.filter(name__icontains = query)
        context = {'invntinfo':allPosts}
        return render(request, 'admin_inventory.html',context)
    else:
        return redirect('admin_login')

def add_inventory(request):
    """
    Handles the addition of a new product inventory.

    This view function processes the form submission for adding a new product inventory. If the request method is
    POST, it retrieves the input data from the form and performs basic validation. If the input data is valid, it
    creates a new ProductInventory instance with the provided data and saves it to the database. Finally, it
    redirects the user to the admin inventory page with a success message. If the request method is GET, it redirects
    to the admin inventory page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the admin inventory page after adding the new product inventory.
            - If the request method is POST.
        HttpResponseRedirect: Redirects to the admin inventory page without making any changes if the request method is GET.
    """
    if request.method == "POST":
        name = request.POST.get('name')
        
       
        has_variants = request.POST.get('inlineRadioOptionsHasvariants')
  
       
       
        fields = [
            (name, 'Inventory name'),
            
            
            
            
        ]

           
        for field, field_name in fields:
            
                error_message = validator(field, field_name)
              
                if error_message:
                  
                    messages.error(request, error_message)
                    return redirect('admin_inventory')
        
        ProductInventory.objects.create(name = name, has_variants = has_variants)
                
       
        messages.success(request, "Succesfully Created")

        return redirect('admin_inventory')

def variant_inventory_display(request, id):
    """
    Renders the variant inventory display page.

    This view function retrieves the product inventory instance with the specified ID from the database and
    renders the admin variant inventory template to display information about the inventory and its parent variants.

    Parameters:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the product inventory.

    Returns:
        HttpResponse: Renders the admin variant inventory template with the inventory and its parent variants.
            - If the inventory with the specified ID exists.
        HttpResponseNotFound: Renders a 404 page if the inventory with the specified ID does not exist.
    """
    inventory = get_object_or_404(ProductInventory, id=id)  
    
    parent_variants = inventory.variants.all()
    
    return render(request, 'admin_variant_inventory.html', {'inventory': inventory, 'parent_variants': parent_variants})

def edit_parent_variant(request, variant_id):
    """
    Handles the editing of a parent variant.

    This view function retrieves the parent variant instance with the specified ID from the database and
    allows the admin to edit its color. Upon successful editing, the function redirects the admin back to the
    variant inventory display page.

    Parameters:
        request (HttpRequest): The HTTP request object.
        variant_id (int): The ID of the parent variant to be edited.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the variant inventory display page upon successful editing.
            - If the request method is POST and the editing is successful.
        HttpResponse: Redirects the admin back to the variant inventory display page if the request method is GET.
            - If the editing is unsuccessful or the variant with the specified ID does not exist.
    """
    variant = get_object_or_404(ProductParentVariantInventory, id=variant_id)
    inventory_id = variant.inventory_id
    
    if request.method == 'POST':
 
        color = request.POST.get('color')
        color = str(color)
        color = color.capitalize()
        
        variant.color = color
      
        variant.save()
       
       
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('variant_inventory_display', inventory_id)

def add_parent_variant(request):
    """
    Handles the addition of a new parent variant.

    This view function adds a new parent variant to the specified inventory. It retrieves the inventory ID and color
    of the new variant from the POST request. Upon successful addition, it redirects the admin back to the variant
    inventory display page.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the variant inventory display page upon successful addition.
            - If the request method is POST and the addition is successful.
        HttpResponse: Redirects the admin back to the variant inventory display page if the request method is GET.
            - If the addition is unsuccessful or the specified inventory does not exist.
    """
    if request.method == 'POST':
        
        inventory_id = request.POST.get('inventory_id')
        inventory = ProductInventory.objects.get(id=inventory_id)

       
        color = request.POST.get('color')
        color = color.capitalize()
       
        ProductParentVariantInventory.objects.create(inventory=inventory, color=color)
       
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('variant_inventory_display', inventory_id)
def edit_child_variant(request, child_variant_id):
    """
    Handles the editing of a child variant.

    This view function updates the details of a specific child variant based on the provided ID. It retrieves the
    child variant's details from the POST request and updates the corresponding fields in the database. Upon
    successful update, it redirects the admin back to the variant inventory display page.

    Args:
        request (HttpRequest): The HTTP request object.
        child_variant_id (int): The ID of the child variant to be edited.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the variant inventory display page upon successful editing.
            - If the request method is POST and the editing is successful.
        HttpResponse: Redirects the admin back to the variant inventory display page if the request method is GET.
            - If the editing is unsuccessful or the specified child variant does not exist.
    """
    child_variant = ProductChildVariantInventory.objects.get(id=child_variant_id)

    if request.method == 'POST':
        inventory_id = request.POST.get('inventory_id')
        child_variant.size = request.POST.get('size')
        child_variant.quantity = request.POST.get('quantity')
        child_variant.supplier_id = request.POST.get('supplier_id')
        child_variant.status = request.POST.get('status')
        # Update other fields as needed
        child_variant.save()

        # Redirect to the original page or another page
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('variant_inventory_display', inventory_id)

def add_child_variant(request):
    """
    Handles the addition of a child variant.

    This view function creates a new child variant associated with a parent variant. It retrieves the details of
    the new child variant from the POST request and creates a new entry in the database. Upon successful creation,
    it redirects the admin back to the variant inventory display page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the variant inventory display page upon successful addition
            of the child variant.
            - If the request method is POST and the addition is successful.
        HttpResponse: Redirects the admin back to the variant inventory display page if the request method is GET.
            - If the addition is unsuccessful.
    """
    if request.method == 'POST':
        
        parent_variant_id = request.POST.get('parent_variant_id')

        
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')
        supplier_id = request.POST.get('supplier_id')
        status = request.POST.get('status')
       
        ProductChildVariantInventory.objects.create(parent_variant_id=parent_variant_id, size=size, quantity=quantity, supplier_id=supplier_id, status=status)
        
        parent = ProductParentVariantInventory.objects.get(id = parent_variant_id)
        inventory_id = parent.inventory_id

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('variant_inventory_display', inventory_id)

def edit_inventory(request,inventory_id):
    """
    Handles the editing of inventory details.

    This view function allows an admin to edit the details of a specific inventory. It retrieves the inventory details
    from the POST request and updates the corresponding entry in the database. Upon successful update, it redirects the
    admin back to the admin inventory page.

    Args:
        request (HttpRequest): The HTTP request object.
        inventory_id (int): The ID of the inventory to be edited.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the admin inventory page upon successful update of inventory
            details.
            - If the request method is POST and the update is successful.
        HttpResponseRedirect: Redirects the admin back to the admin inventory page if the request method is POST but
            the update fails.
        HttpResponseRedirect: Redirects the admin back to the admin inventory page if the request method is not POST.
            - If the request method is not POST.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 
  
    id = inventory_id

    if request.method == "POST":
        name = request.POST.get('name')
        has_variants = request.POST.get('inlineRadioOptionsHasvariants')
      

        invnt = ProductInventory.objects.get(id=id)

        fields = [
            (name, 'Inventory name'),
            
            
            
        ]

           
        for field, field_name in fields:
      
                error_message = validator(field, field_name)
           
                if error_message:
              
                    messages.error(request, error_message)
                    return redirect('admin_inventory') 



        if name is not None and invnt.name != name:
            invnt.name = name





       

       

        
        if has_variants is not None and invnt.has_variants != has_variants:
            invnt.has_variants = has_variants

        invnt.save()

        messages.success(request, 'Inventory updated successfully.')
        return redirect('admin_inventory')
    
  
    messages.error(request, 'Invalid request.')
    return redirect('admin_inventory')






def inventory_inactive(request,id):
    """
    Handles setting an inventory as inactive.

    This view function allows an admin to set a specific inventory as inactive. It retrieves the inventory details based
    on the provided ID and updates its status to 'inactive'. Upon successful update, it redirects the admin back to the
    admin inventory page with a success message. If an error occurs during the process, it redirects the admin back to
    the admin inventory page with an error message.

    Args:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the inventory to be set as inactive.

    Returns:
        HttpResponseRedirect: Redirects the admin back to the admin inventory page upon successfully setting the
            inventory as inactive.
            - If the inventory status is updated successfully.
        HttpResponseRedirect: Redirects the admin back to the admin inventory page if an error occurs while setting
            the inventory as inactive.
            - If an error occurs during the process.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 

    

    invntinfo = get_object_or_404(ProductInventory, id=id)

    try:
        invntinfo.status = 'inactive'
        invntinfo.save()
        messages.success(request, 'Inventory set as inactive successfully.')
    except Exception as e:
        messages.error(request, f'Error setting inventory as inactive: {e}')

    return redirect('admin_inventory')


def admin_coupon(request):
    """
    Renders the admin coupon page.

    This view function retrieves all coupons from the database and renders them in the admin_coupon template. If the
    user is not logged in as an admin, it redirects them to the admin login page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin_coupon template with the coupons.
            - If the user is logged in as an admin.
        HttpResponseRedirect: Redirects the user to the admin login page if not logged in as an admin.
            - If the user is not logged in as an admin.
    """
    if 'admin' not in request.session:
        return redirect('admin_login') 

    coupons = Coupon.objects.all()
    # date = coupons.date
    # date.strftime("%d-%m-%y")

    context = {
        'coupons': coupons,
    }

    return render(request, 'admin_coupon.html', context)

def add_coupon(request):
    """
    Handles the addition of a new coupon.

    If the request method is POST, retrieves the coupon details from the request and attempts to create a new coupon.
    Validates the input fields and checks for duplicate coupon codes.
    Returns appropriate messages based on the success or failure of the operation.
    Redirects to the admin_coupon page after adding the coupon.

    Parameters:
        request (HttpRequest): The HTTP request object containing the form data.

    Returns:
        HttpResponseRedirect: Redirects to the admin_coupon page after adding the coupon.
        HttpResponse: Renders the add_coupon.html template for GET requests.
    """
    if request.method == "POST":
        code = request.POST.get('code')
        coupon_type = request.POST.get('coupon_type')
        coupon_value = request.POST.get('coupon_value')
        min_order = request.POST.get('min_order')
        max_user = request.POST.get('max_user')
        
        exp_date = request.POST.get('exp_date')
        fields = [
                (code, 'Coupon Code'),
                (coupon_value, 'Coupon Value'),
                (min_order, 'Min Order'),
                (max_user, 'Max. User'),
              
            
            
        ]

           
        for field, field_name in fields:
                  
                    error_message = validator(field, field_name)
                 
                    if error_message:
                     
                        messages.error(request, error_message)
                        return redirect('admin_inventory') 
                    

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
                    
                    exp_date=exp_date
             )
                coupon.full_clean()  # Validate model fields, including custom clean method
                coupon.save()
                
                messages.success(request, "Coupon successfully created")
            except ValidationError as e:
                messages.error(request, _(str(e.get('__all__', [])[0])))
                

        return redirect('admin_coupon')
    else:
        
        return render('admin_coupon')  

def edit_coupon(request,id):
    """
    Handles the editing of an existing coupon.

    If the request method is POST, retrieves the coupon details from the request and attempts to update the coupon.
    Validates the input fields.
    Returns appropriate messages based on the success or failure of the operation.
    Redirects to the admin_coupon page after editing the coupon.

    Parameters:
        request (HttpRequest): The HTTP request object containing the form data.
        id (int): The ID of the coupon to be edited.

    Returns:
        HttpResponseRedirect: Redirects to the admin_coupon page after editing the coupon.
        HttpResponse: Renders the admin_coupon page if the request method is not POST.
    """
    if request.method == "POST":
        code = request.POST.get('code')
        coupon_type = request.POST.get('coupon_type')
        coupon_value = request.POST.get('coupon_value')
        min_order = request.POST.get('min_order')
        max_user = request.POST.get('max_user')
        # count = request.POST.get('count')
        exp_date = request.POST.get('exp_date')

      
        fields = [
                (code, 'Coupon Code'),
                (coupon_value, 'Coupon Value'),
                (min_order, 'Min Order'),
                (max_user, 'Max. User'),
                # (count,'count')
            
            
        ]

           
        for field, field_name in fields:
                  
                    error_message = validator(field, field_name)
                
                    if error_message:
                    
                        messages.error(request, error_message)
                        return redirect('admin_inventory') 
                    

       

        try:
                coupon = Coupon.objects.get(id=id)
         
        
                coupon.code = code
                coupon.coupon_type = coupon_type
                coupon.coupon_value = coupon_value
                coupon.min_order = min_order
                coupon.max_user = max_user
                # coupon.count = count
                coupon.exp_date = exp_date

                coupon.full_clean()  
                coupon.save()
                messages.success(request, "Coupon successfully updated")
        except Coupon.DoesNotExist:
                messages.error(request, "Coupon does not exist")
        except ValidationError as e:
            messages.error(request, _(str(e.get('__all__', [])[0])))
          

        return redirect('admin_coupon')
    else:
      
        return render('admin_coupon')  
    


def admin_product_create(request):
    """
    Renders the admin product creation page with options to select product category and inventory.

    Retrieves all product categories and inventories from the database.
    Renders the admin_Product_create.html template with the retrieved data.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin_Product_create.html template with context data.
    """
    catinfo = ProductCategory.objects.all()
    invntinfo = ProductInventory.objects.all()
    context = {
        
        'catinfo': catinfo,
        'invntinfo': invntinfo,
    }

    return render(request, 'admin_Product_create.html', context)


def get_parent_variants(request):
    """
    Retrieves parent variants associated with a specific inventory.

    Retrieves the inventory ID from the GET parameters of the request.
    Queries the database for parent variants belonging to the specified inventory.
    Constructs a JSON response containing the IDs and colors of the parent variants.
    Returns a JSON response with the parent variant data or an error response if the request is invalid.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response containing parent variant data or an error message.
    """
    if request.method == 'GET' and 'inventory_id' in request.GET:
        inventory_id = request.GET['inventory_id']
        
        # Assuming you have a model for ProductParentVariantInventory
        parent_variants = ProductParentVariantInventory.objects.filter(inventory_id=inventory_id)
        
        # Return data as JSON
        data = [{'id': variant.id, 'color': variant.color} for variant in parent_variants]
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)



def view_product_variants(request,product_id):
    """
    Displays the variants associated with a product.

    Retrieves the product and its parent variants, child variants, color images, and inventory information.
    Constructs a context containing the product and its variant details.
    Renders the template for viewing product variants with the constructed context.

    Parameters:
        request (HttpRequest): The HTTP request object.
        product_id (int): The ID of the product.

    Returns:
        HttpResponse: A response containing the rendered template with variant details.
    """
    product = Product.objects.get(pk=product_id)
    parent_variants = ProductParentVariant.objects.filter(product=product)
    child_variants = ProductChildVariant.objects.filter(parent_variant__in=parent_variants)
    color_images = ProductVariantColorImages.objects.filter(parent_variant__in=parent_variants)
    product_parent_variant_inventory = ProductParentVariantInventory.objects.filter(inventory__id=product.inventory.id)
   

    context = {
        'product': product,
        'parent_variants': parent_variants,
        'child_variants': child_variants,
        'color_images': color_images,
        'product_parent_variant_inventory': product_parent_variant_inventory,
       
    }

    
     
    return render(request,'admin_product_variant_create.html',context)

def add_product_parent_variant(request):
    """
    Handles the addition of a parent variant associated with a product.

    Retrieves data from the request including color, parent inventory ID, main image,
    product ID, additional images, and default value.
    Checks for duplicate entries.
    Saves the parent variant data to the database.
    Creates associated color images.
    Redirects to view the product variants page after successful addition.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to view the product variants page.
    """
    if request.method == 'POST':
        
        color = request.POST.get('color')
        parent_inventory_id = request.POST.get('parent_inventory_id')
        main_image = request.FILES.get('main_image')
        product_id = request.POST.get('product_id')
        images = request.FILES.getlist('images')
        default_value = request.POST.get('inlineRadioOptionsDefault')
        

        

        # Check for duplicate entry
        existing_variant = ProductParentVariant.objects.filter(inventory_parent__id=parent_inventory_id, product_id = product_id)
        if existing_variant.exists():
            messages.error(request, 'Duplicate entry. This combination already exists.')
            return redirect('view_product_variants', product_id)

        # Save data to the database
        product_parent_variant = ProductParentVariant.objects.create(
            color=color,
            main_image=main_image,
            product_id = product_id,
            inventory_parent_id = parent_inventory_id,
            default = default_value
            # Add other fields as needed
        )

        product_parent_variant.save()
       

        for image in images:
            ProductVariantColorImages.objects.create(parent_variant=product_parent_variant, image=image)

        

        messages.success(request, 'Product parent variant added successfully.')
        return redirect('view_product_variants', product_id)
    


def edit_product_parent_variant(request):
        """
    Handles the editing of a parent variant associated with a product.

    Retrieves data from the request including color, parent inventory ID,
    product ID, and default value.
    Retrieves the product parent variant based on the provided variant ID.
    Updates the parent variant data in the database.
    Redirects to view the product variants page after successful editing.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to view the product variants page.
    """
        color = request.POST.get('color')
        parent_inventory_id = request.POST.get('parent_inventory_id')
        # main_image = request.FILES.get('main_image')
        product_id = request.POST.get('product_id')
        # images = request.FILES.getlist('images')
        default_value = request.POST.get('inlineRadioOptionsDefault')
        product_variant_id = request.POST.get('pv_id')
      
        

        

        
        # Save data to the database
        product_parent_variant = ProductParentVariant.objects.get(id=product_variant_id)
        product_parent_variant.color = color
        # product_parent_variant.main_image = main_image
        product_parent_variant.product_id = product_id
        product_parent_variant.inventory_parent_id = parent_inventory_id
        product_parent_variant.default = default_value
        # Set other fields as needed

        product_parent_variant.save()
       

        
        

        messages.success(request, 'Product parent variant added successfully.')
        return redirect('view_product_variants', product_id)
     


def add_product_child_variant(request):
    """
    Handles the creation of a child variant associated with a parent variant.

    Retrieves data from the request including size, price, parent variant ID,
    and inventory child ID.
    Validates the provided data and creates a new child variant in the database.
    Redirects to view the product variants page after successful creation.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to view the product variants page.
    """
    if request.method == 'POST':
        try:
            inventory_child_id = request.POST.get('size')
            price = request.POST.get('price')
            product_parent_id = request.POST.get('parent_variant_id')
            prod_parent = get_object_or_404(ProductParentVariant, id=product_parent_id)

            product_id = prod_parent.product_id
            fields = [
            (price, 'Price'),
            
            
            
            
        ]

            for field, field_name in fields:
            
                error_message = validator(field, field_name)
             
                if error_message:
                    
                    messages.error(request, error_message)
                    return redirect('view_product_variants', product_id)  

           
            inventory_child_id = int(inventory_child_id)
            product_parent_id = int(product_parent_id)

            price = Decimal(price)
            inv_child = get_object_or_404(ProductChildVariantInventory, id=inventory_child_id)
            
            

            
            product_child = ProductChildVariant.objects.create(
                
                price=price,
                parent_variant_id=product_parent_id,
                inventory_child=inv_child
            )

         
            product_child.save()

          
            messages.success(request, 'Child variant added successfully.')

            
            return redirect('view_product_variants', product_id)

        except (ValueError, DecimalException):
           
            messages.error(request, 'Invalid IDs provided. Please provide valid integers.')

 
    messages.error(request, 'Invalid request method.')
    return redirect('view_product_variants', product_id)  


def edit_product_child_variant(request, child_variant_id):
    """
    View function for editing a child variant of a product.

    This view handles the POST request to update the price of a child variant.
    It retrieves the child variant instance based on the provided ID, validates
    the price field, and updates the price if valid.

    Parameters:
    - request: HttpRequest object representing the request from the client.
    - child_variant_id: The ID of the child variant to be edited.

    Returns:
    - HttpResponseRedirect: Redirects the user to the product variants view after
                             updating the child variant.
    """
    child_variant = get_object_or_404(ProductChildVariant, id=child_variant_id)
    product_parent = child_variant.parent_variant
    product_id = product_parent.product.id

    if request.method == 'POST':
        price = request.POST.get('price')

        fields = [
            (price, 'Price'),
            
            
            
            
        ]

        for field, field_name in fields:
               
                error_message = validator(field, field_name)
             
                if error_message:
                 
                    messages.error(request, error_message)
                    return redirect('view_product_variants', product_id)  


        price = Decimal(price)
        
        if not price:
            messages.error(request, 'Price is required.')
            return redirect('view_product_variants', product_id)
        
        child_variant.price = price
        child_variant.save()

        messages.success(request, 'Child variant updated successfully.')
        return redirect('view_product_variants', product_id)

    messages.error(request, 'Invalid request method.')
    return redirect('view_product_variants', product_id) 


   

def variant_edit_image(request,variant_id,image_id):
    """
    View function for editing an image associated with a product variant.

    This view handles the POST request containing the edited image data. It decodes
    the base64-encoded image data, saves it as a new image file, and updates the
    corresponding image record in the database.

    Parameters:
    - request: HttpRequest object representing the request from the client.
    - variant_id: The ID of the product variant.
    - image_id: The ID of the image to be edited.

    Returns:
    - JsonResponse: JSON response indicating the success or failure of the operation.
                    If successful, returns {'success': True}. Otherwise, returns
                    {'error': 'Error message'}.
    """
    if request.method == 'POST':
       
        product = get_object_or_404(ProductParentVariant, id=variant_id)

      
        image = get_object_or_404(ProductVariantColorImages, id=image_id, parent_variant_id=product)

    
        cropped_image_data = request.POST.get('image_data', '')

        img_str = cropped_image_data.split(';base64,')[1]

      
        img_data = base64.b64decode(img_str)

     
        img_file = ContentFile(img_data, name=f'{product.id}_image{image.id}.jpg')


        path = default_storage.save(f'variant_product_images/{product.id}_image{image.id}.jpg', img_file)

      
        image.image = path
        image.save()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request method'})


def admin_order_history(request):
    """
    View function for displaying the admin order history page.

    This view retrieves order items from the database and sorts them based on
    multiple fields: modified_at, status, and refund. The sorting order is
    descending for modified_at and status, and ascending for refund, with
    nulls appropriately handled.

    The sorted order items are paginated using Django's Paginator class with
    a default of 10 items per page. The current page number is retrieved from
    the request's GET parameters.

    Parameters:
    - request: HttpRequest object representing the request from the client.

    Returns:
    - HttpResponse: Rendered template containing the paginated order items.

    """
    items_per_page = 10

    # Assuming modified_at is the field representing the last modified date
    order_items = OrderItems.objects.order_by(
        F('modified_at').desc(nulls_last=True),
        F('status').desc(nulls_last=True),
        F('refund').desc(nulls_first=True)
    )

    paginator = Paginator(order_items, items_per_page)

    page = request.GET.get('page')
    try:
        order_items = paginator.page(page)
    except PageNotAnInteger:
        order_items = paginator.page(1)
    except EmptyPage:
        order_items = paginator.page(paginator.num_pages)

    context = {
        'order_items': order_items,
    }

    return render(request, 'admin_order_history.html', context)





def get_user_totals(user):
    """
    Calculates the total referral and joining rewards for a given user.

    Args:
        user (User): User object for which rewards are calculated.

    Returns:
        Tuple: A tuple containing the user object, total referral rewards, and total joining rewards.
    """
    referral_rewards_total = ReferralCodeHistory.objects.filter(user=user).aggregate(Sum('referral_rewards'))['referral_rewards__sum'] or 0
    joining_rewards_total = ReferralCodeHistory.objects.filter(new_user=user).aggregate(Sum('joining_rewards'))['joining_rewards__sum'] or 0

    return {
        'user': user,
        'referral_rewards_total': referral_rewards_total,
        'joining_rewards_total': joining_rewards_total,
    }





def get_user_totals(user):
    """
    Calculates the total referral and joining rewards for a given user.

    Args:
        user (User): User object for which rewards are calculated.

    Returns:
        Tuple: A tuple containing the total referral rewards and total joining rewards for the user.
    """
    if user.username == 'admin':
        return 0, 0  

    referral_rewards_total = ReferralCodeHistory.objects.filter(user=user).aggregate(Sum('referral_rewards'))['referral_rewards__sum'] or 0
    joining_rewards_total = ReferralCodeHistory.objects.filter(new_user=user).aggregate(Sum('joining_rewards'))['joining_rewards__sum'] or 0

    return referral_rewards_total, joining_rewards_total

def plot_referral_rewards(users):
    """
    Plots the referral rewards graph.

    Args:
        users (QuerySet): QuerySet containing User objects.

    Returns:
        str: Base64-encoded image HTML tag.
    """
    fig, ax = plt.subplots()
    width = 0.35
    x = range(len(users))
    referral_rewards_totals = []
    joining_rewards_totals = []

    for user in users:
        referral_rewards_total, joining_rewards_total = get_user_totals(user)
        referral_rewards_totals.append(referral_rewards_total)
        joining_rewards_totals.append(joining_rewards_total)

    ax.bar(x, referral_rewards_totals, width, label='Referral Rewards')
    ax.bar([i + width for i in x], joining_rewards_totals, width, label='Joining Rewards')

    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels([user.username for user in users])
    ax.legend()

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    image_base64 = base64.b64encode(image_stream.read()).decode('utf-8')

   
    graph_html = f'<img src="data:image/png;base64,{image_base64}" alt="Referral Rewards Plot" class="img-fluid">'

    return graph_html

def plot_daily_rewards():
    """
    Plots the daily rewards graph.

    Retrieves daily referral and joining rewards from the ReferralCodeHistory model.
    Creates a line plot showing cumulative referral and joining rewards over time.
    Saves the plot as a PNG image and converts it to base64 format.
    Returns the base64-encoded image HTML tag.

    Returns:
        str: Base64-encoded image HTML tag.
    """
    daily_rewards = ReferralCodeHistory.objects.values('created_at__date').annotate(
        daily_referral_rewards=Sum('referral_rewards'),
        daily_joining_rewards=Sum('joining_rewards')
    )

    dates = [entry['created_at__date'] for entry in daily_rewards]
    cumulative_referral_rewards = [entry['daily_referral_rewards'] for entry in daily_rewards]
    cumulative_joining_rewards = [entry['daily_joining_rewards'] for entry in daily_rewards]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(dates, cumulative_referral_rewards, label='Cumulative Referral Rewards', marker='o')
    ax.plot(dates, cumulative_joining_rewards, label='Cumulative Joining Rewards', marker='o')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Rewards')
    ax.legend()

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    image_base64 = base64.b64encode(image_stream.read()).decode('utf-8')

    return f'<img src="data:image/png;base64,{image_base64}" alt="Daily Rewards Plot" class="img-fluid">'



def referral_schemes_view(request):
    """
    Displays the referral reward schemes and referral history.

    Retrieves all referral reward schemes and calculates the overall referral and joining rewards totals.
    Paginates the referral history with 10 items per page.
    Calculates totals for each user excluding the 'admin' user.
    Generates plots for the referral rewards graph and the line graph for daily rewards.
    Renders the admin_referral.html template with the necessary context data.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin_referral.html template with the necessary context data.
    """
    try:
        referral_schemes = ReferralRewardSchemes.objects.all()
        overall_referral_rewards_total = ReferralCodeHistory.objects.aggregate(Sum('referral_rewards'))['referral_rewards__sum'] or 0
        overall_joining_rewards_total = ReferralCodeHistory.objects.aggregate(Sum('joining_rewards'))['joining_rewards__sum'] or 0
        total = overall_joining_rewards_total + overall_referral_rewards_total

        referral_history = ReferralCodeHistory.objects.all()

        page = request.GET.get('page', 1)
        paginator = Paginator(referral_history, 10)  # 10 items per page
        try:
            referral_history_page = paginator.page(page)
        except PageNotAnInteger:
            referral_history_page = paginator.page(1)
        except EmptyPage:
            referral_history_page = paginator.page(paginator.num_pages)

        # Calculate totals for each user excluding 'admin'
        users = User.objects.exclude(username='admin')  # Exclude the 'admin' user
        user_totals = [get_user_totals(user) for user in users]

        # Plot the referral rewards graph
        graph_html = plot_referral_rewards(users)

        # Plot the line graph for daily rewards
        daily_rewards_html = plot_daily_rewards()

        return render(request, 'admin_referral.html', {
            'referral_schemes': referral_schemes,
            'overall_referral_rewards_total': overall_referral_rewards_total,
            'overall_joining_rewards_total': overall_joining_rewards_total,
            'user_totals': user_totals,
            'total': total,
            'referral_history_page': referral_history_page,
            'graph_html': graph_html,
            'daily_rewards_html': daily_rewards_html,
        })
    except Exception as e:
        # Render the same page with an error message
        return render(request, 'admin_referral.html', {'error_message': str(e)})

def create_referral_reward_scheme(request):
    if request.method == 'POST':
        joining = request.POST.get('joining')
        referral = request.POST.get('referral')
        status = request.POST.get('status')
        
        
        referral_reward_scheme = ReferralRewardSchemes.objects.create(
            joining=joining,
            referral=referral,
            status=status
        )
        
        return redirect('referral_schemes_view')  # Redirect to success URL
    
    return redirect('referral_schemes_view')




def edit_referral(request):
    """
    Edits the referral reward scheme.

    If the request method is POST, retrieves the joining and referral values from the request.
    Retrieves the reward scheme object based on the provided ID.
    Validates the input and updates the joining and referral fields if provided.
    Saves the changes if at least one field is provided.
    Redirects the user to the referral_schemes_view page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects the user to the referral_schemes_view page.
    """
    if request.method == 'POST':
        joining = request.POST.get('joining')
        referral = request.POST.get('referral')
        reward_id = request.POST.get('reward_id')

        # Use get_object_or_404 to retrieve the specific object or return a 404 response if not found
        rewards = get_object_or_404(ReferralRewardSchemes, id=reward_id)

        # Validate input
        if joining is not None:
            rewards.joining = joining

        if referral is not None:
            rewards.referral = referral

        # Save the changes only if at least one field is provided
        if joining is not None or referral is not None:
            rewards.save()

    return redirect('referral_schemes_view')


def change_status(request):
    """
    Handles changing the status of an object.

    If the request method is POST, retrieves the object ID and new status from the request.
    Retrieves the object from the database based on the provided ID.
    Updates the status of the object to the new status.
    Redirects the user to the referral_schemes_view page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects the user to the referral_schemes_view page.
    """
    if request.method == 'POST':
        object_id = request.POST.get('object_id')
        new_status = request.POST.get('status')

        # Assuming you have a unique identifier for YourModel, such as an ID
        your_object = get_object_or_404(ReferralRewardSchemes, id=object_id)

        # Update the status
        your_object.status = new_status
        your_object.save()

    return redirect('referral_schemes_view') 


def admin_discount(request):
    """
    Renders the admin_discount.html template with active discounts.

    Retrieves all active discounts from the database.
    Passes the active discounts as context variables to the template.
    Renders the admin_discount.html template with the provided context.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin_discount.html template with active discounts.
    """
    # Retrieve all active discounts
    discounts = Discount.objects.filter(isactive=True)

    # Pass the discounts to the template
    context = {'discounts': discounts}
    return render(request, 'admin_discount.html', context)


def add_new_discount(request):
    """
    Renders the add_new_discount.html template with context data based on the selected discount location option.

    Retrieves the selected discount location option from the form submitted via POST request.
    Fetches data based on the selected option, such as product categories, products, parent variants,
    or child variants, and passes them as context variables to the template.
    Renders the add_new_discount.html template with the appropriate context.

    Parameters:
        request (HttpRequest): The HTTP request object containing form data.

    Returns:
        HttpResponse: Renders the add_new_discount.html template with context data.
    """
    selected_option = request.POST.get('discountLocation', 'category')  # Default to 'category'
    
    # Fetch data based on the selected option
    if selected_option == 'category':
        product_categories = ProductCategory.objects.all()
    elif selected_option == 'product':
        products = Product.objects.all()
        
    elif selected_option == 'parentVariant':
        parent_variants = ProductParentVariant.objects.all()
        
    elif selected_option == 'childVariant':
        child_variants = ProductChildVariant.objects.all()
        
   
    context = {
        'selected_option': selected_option,
        'product_categories': product_categories if selected_option == 'category' else None,
        'products': products if selected_option == 'product' else None,
        'parent_variants': parent_variants if selected_option == 'parentVariant' else None,
        'child_variants': child_variants if selected_option == 'childVariant' else None,
        # Add other context variables based on your logic
    }

    return render(request, 'add_new_discount.html', context)



def contains_only_spaces(value):
    return value.isspace()

def create_discount_category(request):
    """
    Handles the creation of a discount for a product category.

    Retrieves input data from the form submitted via POST request, including name, description,
    discount type (percentage or fixed amount), discount value, and whether the discount is active.
    Validates the input data and creates a new Discount instance if the input is valid.
    Updates the discount field in the ProductCategory model with the created discount.
    Returns appropriate messages indicating success or error.

    Parameters:
        request (HttpRequest): The HTTP request object containing form data.

    Returns:
        HttpResponseRedirect: Redirects to the admin_discount page upon successful creation of the discount.
    """
    if request.method == 'POST':
        try:
            # Get input data from the form
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_percentage = request.POST.get('is_percentage') == 'True'
            disc_value = request.POST.get('disc_value')
            isactive = request.POST.get('isactive')
            category_id = request.POST.get('category_id')

            # Validate the input data
            if not name or not disc_value or not isactive or contains_only_spaces(name) or contains_only_spaces(disc_value) or contains_only_spaces(isactive):
                raise ValidationError("Name, Value, and Status are required fields and should not contain only spaces.")

            disc_value = float(disc_value)

            if is_percentage and (disc_value < 0 or disc_value > 90):
                raise ValidationError("Percentage discount value should be between 0 and 90.")

            # Create a new Discount instance
            discount = Discount.objects.create(
                name=name,
                description=description,
                is_percentage=is_percentage,
                disc_value=disc_value,
                isactive=isactive
            )

            # Update the discount field in the ProductCategory model
            category = ProductCategory.objects.get(id=category_id)
            category.discount = discount
            category.save()

            messages.success(request, 'Discount created successfully!')
            return redirect('admin_discount')  # Redirect to the appropriate page

        except ValidationError as e:
            # Handle validation errors
            error_message = str(e)
            messages.error(request, error_message)

    # If the request method is not POST or if there are errors, render the form
    return redirect('add_new_discount')


def create_discount_product(request):
    """
    Handles the creation of a discount for a product.

    Retrieves input data from the form submitted via POST request, including name, description,
    discount type (percentage or fixed amount), discount value, and whether the discount is active.
    Validates the input data and creates a new Discount instance if the input is valid.
    Updates the discount field in the Product model with the created discount.
    Returns appropriate messages indicating success or error.

    Parameters:
        request (HttpRequest): The HTTP request object containing form data.

    Returns:
        HttpResponseRedirect: Redirects to the admin_discount page upon successful creation of the discount.
    """
    if request.method == 'POST':
        try:
            # Get input data from the form
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_percentage = request.POST.get('is_percentage') == 'True'
            disc_value = request.POST.get('disc_value')
            isactive = request.POST.get('isactive')
            product_id = request.POST.get('product_id')

            # Validate the input data
            if not name or not disc_value or not isactive or contains_only_spaces(name) or contains_only_spaces(disc_value) or contains_only_spaces(isactive):
                raise ValidationError("Name, Value, and Status are required fields and should not contain only spaces.")

            disc_value = float(disc_value)

            if is_percentage and (disc_value < 0 or disc_value > 90):
                raise ValidationError("Percentage discount value should be between 0 and 90.")

            # Create a new Discount instance
            discount = Discount.objects.create(
                name=name,
                description=description,
                is_percentage=is_percentage,
                disc_value=disc_value,
                isactive=isactive
            )

            # Update the discount field in the ProductCategory model
            product = Product.objects.get(id=product_id)
            product.discount = discount
            product.save()

            messages.success(request, 'Discount created successfully!')
            return redirect('admin_discount')  # Redirect to the appropriate page

        except ValidationError as e:
            # Handle validation errors
            error_message = str(e)
            messages.error(request, error_message)

    # If the request method is not POST or if there are errors, render the form
    return redirect('add_new_discount')

def create_discount_parent_variant(request):
    """
    Handles the creation of a discount for a product parent variant.

    Retrieves input data from the form submitted via POST request, including name, description,
    discount type (percentage or fixed amount), discount value, and whether the discount is active.
    Validates the input data and creates a new Discount instance if the input is valid.
    Updates the discount field in the ProductParentVariant model with the created discount.
    Returns appropriate messages indicating success or error.

    Parameters:
        request (HttpRequest): The HTTP request object containing form data.

    Returns:
        HttpResponseRedirect: Redirects to the admin_discount page upon successful creation of the discount.
    """
    if request.method == 'POST':
        try:
            # Get input data from the form
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_percentage = request.POST.get('is_percentage') == 'True'
            disc_value = request.POST.get('disc_value')
            isactive = request.POST.get('isactive')
            parent_variant_id = request.POST.get('product_id')

            # Validate the input data
            if not name or not disc_value or not isactive or contains_only_spaces(name) or contains_only_spaces(disc_value) or contains_only_spaces(isactive):
                raise ValidationError("Name, Value, and Status are required fields and should not contain only spaces.")

            disc_value = float(disc_value)

            if is_percentage and (disc_value < 0 or disc_value > 90):
                raise ValidationError("Percentage discount value should be between 0 and 90.")

            # Create a new Discount instance
            discount = Discount.objects.create(
                name=name,
                description=description,
                is_percentage=is_percentage,
                disc_value=disc_value,
                isactive=isactive
            )

            # Update the discount field in the ProductCategory model
            product = ProductParentVariant.objects.get(id=parent_variant_id)
            product.discount = discount
            product.save()

            messages.success(request, 'Discount created successfully!')
            return redirect('admin_discount')  # Redirect to the appropriate page

        except ValidationError as e:
            # Handle validation errors
            error_message = str(e)
            messages.error(request, error_message)

    # If the request method is not POST or if there are errors, render the form
    return redirect('add_new_discount')


def create_discount_child_variant(request):
    """
    Handles the creation of a discount for a product child variant.

    Retrieves input data from the form submitted via POST request, including name, description,
    discount type (percentage or fixed amount), discount value, and whether the discount is active.
    Validates the input data and creates a new Discount instance if the input is valid.
    Updates the discount field in the ProductChildVariant model with the created discount.
    Returns appropriate messages indicating success or error.

    Parameters:
        request (HttpRequest): The HTTP request object containing form data.

    Returns:
        HttpResponseRedirect: Redirects to the admin_discount page upon successful creation of the discount.
    """
    if request.method == 'POST':
        try:
            # Get input data from the form
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_percentage = request.POST.get('is_percentage') == 'True'
            disc_value = request.POST.get('disc_value')
            isactive = request.POST.get('isactive')
            child_variant_id = request.POST.get('product_id')

            # Validate the input data
            if not name or not disc_value or not isactive or contains_only_spaces(name) or contains_only_spaces(disc_value) or contains_only_spaces(isactive):
                raise ValidationError("Name, Value, and Status are required fields and should not contain only spaces.")

            disc_value = float(disc_value)

            if is_percentage and (disc_value < 0 or disc_value > 90):
                raise ValidationError("Percentage discount value should be between 0 and 90.")

            # Create a new Discount instance
            discount = Discount.objects.create(
                name=name,
                description=description,
                is_percentage=is_percentage,
                disc_value=disc_value,
                isactive=isactive
            )

            # Update the discount field in the ProductCategory model
            product = ProductChildVariant.objects.get(id=child_variant_id)
            product.discount = discount
            product.save()

            messages.success(request, 'Discount created successfully!')
            return redirect('admin_discount')  

        except ValidationError as e:
            # Handle validation errors
            error_message = str(e)
            messages.error(request, error_message)

    
    return redirect('add_new_discount')








def edit_discount(request, discount_id):
    discount = get_object_or_404(Discount, pk=discount_id)

    if request.method == 'POST':
        # Retrieve form data from request.POST
        name = request.POST.get('editDiscountName').strip()
        description = request.POST.get('editDiscountDescription').strip()
        disc_value = request.POST.get('editDiscountValue').strip()

        # Check for empty or only space values in critical fields
        if not name or not disc_value:
            messages.error(request, 'Name and Value cannot be empty or contain only spaces.')
            return redirect('admin_discount')

        # Update discount data
        discount.name = name
        discount.description = description
        discount.is_percentage = request.POST.get('editDiscountType') == 'percentage'
        discount.disc_value = Decimal(disc_value)
        discount.isactive = request.POST.get('editDiscountIsActive') == 'yes'

        # Save the updated discount
        discount.save()

        messages.success(request, 'Discount updated successfully.')
        return redirect('admin_discount')  # Update the URL as needed

    return redirect('admin_discount')








def fetch_product_details(request):
    """
    Fetches details of the top 5 most ordered product child variants.

    Retrieves the top 5 most ordered product child variants along with their details,
    including product name, description, category, main image URL, color, price, size,
    total orders, and total revenue.
    Constructs a JSON response containing the product details.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response containing the details of the top 5 most ordered product child variants.
    """
    # Get the top 5 most ordered product child variants
    most_ordered_products_child = OrderItems.objects.values('product').annotate(total_orders=Count('product')).order_by('-total_orders')[:5]
    
    product_details_list = []
    
    for product_child in most_ordered_products_child:
        # Retrieve the product child variant instance
        product_child_variant = ProductChildVariant.objects.get(pk=product_child['product'])
        
        # Get the parent variant and product instances
        parent_variant = product_child_variant.parent_variant
        product = parent_variant.product

        # Calculate total revenue for the product
        total_revenue = OrderItems.objects.filter(product=product_child_variant).aggregate(total_revenue=Sum('amount'))['total_revenue']
        if total_revenue is None:
            total_revenue = 0  # Handle case where there are no orders for the product

        # Construct the product details JSON response
        product_details = {
            'product_id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category.name,
            'main_image': parent_variant.main_image.url,
            'color': parent_variant.color,
            'price': product_child_variant.price,
            'size': product_child_variant.inventory_child.size,
            'total_orders': product_child['total_orders'],
            'total_revenue': total_revenue,
        }
        
        product_details_list.append(product_details)

    return JsonResponse(product_details_list, safe=False)



def admin_banner(request):
    """
    Renders the admin banner page with all product categories and existing banners.

    Retrieves all product categories and existing banners.
    Renders the admin banner page with the retrieved data.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the admin banner page with product categories and banners.
    """
    category = ProductCategory.objects.all()
    banners = Banner.objects.all()
    
    return render(request, 'admin_banner.html',{'categories':category, 'banners': banners})


def add_banner(request):
    """
    Renders the add banner page with products filtered by category.

    Retrieves the category ID from the request POST data.
    Filters products based on the category ID.
    Renders the add banner page with the filtered products.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the add banner page with the filtered products.
    """
    
    if request.method == 'POST':
        cat = request.POST.get('cat')
      

        product = Product.objects.filter(category_id = cat )



        return render(request,'add_banner.html', {'products' : product})  

    return redirect('admin_banner') 


def create_banner(request):
    """
    Handles the creation of a banner.

    Retrieves data from the request including title, image, text,
    product ID, start date, and end date.
    Validates the provided data and creates a new banner in the database.
    Redirects to the admin banner page after successful creation.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the admin banner page.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        image = request.FILES.get('image')
        text = request.POST.get('text')
        product_id = request.POST.get('product')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')


        product = Product.objects.get(id = product_id)



        banner = Banner.objects.create(
            title=title,
            image=image,
            text=text,
            start_date=start_date,
            end_date=end_date,
            reference = product
        )
        banner.save()

        return redirect('admin_banner')  

    return redirect('admin_banner') 
    



          




        
     






    







        
    


