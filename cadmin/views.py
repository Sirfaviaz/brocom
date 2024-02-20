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
    return dt.replace(hour=(dt.hour // 4) * 4, minute=0, second=0, microsecond=0)

def chart_data(request, time_range):
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
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    
    userinfo = User.objects.filter(adminstatus='user')
    
    context = {
        'userinfo': userinfo,
    }
    
    return render(request, 'admin_user.html', context)

def user_block(request, id):
    userinfo = get_object_or_404(User, id=id)

    if userinfo.status == 'active':
        userinfo.status = 'block'
    elif userinfo.status == 'block':
        userinfo.status = 'active'
    
    userinfo.save()  

    return redirect('admin_user')

def user_search(request):
    # if 'admin' in request.session:
        query = request.GET['query']
        allPosts = User.objects.filter(username__icontains = query)
        context = {'userinfo':allPosts}
        return render(request, 'admin_user.html', context)
    # else:
    #     return redirect('admin_login')

def admin_product(request):
    # if 'admin' not in request.session:
    #     return redirect('admin_login') 

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
    parent_variant_id = request.GET.get('parent_variant_id')
 

    sizes = ProductChildVariantInventory.objects.filter(parent_variant_id=parent_variant_id).values('id', 'size')

    return JsonResponse(list(sizes), safe=False)


def add_product(request):
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
    if not field.strip():

        return f'{field_name} cannot be empty or contain only spaces.'
    return False 


def search_product(request):
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
    # else:
    #     return redirect('admin_login')
    



def edit_product(request,id):
    # if 'admin' not in request.session:
    #     return redirect('admin_login') 
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
            
        # userinfo.save()
    return redirect('admin_product')



@csrf_exempt
def edit_image(request, product_id, image_id):
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
    # if 'admin' not in request.session:
    #     return redirect('admin_login') 
    
    prodinfo = Product.objects.filter(id=id)
    prodinfo.status = 'inactive'
    prodinfo.save()
    return redirect('admin_product')
        



def admin_category(request):
    # if 'admin' not in request.session:
    #     return redirect('admin_login') 
    catinfo = ProductCategory.objects.all()
    context = {
        'catinfo':catinfo,
    }
    return render(request, 'admin_category.html',context)



def add_category(request):
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
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductCategory.objects.filter(name__icontains = query)
        context = {'catinfo':allPosts}
        return render(request, 'admin_category.html', context)
    else:
        return redirect('admin_login')

def edit_category(request,id):
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
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    catinfo = ProductCategory.objects.filter(id=id)
    catinfo.status = 'inactive'
    catinfo.save()
    return redirect('admin_category')



def admin_inventory(request):
    
    invntinfo = ProductInventory.objects.all()
    context = {
        'invntinfo':invntinfo,
    }
    return render(request, 'admin_inventory.html',context)

def search_inventory(request):
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductInventory.objects.filter(name__icontains = query)
        context = {'invntinfo':allPosts}
        return render(request, 'admin_inventory.html',context)
    else:
        return redirect('admin_login')

def add_inventory(request):
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
    inventory = get_object_or_404(ProductInventory, id=id)  
    
    parent_variants = inventory.variants.all()
    
    return render(request, 'admin_variant_inventory.html', {'inventory': inventory, 'parent_variants': parent_variants})

def edit_parent_variant(request, variant_id):
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
    if request.method == 'POST':
        
        inventory_id = request.POST.get('inventory_id')
        inventory = ProductInventory.objects.get(id=inventory_id)

       
        color = request.POST.get('color')
        color = color.capitalize()
       
        ProductParentVariantInventory.objects.create(inventory=inventory, color=color)
       
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('variant_inventory_display', inventory_id)
def edit_child_variant(request, child_variant_id):
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
    # if 'admin' not in request.session:
    #     return redirect('admin_login') 
  
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
    catinfo = ProductCategory.objects.all()
    invntinfo = ProductInventory.objects.all()
    context = {
        
        'catinfo': catinfo,
        'invntinfo': invntinfo,
    }

    return render(request, 'admin_Product_create.html', context)


def get_parent_variants(request):
    if request.method == 'GET' and 'inventory_id' in request.GET:
        inventory_id = request.GET['inventory_id']
        
        # Assuming you have a model for ProductParentVariantInventory
        parent_variants = ProductParentVariantInventory.objects.filter(inventory_id=inventory_id)
        
        # Return data as JSON
        data = [{'id': variant.id, 'color': variant.color} for variant in parent_variants]
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)



def view_product_variants(request,product_id):
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
    referral_rewards_total = ReferralCodeHistory.objects.filter(user=user).aggregate(Sum('referral_rewards'))['referral_rewards__sum'] or 0
    joining_rewards_total = ReferralCodeHistory.objects.filter(new_user=user).aggregate(Sum('joining_rewards'))['joining_rewards__sum'] or 0

    return {
        'user': user,
        'referral_rewards_total': referral_rewards_total,
        'joining_rewards_total': joining_rewards_total,
    }





def get_user_totals(user):
    if user.username == 'admin':
        return 0, 0  

    referral_rewards_total = ReferralCodeHistory.objects.filter(user=user).aggregate(Sum('referral_rewards'))['referral_rewards__sum'] or 0
    joining_rewards_total = ReferralCodeHistory.objects.filter(new_user=user).aggregate(Sum('joining_rewards'))['joining_rewards__sum'] or 0

    return referral_rewards_total, joining_rewards_total

def plot_referral_rewards(users):
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

def edit_referral(request):
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
    # Retrieve all active discounts
    discounts = Discount.objects.filter(isactive=True)

    # Pass the discounts to the template
    context = {'discounts': discounts}
    return render(request, 'admin_discount.html', context)


def add_new_discount(request):
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
            return redirect('admin_discount')  # Redirect to the appropriate page

        except ValidationError as e:
            # Handle validation errors
            error_message = str(e)
            messages.error(request, error_message)

    # If the request method is not POST or if there are errors, render the form
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
    category = ProductCategory.objects.all()
    banners = Banner.objects.all()
    
    return render(request, 'admin_banner.html',{'categories':category, 'banners': banners})


def add_banner(request):
    if request.method == 'POST':
        cat = request.POST.get('cat')
      

        product = Product.objects.filter(category_id = cat )



        return render(request,'add_banner.html', {'products' : product})  

    return redirect('admin_banner') 


def create_banner(request):
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
    



          




        
     






    







        
    


