import base64
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import Product,ProductCategory,ProductInventory
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image


# Create your views here.
# Inventory Management

def inventory_admin(request):
    if 'admin' not in request.session:
        return redirect('login') 
    invntinfo = ProductInventory.objects.all()
    context = {
        'invntinfo':invntinfo,
    }
    return render(request, 'inventory_admin.html',context)

@never_cache
def inventory_create(request):
    if request.method == "POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        quantity = request.POST.get('quantity')
        supplier_id = request.POST.get('supplier_id')
        status = request.POST.get('inlineRadioOptionsStatus')
        has_variants = request.POST.get('inlineRadioOptionsHasvariants')
      

        
        invntinfo = ProductInventory(name=name, description=desc, quantity=quantity, supplier_id = supplier_id, status=status,has_variants = has_variants)
        invntinfo.save()
        messages.success(request, "Succesfully Created")

        return redirect('inventory_admin')  
    
@never_cache
def inventory_search(request):
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductInventory.objects.filter(name__icontains = query)
        context = {'invntinfo':allPosts}
        return render(request, 'inventory_admin.html', context)
    else:
        return redirect('admin_login')
    

def inventory_Update(request, id):
    if 'admin' not in request.session:
        return redirect('admin_login') 

    if request.method == "POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        quantity = request.POST.get('quantity')
        supplier_id = request.POST.get('supplier_id')
        status = request.POST.get('inlineRadioOptionsStatus')
        has_variants = request.POST.get('inlineRadioOptionsHasvariants')
     

        invnt = ProductInventory.objects.get(id=id)

        if name is not None and invnt.name != name:
            invnt.name = name

        if desc is not None and invnt.description != desc:
            invnt.description = desc

        if quantity is not None and invnt.quantity != quantity:
            invnt.quantity = quantity

        if supplier_id is not None and invnt.supplier_id != supplier_id:
            invnt.supplier_id = supplier_id

        if status is not None and invnt.status != status:
            invnt.status = status
        if has_variants is not None and invnt.has_variants != has_variants:
            invnt.has_variants = has_variants

        invnt.save()

        messages.success(request, 'Inventory updated successfully.')
        return redirect('inventory_admin')
    
  
    messages.error(request, 'Invalid request.')
    return redirect('inventory_admin')
        
    return render(request, 'inventory_admin.html')

def inactive_inventory(request, id):
    if 'admin' not in request.session:
        return redirect('admin_login') 

    

    invntinfo = get_object_or_404(ProductInventory, id=id)

    try:
        invntinfo.status = 'inactive'
        invntinfo.save()
        messages.success(request, 'Inventory set as inactive successfully.')
    except Exception as e:
        messages.error(request, f'Error setting inventory as inactive: {e}')

    return redirect('inventory_admin')


def add_variant(request):
    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')
        inventory_id = request.POST.get('inventory_id')

        if size and quantity and inventory_id:
            try:
                
                existing_variant = ProductVariant.objects.filter(
                    size=size,
                    inventory_id=inventory_id,
                   
                ).first()

                if existing_variant:
               
                    existing_variant.quantity += int(quantity)
                    existing_variant.save()
                    messages.success(request, 'Variant updated successfully!')
                else:
                    
                    ProductVariant.objects.create(
                        size=size,
                        quantity=quantity,
                        inventory_id=inventory_id,
                       
                    )
                    messages.success(request, 'Variant added successfully!')

                return redirect('inventory_admin')
            except Exception as e:
                messages.error(request, f"Error adding/updating variant: {str(e.get('__all__', [])[0])}")
               
        else:
            messages.error(request, 'Please fill out all the required fields.')

    return redirect('inventory_admin')








# Product Category

def category_admin(request):
    if 'admin' not in request.session:
        return redirect('admin_login') 
    catinfo = ProductCategory.objects.all()
    context = {
        'catinfo':catinfo,
    }
    return render(request, 'category_admin.html',context)

@never_cache
def category_create(request):
    if request.method == "POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        status = request.POST.get('inlineRadioOptionsStatus')
      

        
        catinfo = ProductCategory(name=name, description=desc,  status=status)
        catinfo.save()
        messages.success(request, "Succesfully Created")

        return redirect('category_admin')  
    
@never_cache
def category_search(request):
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = ProductCategory.objects.filter(name__icontains = query)
        context = {'catinfo':allPosts}
        return render(request, 'category_admin.html', context)
    else:
        return redirect('admin_login')
    
def category_Update(request,id):
    if 'admin' not in request.session:
        return redirect('login') 
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('desc')
        status = request.POST.get('inlineRadioOptionsStatus')

    cat = ProductCategory.objects.get(id=id)

    if name is not None and name != cat.name :
            messages.error(request, 'Category with the same name already exists.')
            return render(request, 'category_admin.html')
    
    

    if name is not None and cat.name != name:
        cat.name = name

    if description is not None and cat.description != description:
        cat.description = description

   

    if status is not None and cat.status != status:
        cat.status = status


    
    cat.save()
            
        # userinfo.save()
    return redirect('category_admin')
        
    return render(request, 'category_admin.html')

def inactive_category(request,id):
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    catinfo = ProductCategory.objects.filter(id=id)
    catinfo.status = 'inactive'
    catinfo.save()
    return redirect('category_admin')




def product_admin(request):
    if 'admin' not in request.session:
        return redirect('admin_login') 

    prodinfo = Product.objects.all()
    catinfo = ProductCategory.objects.all()
    invntinfo = ProductInventory.objects.all()

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

    return render(request, 'product_admin.html', context)





# @never_cache
# def product_create(request):
#     if request.method == "POST":
#         name = request.POST.get('name')
#         desc = request.POST.get('desc')
#         price = request.POST.get('price')
#         category_id = request.POST.get('category_id')
#         discount_id = request.POST.get('discount_id')
#         inventory_id = request.POST.get('inventory_id')
#         status = request.POST.get('inlineRadioOptionsStatus')
#         variant = request.POST.get('variantinlineRadioOptionsStatus')
#         main_image = request.FILES.get('image1')
#         if main_image:
#             main_image = main_image
#       
#         # Create Product instance
#         prodinfo = Product(
#             name=name,
#             description=desc,
#             price=price,
#             category_id=category_id,
#             discount=discount_id,
#             inventory_id=inventory_id,
#             status=status,
#             has_variants=variant,
#             main_image = main_image
#         )
#         prodinfo.save()

      
     

#         # Save additional images (Image 2 to 4) to the ProductImage model
#         for i in range(2, 5):
#             image_field_name = 'image{}'.format(i)
#             image = request.FILES.get(image_field_name)
#             if image:
#                 # Resize the image if needed
#                 # image = resize_image(image)
#                 product_image = ProductImage(product=prodinfo, image=image)
#                 product_image.save()
#            
#         return redirect('product_admin')

def resize_image(image):
    """
    Resize the image to a specific size if needed.
    """
    max_size = (300, 300)
    img = Image.open(image)
    img.thumbnail(max_size, Image.LANCZOS)

    # Save the resized image to a BytesIO buffer
    image_io = BytesIO()
    img.save(image_io, format='JPEG', quality=75)
    image_io.seek(0)

    # Replace the original image with the resized one
    image.file = InMemoryUploadedFile(
        image_io,
        None,
        '{}.jpg'.format(image.name.split('.')[0]),
        'image/jpeg',
        image_io.tell(),
        None
    )
    return image
    
@never_cache
def product_search(request):
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = Product.objects.filter(name__icontains = query)
        context = {'catinfo':allPosts}
        return render(request, 'category_admin.html', context)
    else:
        return redirect('admin_login')
    
def product_update(request,id):
    if 'admin' not in request.session:
        return redirect('admin_login') 
    if request.method == "POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        price = request.POST.get('price')
        category_id = request.POST.get('category_id')
        discount_id = request.POST.get('discount_id')
        inventory_id = request.POST.get('inventory_id')
        status = request.POST.get('inlineRadioOptionsStatus')


    prod = Product.objects.get(id=id)

    if name is not None and prod.name != name:
        prod.name = name

    if desc is not None and prod.desc != desc:
        prod.description = desc

    if price is not None and prod.price != price:
        prod.price = price

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
    return redirect('category_admin')
        
    return render(request, 'category_admin.html')

def inactive_product(request,id):
    if 'admin' not in request.session:
        return redirect('admin_login') 
    
    prodinfo = Product.objects.filter(id=id)
    prodinfo.status = 'inactive'
    prodinfo.save()
    return redirect('product_admin')

@csrf_exempt
def update_main_image(request, product_id):
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

@csrf_exempt
def update_image(request, product_id, image_id):
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

# def add_productimage(request):
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
  
#         try:
#             for i in range(1, 4):  
#                 image_file = request.FILES.get(f'image{product_id}{i}')
#                 if image_file:
               
#                     ProductImage.objects.create(product_id=product_id, image=image_file)
          
#             messages.success(request, 'Images added successfully')
#             return redirect('product_admin')  
#         except Exception as e:
        
#             messages.error(request, f'Error adding images: {str(e.get('__all__', [])[0])}')
            
#             return redirect('product_admin')  
#     else:
     
#         messages.error(request, 'Something went wrong. Please contact support.')
#         return redirect('product_admin')



    
