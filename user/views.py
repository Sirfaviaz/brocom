import datetime
from decimal import Decimal
from gettext import translation
import random
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect 
from django.contrib.auth import authenticate
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.db.models import Count

from Brocom.settings import RAZORPAY_KEY, RAZORPAY_SECRET
from django.db.models import F, Value
from cadmin.models import Banner, ReferralRewardSchemes, UserHistory, UserPreferences, UserPreferencesCount, Referral, ReferralCodeHistory

from orders.models import AppliedCoupon, Cart, Coupon
from orders.views import check_out
from .models import EmailVerification, Invoice, PaymentDetails, User, Address, Wallet, WalletTranslation, Order
from product.models import Product, ProductCategory, ProductChildVariant, ProductChildVariantInventory, ProductInventory, ProductParentVariant, ProductParentVariantInventory, ProductRating, ProductVariantColorImages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.contrib.auth import logout
from django.views.generic import ListView
from .models import OrderDetails, OrderItems
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg

from razorpay.errors import SignatureVerificationError
from django.db.models import Min
from reportlab.lib.pagesizes import letter,A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.template.loader import render_to_string
import pdfkit
from weasyprint import CSS, HTML,cssselect2
from django.db.models import Max





# for otp generator
import secrets
import string


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.db import transaction
from razorpay.errors import BadRequestError

import json
from reportlab.pdfgen import canvas


# Create your views here.
def user_login(request):
    """
    View function to handle user login.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
 
    if 'username' in request.session:
        m = User.objects.get(username=request.session['username'])
        if m.status != 'active':
            messages.error(request, f"Sorry, {request.session['username']} your account is currently suspended, Kindly contact blahblah@brocom.com for your queries!")
            return render(request,'user_login.html')
        return redirect('index')
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(password)
        try:
            m = User.objects.get(username=username)
           
            
            
            if check_password(password, m.password):
                print(m.password)
                print(password)
                if m.verified == False:
                    
                    request.session['username'] = username
                    return redirect('not_verified')
                if m.status != 'active':
                    messages.error(request,'Sorry, your account is currently suspended, Kindly contact blahblah@brocom.com for your blaberings!')
                    return redirect('user_login')

                request.session['username'] = username
                return redirect('index')
            
        except:
            pass
        
        messages.error(request, "Username or Password Incorrect") 
    return render(request,"user_login.html")

def view_signup(request):
    if ReferralRewardSchemes.objects.filter(status=True).first():
        active_referral_scheme = ReferralRewardSchemes.objects.filter(status=True).first()
    else:
        active_referral_scheme = False
    return render(request, 'user_signup.html', {'active_referral_scheme':active_referral_scheme})

def user_signup(request):
    """
    View function to handle user sign-up.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """

    
   
    if 'username' in request.session:
        return redirect('index')
    if request.method == 'POST':
        username = request.POST["username"]
        gender = request.POST["inlineRadioOptions"]
        birthday = request.POST["birthday"]
        e_mail = request.POST["email"]
        mobile_number = request.POST["mobile"]
        password = request.POST["password"]
        code = request.POST.get('code')
        if code is not None and code.strip():  # Check if code is not None and not empty or contains only whitespace
            try:
                ref = Referral.objects.get(referral_code=code)
            except Referral.DoesNotExist:
                messages.error(request, "Wrong Referral URL, try again")
                return render(request, 'user_signup.html')



        cp = request.POST["password1"]  
       
        email_validator = EmailValidator(message='Enter a valid email address.')
        try:
            email_validator(e_mail)
        except ValidationError as e:
            messages.error(request, e.message)
            return render(request, 'user_signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            
        elif User.objects.filter(email=e_mail).exists():
            messages.error(request, "Email already exists")
            
        elif User.objects.filter(mobile=mobile_number).exists():
            messages.error(request, "Mobile Number already exists")
            
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long")
        
        # elif len(mobile_number) >= 10:
        #     messages.error(request, "Mobile number should be under 10 characters long")
            
        elif password != cp:
            messages.error(request, "Passwords does not match")  
    
                  
                        
        else:
            hashed_password = make_password(password)
            myuser = User.objects.create(username=username, email=e_mail, password=hashed_password, mobile=mobile_number, gender = gender, birthday = birthday)
            myuser.save()
            
            request.session['username'] = username
            if code is not None and code.strip(): 
                log_reward(code,username)

            
            
            
          
            
            
            return redirect('send_otp')
    return render(request, 'user_signup.html')


def enter_mail(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate OTP and save it in EmailVerification model
            otp = generate_otp(5)  # Implement your OTP generation logic
            email_verification = EmailVerification.objects.create(user=user, email=email, otp=otp)
            subject = f'Password Reset Request for {user.username}'
            message = f'Your password reset OTP is {otp} '
            from_email = 'ecombrocom@gmail.com'
            to_email = [user.email]
            send_mail(subject, message, from_email, to_email)

            messages.success(request, "Password reset instructions sent to your email.")
            return render(request, 'password_reset.html', {'email': email, 'username': user.username if user else None})
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
    
    return render(request, 'enter_email.html')

def reset_password(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
       
        try:
            email_verification = EmailVerification.objects.get(otp=otp)
            # Check if OTP is valid (within a certain timeframe)
            if is_valid_otp(email_verification):
                # Update user's password
                user = email_verification.user
                hashed_password = make_password(new_password)  # Hash the new password
                
                user.password = hashed_password  # Set the hashed password
                user.save()
                messages.success(request, "Password reset successfully.")
                return redirect('user_login')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except EmailVerification.DoesNotExist:
            messages.error(request, "Invalid OTP.")
    return render(request, 'password_reset.html')
        
def is_valid_otp(email_verification):
    """
    Checks if the OTP associated with the provided EmailVerification instance is valid.
    If the OTP is valid, deletes the entry from EmailVerification.
    """
    if email_verification:
        expiration_time = email_verification.created_at + timedelta(minutes=15)  
        if timezone.now() <= expiration_time:
            
            email_verification.delete()
           
            return True
    return False


def forgot_password(request):

    return render(request, 'enter_email.html')




def log_reward(code,username):
    """
    Log the reward when a user signs up using a referral code.

    Args:
    - code: Referral code used during sign-up.
    - username: Username of the new user who signed up using the referral code.

    Returns:
    - None
    """
    referral = Referral.objects.get(referral_code=code)
    referral_user = referral.user
    new_user = User.objects.get(username=username)
    new_user_id = new_user.id
    ReferralCodeHistory.objects.create(user = referral_user, new_user = new_user)

def send_rewards(user_id):
    """
    Send rewards to a new user and their referrer.

    Args:
    - user_id: ID of the new user who signed up.

    Returns:
    - None
    """
    new_user = User.objects.get(id=user_id)

    if ReferralCodeHistory.objects.filter(new_user=new_user).exists():
        referral_history_qs = ReferralCodeHistory.objects.filter(new_user=new_user)

        if referral_history_qs.exists():
            referral = referral_history_qs.get()
            referral_user = referral.user

            reward_scheme = ReferralRewardSchemes.objects.first()
            join_reward_amount = reward_scheme.joining
           

            # Create a new Wallet for the new user if one doesn't exist
            new_user_wallet, created = Wallet.objects.get_or_create(user=new_user)

            # Deposit joining reward for the new user
            new_user_wallet.deposit(join_reward_amount)

            # Create a WalletTranslation entry for the new user
            n_narration = 'Joining bonus'
            WalletTranslation.objects.create(
                wallet=new_user_wallet,
                type='r',  # Assuming 'r' is for Received
                amount=join_reward_amount,
                naration=n_narration
            )

            # Send email to the new user
            subject = f'Congratulations! You received rupees {join_reward_amount} in your Brocom wallet'
            message = f'Your wallet is credited with rupees {join_reward_amount} for {n_narration}'
            from_email = 'ecombrocom@gmail.com'
            to_email = [new_user.email]
            send_mail(subject, message, from_email, to_email)

            # Deposit referral reward for the referral user
            referral_reward_amount = reward_scheme.referral
            referral_user_wallet, created = Wallet.objects.get_or_create(user=referral_user)
            referral_user_wallet.deposit(referral_reward_amount)

            # Create a WalletTranslation entry for the referral user
            r_narration = 'Referral reward'
            WalletTranslation.objects.create(
                wallet=referral_user_wallet,
                type='r',  # Assuming 'r' is for Received
                amount=referral_reward_amount,
                naration=r_narration
            )

            # Send email to the referral user
            subject = f'Congratulations! You received rupees {referral_reward_amount} in your Brocom wallet'
            message = f'Your wallet is credited with rupees {referral_reward_amount} for {r_narration}'
            from_email = 'ecombrocom@gmail.com'
            to_email = [referral_user.email]
            send_mail(subject, message, from_email, to_email)

            # Update referral record with rewards
            referral.referral_rewards = referral_reward_amount
            referral.joining_rewards = join_reward_amount
            referral.save()
            return
    return

    
    



def verify_otp(request):
    """
    Verify the OTP entered by the user during the signup process.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        email = request.POST.get('email')
       
        
        email_verification = EmailVerification.objects.filter(email= email).last()
        
        if email_verification and email_verification.otp == entered_otp:
         
            expiry_time = email_verification.created_at + timezone.timedelta(minutes=1)
            if timezone.now() <= expiry_time:
               
                email_verification.delete()
                user = User.objects.get(email=email)
                user.verified = True
                user.save()
                user_id=user.id
                send_rewards(user_id)

                return render(request, 'user_login.html')
            else:
              
                return render(request, 'otp_expired.html')

        messages.error(request, "Incorrect OTP. Please try again.")

        return render(request, 'verify_otp.html')
    messages.error(request, " Incorrect") 
    return render(request, 'verify_otp.html')

def send_otp(request):
    """
    Send OTP to the user's email for verification.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """

    username = request.session['username']

    email = User.objects.filter(username=username).values_list('email', flat=True).first()
    otp = generate_otp(5)
    user_id = User.objects.filter(email=email).values_list('id', flat=True).first()
    e_mail = email
    
 
    email_verification = EmailVerification.objects.create(email=e_mail, otp=otp, user_id = user_id)

 
    subject = 'Your OTP for Email Verification'
    message = f'Your OTP for brocom is: {otp}'
    from_email = 'ecombrocom@gmail.com'
    to_email = [email]

    send_mail(subject, message, from_email, to_email)
    expiry_time = email_verification.created_at + timezone.timedelta(minutes=1)
    
    return render(request,'verify_otp.html', {'expiry_time': expiry_time, 'email':email})

def user_logout(request):
    if 'username' in request.session:
        request.session.flush()
    return redirect('user_login')


def not_verified(request):
   
    return render(request, 'Notverified.html')

def click_here(request):
    
    
    return redirect('send_otp')

# otp generator
def generate_otp(length):
    characters = string.ascii_letters + string.digits  
    otp = ''.join(secrets.choice(characters) for _ in range(length))
    return otp 



def change_email(request):
    """
    Change the email address associated with the user's account.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    username = request.session.get('username', None)

    if username:
        if request.method == 'POST':
            new_email = request.POST.get('email', '')

            if new_email:
                user = User.objects.get(username=username)
                user.email = new_email
                user.save()

                messages.success(request, 'Email changed successfully.')
                # return render(request, "change_email.html")
                return redirect('send_otp')
            else:
                messages.error(request, 'Invalid email provided.')
    else:
        messages.error(request, 'User not authenticated.')

    # Handle redirect or render logic after processing the form
    return render(request,"change_email.html")





@never_cache
def index(request):
    """
    Render the main page of the website.
    Banner, recently viewed products, last purchases and new products in child variant level

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """

    if 'username' in request.session:
        m = User.objects.get(username=request.session['username'])
        if m.status != 'active':
            messages.error(request, 'Sorry, your account is currently suspended. Kindly contact blahblah@brocom.com for assistance.')
            return redirect('user_login')
    else:
        return redirect('user_login')

    clothing_all = Product.objects.filter(category_id=1)
    tech_all = OrderItems.objects.filter(order__user=m).order_by('product').distinct('product')[:10]
    nontech_all = ProductChildVariant.objects.order_by('-id')[:5]

    # Fetch user's preferences if available
    ordered_categories = ProductCategory.objects.filter(
        userpreferencescount__user=m
    ).annotate(
        category_count=Count('userpreferencescount')
    ).order_by('-category_count')

    if not ordered_categories.exists():
        banners = Banner.objects.all()  # Fetch all banners if user has no preferences
    else:
        # Fetch banners based on user's ordered categories
        banners_with_category = Banner.objects.filter(
            reference__category__in=ordered_categories
        ).annotate(
            product_category_id=F('reference__category__id')
        )

        category_order = {category.id: index for index, category in enumerate(ordered_categories)}

        banners = sorted(
            banners_with_category,
            key=lambda banner: category_order.get(banner.product_category_id, float('inf'))
        )

    # Fetch user's history if available
    user_history = Product.objects.none()
    if UserHistory.objects.filter(user=m).exists():
        user_history = Product.objects.filter(
            id__in=UserHistory.objects.filter(user=m)
            .values('product')
            .annotate(max_checked_at=Max('checked_at'))
            .order_by('max_checked_at')[:10]
            .values_list('product', flat=True)
        )

    # Render the index page with fetched data
    return render(request, 'Index.html', {'user_history': user_history, 'cproducts': clothing_all, 'tproducts': tech_all, 'nproducts': nontech_all, 'banners': banners})




@never_cache
def admin_login(request):
    """
    Handle the login process for administrators.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """

    if 'admin' in request.session:
    
        return redirect('admin_index')
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            m = User.objects.get(username=username)
            if m.password==password:
                if m.adminstatus == 'unauth':
                   
                    messages.error(request, 'admin not authenticated.')
                    return redirect('admin_login')
                
                if m.adminstatus == 'user':
                   
                    messages.error(request, 'Sorry, that was a wrong try, Please try here')
                    return redirect('user_login')
                if m.adminstatus == 'auth':
                    request.session['admin'] = username
                    messages.success(request,'Welcome, back')
                    return redirect('admin_index')
            
        except:
            pass
        
        messages.error(request, "Username or Password Incorrect") 
    return render(request,"admin_login.html")







@never_cache
def create(request):
    """
    Handle the creation of new user accounts.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    if request.method == "POST":
        username = request.POST.get('username')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        gender = request.POST.get('inlineRadioOptionsGender')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        verified = request.POST.get('inlineRadioOptionsVerification')
        birthday = request.POST.get('birthday')

        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            
        elif User.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile Number already exists")
            
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long")
        else:
            userinfo = User(username=username, firstname=firstname,lastname=lastname,gender = gender, email=email, mobile=mobile, password=password, verified=verified, birthday = birthday )
            userinfo.save()
            messages.success(request, "Succesfully Created")

        return redirect('user_admin')       




def update(request,id):
    """
    Handle the updating of user information.

    Args:
    - request: HTTP request object.
    - id: ID of the user to be updated.

    Returns:
    - HTTP response object.
    """
    if 'admin' not in request.session:
        return redirect('login') 
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        gender = request.POST.get('inlineRadioOptionsGender')
        verified = request.POST.get('inlineRadioOptionsVerification')
        birthday = request.POST.get('birthday')
     



    user = User.objects.get(id=id)

    if username is not None and user.username != username:
        user.username = username

    if firstname is not None and user.firstname != firstname:
        user.firstname = firstname

    if lastname is not None and user.lastname != lastname:
        user.lastname = lastname

    if birthday is not None and user.birthday != birthday:
        user.birthday = birthday

    if gender is not None and user.gender != gender:
        user.gender = gender

    if email is not None and user.email != email:
        user.email = email

    if mobile is not None and user.mobile != mobile:
        user.mobile = mobile

    if verified is not None and user.verified != verified:
        user.verified = verified

    if password is not None and user.password != password:
        user.password =password

    
    user.save()
            
       
    return redirect('user_admin')
        
 
def delete(request, id):
    """
    Handle the activation or deactivation of user accounts.

    Args:
    - request: HTTP request object.
    - id: ID of the user to be activated or deactivated.

    Returns:
    - HTTP response object.
    """
    userinfo = get_object_or_404(User, id=id)

    if userinfo.status == 'active':
        userinfo.status = 'block'
    elif userinfo.status == 'block':
        userinfo.status = 'active'
    
    userinfo.save()  # Save changes to the database

    return redirect('user_admin')


@never_cache
def search(request):
    if 'admin' in request.session:
        query = request.GET['query']
        allPosts = User.objects.filter(username__icontains = query)
        context = {'userinfo':allPosts}
        return render(request, 'user_admin.html', context)
    else:
        return redirect('admin_login')
    
@never_cache
def admin_logout(request):
    if 'admin' in request.session:
        request.session.flush()
    return redirect('admin_login')
    





def product_list(request):
    """
    Display a list of products with pagination and banners based on user preferences.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    products_per_page = 10
    user_instance = User.objects.get(username=request.session['username'])

   
    products_with_ratings = Product.objects.annotate(avg_rating=Avg('productrating__rating'))

  
    paginator = Paginator(products_with_ratings, products_per_page)

    user_preferences = UserPreferences.objects.filter(user=user_instance).values_list('preference', flat=True)

    if user_preferences:
   
        banners = Banner.objects.filter(reference__category__in=user_preferences)

   
        # today = datetime.date.today()
        # banners = matching_banners.filter(start_date__lte=today, end_date__gte=today)

    
    else:
    # If there are no preferences, retrieve a random banner
        banners = Banner.objects.order_by('?')[:1]


    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    

    category = ProductCategory.objects.all()
    count = 0
              
 
    context = {
        'category':category,
        'products': products,
        'count': count,
        'banners': banners,
        }
    return render(request, 'product_list.html', context)







def product_rating(request):
    """
    Handle the creation or updating of ratings and comments for products.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    if request.method == 'GET':
        rating = request.GET.get('rating')
        comments = request.GET.get('comment')
        product_id = request.GET.get('product_id')
        username = request.session.get('username')

        try:
            user_instance, created = User.objects.get_or_create(username=username)
            user_id = user_instance.id

            # Try to get an existing ProductRating instance
            product_rating_instance = ProductRating.objects.get(product_id=product_id, user=user_instance)

            # If the entry exists, update the rating and comments
            product_rating_instance.rating = rating
            product_rating_instance.comments = comments
            product_rating_instance.save()

            messages.success(request, 'Rating updated successfully')

        except ProductRating.DoesNotExist:
            # If the entry does not exist, create a new one
            ProductRating.objects.create(product_id=product_id, user=user_instance, rating=rating, comments=comments)
            messages.success(request, 'Rating created successfully')

        except ObjectDoesNotExist as e:
            error_message = f'Error: {e}'
            messages.error(request, error_message)

        # Always redirect to single_product, whether the entry was updated or created
        return redirect('single_product', product_id=product_id)

    # If the request method is not GET, redirect with an error message
    messages.error(request, 'Invalid request method')
    return redirect('single_product', product_id=product_id)


    


    


def list_product_search(request):

    if 'username' in request.session:
        query = request.GET.get('query')
        

        allPosts = Product.objects.filter(name__icontains = query)
        products= {'products':allPosts}
      
        return render(request, 'product_list.html', products)
    else:
        return redirect('product_list')
    





from django.db.models import Min

def product_filter(request):
    """
    Handle the filtering of products based on category, price range, and price sorting.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response object.
    """
    if 'username' in request.session:
        cat_query = request.GET.get('catFilterQuery')
        price_range = request.GET.get('priceRange')
        price_sort = request.GET.get('priceFilterQuery')
        
       

        # Use annotate to get the smallest price for each product
        all_products = Product.objects.annotate(smallest_price=Min('color__parent__price'))

        if price_sort:
            if price_sort == 'lh':
                all_products = all_products.order_by('smallest_price')
            else:
                all_products = all_products.order_by('-smallest_price')

        if cat_query:
            if cat_query in ['Clothings', 'Tech accessories', 'Non-tech accessories']:
                all_products = all_products.filter(category__name=cat_query)

        if price_range:
            min_price, max_price = map(int, price_range.split('-'))
            all_products = all_products.filter(smallest_price__range=(min_price, max_price))

        category = ProductCategory.objects.all()
        context = {
            'category': category,
            'products': all_products,
            'cate':cat_query,
            'range': price_range,
            'sort': price_sort,
        }
        return render(request, 'product_list.html', context)
    else:
        return redirect('product_list')


    







def single_product(request, product_id):
    """
    Display detailed information about a specific product.

    Args:
    - request: HTTP request object.
    - product_id: ID of the product to be displayed.

    Returns:
    - HTTP response object.
    """

    if 'username' in request.session:
        user = User.objects.get(username = request.session['username'])
        user_id = user.pk
        prod_id = product_id

        if request.method == 'GET':
            variant_id = request.GET.get('variant_id')

        if prod_id:
            product = get_object_or_404(Product, id=prod_id)

            # Fetch product images for all parent variants
            product_images = []
            parents = ProductParentVariant.objects.filter(product_id=product.id)
            for parent in parents:
                images = ProductVariantColorImages.objects.filter(parent_variant=parent.id)
                product_images.extend(images)

            # Fetch similar products
            cat = product.category
            cat_id = cat.id
            similar_products = Product.objects.filter(category_id=cat_id).exclude(id=prod_id)

            # Get product ratings
            product_ratings = ProductRating.objects.filter(product=product)
            average_rating = product_ratings.aggregate(Avg('rating'))['rating__avg']

            # Fetch product inventory and variants
            product_inventory = product.inventory
            parent_inventory = ProductParentVariantInventory.objects.filter(inventory=product_inventory)

            
            variants = []
            for parent_variant in parent_inventory:
                parent_variants = ProductParentVariant.objects.filter(inventory_parent=parent_variant.id)
                variants.extend(parent_variants)
            
                

            # Fetch child variants if a specific variant_id is provided
            child_variant = ProductChildVariantInventory.objects.filter(parent_variant=variant_id) if variant_id else None

            # Update UserPreferencesCount for the current user and category
            try:
                user_preference_count = UserPreferencesCount.objects.get(user_id=user_id, category=cat)
                user_preference_count.count = F('count') + 1
                user_preference_count.save()
            except UserPreferencesCount.DoesNotExist:
            # If the user doesn't have a preference count for the category, create a new entry
                UserPreferencesCount.objects.create(user_id=user_id, category=cat, count=1)
            
            
            # Create UserHistory entry for the user viewing the product
            UserHistory.objects.create(user_id=user_id, product=product)

            # Prepare the context
            context = {
                'single_product': product,
                'similar_products': similar_products,
                'product_ratings': product_ratings,
                'average_rating': average_rating,
                'product_images': product_images,
                'variants': variants,
                'product_inventory': product_inventory,
                'child_variant': child_variant,
            }

            return render(request, 'single_product.html', context)

    return redirect('user_login')  # Correct the redirect function call





def child_variant_details(request):
    """
    Provide details about child variants(Size) associated with a parent variant(Color) in JSON format.

    Args:
    - request: HTTP request object.

    Returns:
    - JSON response containing details about child variants and the parent variant.
    """
    if request.method == 'GET':
        variant_id = request.GET.get('variant_id')

        if not variant_id:
            return JsonResponse({'error': 'Missing variant_id parameter'})

        try:
            # Retrieve child variants associated with the parent variant ID
            child_variants = ProductChildVariant.objects.filter(parent_variant_id=variant_id)
            # Retrieve data of the parent variant
            parent_variant_data = ProductParentVariant.objects.get(id=variant_id)

            # Prepare data to be sent as JSON
            child_variant_data = []
            for child_variant in child_variants:
                original_price = child_variant.price
                discount_amount = 0
                discount_type = ''

                # Check for discounts in child variant
                if child_variant.discount is not None:
                    if child_variant.discount.is_percentage:
                        discount_percentage = child_variant.discount.disc_value
                        discount_amount = (discount_percentage / 100) * original_price
                        discount_type = '%'
                    else:
                        discount_amount = child_variant.discount.disc_value
                        discount_type = 'Rs.'

                # Check for discounts in parent variant
                elif parent_variant_data.discount is not None:
                    parent_discount = parent_variant_data.discount
                    if parent_discount.is_percentage:
                        discount_percentage = parent_discount.disc_value
                        discount_amount = (discount_percentage / 100) * original_price
                        discount_type = '%'
                    else:
                        discount_amount = parent_discount.disc_value
                        discount_type = 'Rs.'

                # Check for discounts in product
                elif parent_variant_data.product.discount is not None:
                    product_discount = parent_variant_data.product.discount
                    if product_discount.is_percentage:
                        discount_percentage = product_discount.disc_value
                        discount_amount = (discount_percentage / 100) * original_price
                        discount_type = '%'
                    else:
                        discount_amount = product_discount.disc_value
                        discount_type = 'Rs.'

                # Check for discounts in category
                elif parent_variant_data.product.category.discount is not None:
                    category_discount = parent_variant_data.product.category.discount
                    if category_discount.is_percentage:
                        discount_percentage = category_discount.disc_value
                        discount_amount = (discount_percentage / 100) * original_price
                        discount_type = '%'
                    else:
                        discount_amount = category_discount.disc_value
                        discount_type = 'Rs.'

                # Calculate the discounted price
                discounted_price = format(original_price - discount_amount, ".2f")

                # Append child variant data to the list
                child_variant_data.append({
                    'id': child_variant.id,
                    'size': str(child_variant.inventory_child.size),
                    'discount_type': str(discount_type),
                    'discount_amount': str(format(discount_amount, '.2f')),
                    'original_price': str(original_price),
                    'discounted_price': str(discounted_price),
                    'quantity': str(child_variant.inventory_child.quantity)
                })

            # Prepare response data
            response_data = {
                'child_variants': child_variant_data,
                'parent_variant': {
                    'main_image': str(parent_variant_data.main_image.url),
                    'images': [str(image.image.url) for image in parent_variant_data.images.all()],
                    # Add other relevant fields from ProductParentVariant
                }
            }

            # Return the JSON response
            return JsonResponse(response_data)

        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Parent variant not found'})

    else:
        return JsonResponse({'error': 'Invalid request method'})






def prod_add_button(request, cart_id):
    """
    Add a product to the cart and handle inventory checks.

    Args:
    - request: HTTP request object.
    - cart_id: ID of the cart entry to add the product.

    Returns:
    - HTTP redirect response to the single product page.
    """
    cart_entry = get_object_or_404(Cart, id=cart_id)
    product_inventory = get_object_or_404(ProductChildVariantInventory, id=cart_entry.child_variant.inventory_child_id)

    # Check if adding one more to the cart exceeds the inventory quantity
    if cart_entry.quantity + 1 > product_inventory.quantity:
        messages.error(request, "Requirement exceeds the limit. Cannot add more to the cart.")
    else:
        cart_entry.quantity += 1
        cart_entry.save()
        messages.success(request, "Item added to the cart successfully.")

    return redirect(reverse('single_product', args=[cart_entry.product_id]))




def add_address(request):
    """
    Add a new address for the user.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP redirect response to the address page.
    """
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
               
        

    return redirect('address')

def address(request):
    """
    Render the address page with the user's address information.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response rendering the address page with the user's address information.
    """
    if 'username' not in request.session:
        return redirect('login') 
    username = request.session['username']
    addinfo = Address.objects.filter(user__username = username)
    
    
    context = {
        'infos':addinfo,
    }
    
    return render(request, 'address.html',context)

def edit_address(request,id):
    """
    Edit an existing address associated with the logged-in user.

    Args:
    - request: HTTP request object.
    - id: ID of the address to be edited.

    Returns:
    - HTTP response rendering the address page with the updated address information.
    """
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

        # Save the updated address
        address.save()

        return redirect(reverse('address'))  # Change 'address_list' to the URL name of the address list view

    return render(request, 'address.html', {'address': address})




def delete_address(request,id):
    """
    Delete a specific address associated with the user.

    Args:
    - request: HTTP request object.
    - id: ID of the address to be deleted.

    Returns:
    - HTTP response redirecting to the address page after deletion.
    """
    address = get_object_or_404(Address, id=id)
    address.delete()

    return redirect('address')







def wallet(request):
    """
    Display the user's wallet information, including balance and transaction history.

    Args:
    - request: HTTP request object.

    Returns:
    - HTTP response rendering the wallet page with user's wallet information.
    """

    if 'username' not in request.session:
        return redirect('login') 

    username = request.session['username']
    user = User.objects.get(username=username)

    user_wallet, created = Wallet.objects.get_or_create(user=user, defaults={'balance': 0.0})

    show_refunds = request.GET.get('show_refunds', 'all')

    if show_refunds == 'refunds':
        transactions = WalletTranslation.objects.filter(wallet=user_wallet, naration='Refund deposit').order_by('-date')
    else:
        transactions = WalletTranslation.objects.filter(wallet=user_wallet).order_by('-date')

    context = {
        'wallet_id': user_wallet.id,
        'balance': user_wallet.balance,
        'transactions': transactions,
        'show_refunds': show_refunds,
    }

    return render(request, 'wallet.html', context)








def deposit_view(request, wallet_id):
    """
    Handle depositing money into the user's wallet using the Razorpay payment gateway.

    Args:
    - request: HTTP request object.
    - wallet_id: ID of the wallet where the deposit will be made.

    Returns:
    - HTTP response rendering the deposit page or the wallet page with error messages.
    """
    wallet = Wallet.objects.get(pk=wallet_id)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))

        if amount > 0:
            # Razorpay Integration

            receipt_identifier = f'receipt_order_{int(datetime.timestamp(datetime.now()))}'
            client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
            payment_data = {
                'amount': int(amount * 100),  # Amount in paise
                'currency': 'INR',
                'receipt': 'receipt_identifier',  # Replace with a unique identifier
            }

            

            order = client.order.create(payment_data)
            
        
       
            user = User.objects.get(username=request.session['username'])
            user_id = user.id
            Order.objects.create(order_id=order['id'], amount=request.POST.get('amount'),user_id = user_id)
            order_id = order.get('id')




            user = User.objects.get(username = request.session['username'])
            

            context = {
                'wallet': wallet,
                'order_id': order_id,
                'razorpay_amount': int(amount * 100),                                
                'amount': amount,
                'RAZORPAY_KEY' : RAZORPAY_KEY,
                'user': user,

            }

            return render(request, 'deposit_with_razorpay.html', context)

        else:
            messages.error(request, "Invalid deposit amount.")

    return render(request, 'wallet.html', {'wallet': wallet})


 
def withdraw_view(request, wallet_id, amount, order_id):
    """
    Handle withdrawing funds from the user's wallet.

    Args:
    - request: HTTP request object.
    - wallet_id: ID of the wallet from which funds will be withdrawn.
    - amount: Amount to withdraw from the wallet.
    - order_id: ID of the order for which the withdrawal is being made.

    Returns:
    - Redirect to the check_out page after processing the withdrawal.
    """

    try:
        wallet = Wallet.objects.get(pk=wallet_id)
        
        
        if wallet.balance >= amount > 0:
            wallet.withdraw(amount)
            
           
            wallet_transaction = WalletTranslation.objects.create(
                wallet_id=wallet_id,
                amount=amount,
                type='p',
                naration=f'Paid for order#{order_id}'
            )

            messages.success(request, f"Successfully withdrew ${amount}. New balance: Rs{wallet.balance}")
        elif wallet.balance == 0:
            messages.error(request, "Your Wallet is empty!")
        else:
            messages.error(request, "Insufficient funds for withdrawal!")
    except Wallet.DoesNotExist:
        messages.error(request, "Wallet not found.")
    except Exception as e:
        messages.error(request, str(e.get('__all__', [])[0]))
        
        
    
    return redirect('check_out')


        


def view_profile(request):
    """
    View function to display the user's profile.

    Args:
    - request: HTTP request object.

    Returns:
    - Rendered profile page with user information.
    """
    
    if 'username' not in request.session:
        return redirect('login')

    username = request.session['username']

    try:
        info = User.objects.get(username=username)
        referral_obj = Referral.objects.filter(user=info).first()

        if referral_obj:
            referral_code = referral_obj.referral_code
        else:
            referral_code = False

        # Get the active referral scheme
        active_referral_scheme = ReferralRewardSchemes.objects.filter(status=True).first()

        return render(request, 'view_profile.html', {
            'info': info,
            'referral_code': referral_code,
            'active_referral_scheme': active_referral_scheme,
        })

    except User.DoesNotExist:
        return render(request, 'view_profile.html', {'error_message': 'User not found'})




def edit_profile(request):
    if request.method == "POST":
        username = request.session['username']
        
        mobile = request.POST.get('mobile')
        
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        gender = request.POST.get('gender')
       
        birthday = request.POST.get('birthday')
      

        


        user = User.objects.get(username=username)
 

        if username is not None and user.username != username:
            user.username = username

        if firstname is not None and user.firstname != firstname:
            user.firstname = firstname

        if lastname is not None and user.lastname != lastname:
            user.lastname = lastname

        if birthday and user.birthday != birthday:  
            user.birthday = birthday

        if gender is not None and user.gender != gender:
            user.gender = gender

  

        if mobile is not None and user.mobile != mobile:
            user.mobile = mobile

   

    
        user.save()
     
        messages.success(request, 'Profile updated successfully.')
        return redirect('view_profile')

    # If the request method is not POST, handle accordingly (e.g., display the form).
    messages.error(request, 'Failed to update profile. Please try again.')
    return redirect('view_profile')    
        





def order_admin(request):
    """
    View function to display a paginated list of order items in an admin interface.

    Args:
    - request: HTTP request object.

    Returns:
    - Rendered order_admin template with paginated order items.
    """

   
    items_per_page = 10
    
    order_items = OrderItems.objects.order_by(
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

    return render(request, 'order_admin.html', context)


def approve_cancel_refund(request, order_item_id):
    """
    Process the approval or cancellation of a refund request for a specific order item.

    Args:
        request (HttpRequest): The HTTP request object.
        order_item_id (int): The ID of the order item for which the refund request is being processed.

    Returns:
        HttpResponseRedirect: Redirects to the admin order history page after processing the refund request.

    Raises:
        Http404: If the order item with the provided ID does not exist.

    Notes:
        This view function expects a GET request parameter 'refund' containing the refund status,
        which can be either 'Approve' or 'Cancel'.
        - If the refund status is 'Approve', the function updates the order item's refund status,
          deposits the refunded amount back to the user's wallet, creates a wallet transaction record
          for the refund deposit, and handles the inventory return for the refunded product by adding
          the refunded quantity back to the inventory.
        - If the refund status is not 'Approve', an error message indicating an invalid refund status
          is displayed.
    """

    order_item = get_object_or_404(OrderItems, pk=order_item_id)
    order_details = order_item.order
    user_id = order_details.user
    amount = Decimal(order_item.amount)
    product_id = order_item.product_id
    quantity_to_add = order_item.quantity

    if 'refund' in request.GET:
        refund_status = request.GET['refund']
        

        if refund_status:
            order_item.refund = refund_status
            order_item.save()

        if refund_status == 'Approve':


            wallet = Wallet.objects.get(user_id=user_id)
        
            wallet.deposit(amount)

           
            transaction_type = 'r'  
            naration = 'Refund deposit'
            WalletTranslation.objects.create(
                wallet=wallet,
                type=transaction_type,
                amount=amount,
                naration=naration
            )

            inventory_return(product_id,quantity_to_add)

          
            messages.success(request, 'Refund request processed successfully')
        else:
            
            messages.error(request, 'Invalid refund status')

    return redirect('admin_order_history')






class DeliveryStatus:
    CANCELLED = 'Cancelled'
    DELIVERED = 'Delivered'
    PENDING = 'Pending'

def delivery_status(request, order_item_id):
    """
    Update the delivery status for a specific order item.

    Args:
        request (HttpRequest): The HTTP request object.
        order_item_id (int): The ID of the order item for which the delivery status is being updated.

    Returns:
        HttpResponseRedirect: Redirects to the admin order history page after updating the delivery status.

    Raises:
        Http404: If the order item with the provided ID does not exist.

    Notes:
        This view function expects a GET request parameter 'd_status' containing the new delivery status,
        which can be one of the values from the DeliveryStatus enum class (e.g., 'CANCELLED', 'DELIVERED', 'PENDING').
        - If the delivery status is successfully updated, a success message is displayed.
        - If the delivery status is 'Delivered', an invoice is created for the order item.
        - If an invalid delivery status is provided, an error message is displayed.
    """
    order_item = get_object_or_404(OrderItems, pk=order_item_id)

    try:
       
        d_status = escape(request.GET.get('d_status', ''))
       

        if d_status in [DeliveryStatus.CANCELLED, DeliveryStatus.DELIVERED, DeliveryStatus.PENDING]:
            order_item.delivery = d_status
            order_item.save()
            messages.success(request, 'Delivery Status changed successfully')
        if d_status == 'Delivered':
            invoice = Invoice.objects.create(user=order_item.order.user, total_amount=order_item.amount, order_items = order_item)
            
        else:
            messages.error(request, 'Invalid delivery status provided.')
    except Exception as e:
        error_message = str(e) if not hasattr(e, "__all__") else str(e.__all__[0])
        messages.error(request, f'Error updating delivery status: {error_message}')


    return redirect('admin_order_history')


@csrf_exempt
@login_required
def create_razorpay_order(request):
    """
    Create a Razorpay order for payment processing.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response containing the order details if the order creation is successful,
                      otherwise, a JSON response with an error message.

    Raises:
        None

    Notes:
        This view function expects a POST request containing the 'razorpayAmount' parameter,
        which represents the amount to be paid in INR. It creates a Razorpay order with the specified amount,
        currency, and receipt identifier.
        If the order creation is successful, it saves the order details to the database and returns a JSON response
        with the order details, including the order ID, amount, and Razorpay key.
        If an error occurs during the order creation, it returns a JSON response with an error message.
        If the request method is not POST, it returns a JSON response indicating an invalid request method.
    """
    if request.method == 'POST':
        razorpay_amount = request.POST.get('razorpayAmount')
        receipt_identifier = f'receipt_order_{int(datetime.timestamp(datetime.now()))}'
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))
        amount = float(razorpay_amount)
        
        payment_data = {
            'amount': int(amount * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': receipt_identifier,
        }

        try:
            order = client.order.create(payment_data)
            user = request.user
            user_id = user.id

            # Save the order details to your database
            Order.objects.create(order_id=order['id'], amount=amount, user_id=user_id)

            context = {
                'order_id': order['id'],
                'razorpay_amount': int(amount * 100),
                'amount': amount,
                'RAZORPAY_KEY': settings.RAZORPAY_KEY,
                'user': user.username,
            }

            return JsonResponse(context)

        except razorpay.errors.RazorpayError as e:
            return JsonResponse({'success': False, 'message': f"Razorpay Error: {str(e.get('__all__', [])[0])}"})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})



@transaction.atomic
def order_confirmation(request):
    """
    Confirm an order and process the payment.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response indicating the success or failure of the order confirmation
                      and payment processing.

    Raises:
        None

    Notes:
        This view function verifies if the user is logged in and processes the order confirmation
        based on the request method and parameters.
        If the request method is POST, it validates the order details, including the address, total amount,
        coupon code, and payment method. It checks if the user's wallet balance is sufficient for the payment
        and applies any applicable coupon discounts.
        If the payment method is 'wallet', it processes the payment using the user's wallet balance.
        If the payment is successful, it creates the order and deducts the inventory accordingly.
        If the payment method is not 'wallet' (e.g., card payment), it completes the order placement without
        processing any payment.
        If the request method is not POST, it returns a JSON response indicating an invalid request method.
        If any error occurs during the order confirmation or payment processing, it returns a JSON response
        indicating the failure with an error message.
    """
    try:
        if 'username' not in request.session:
            messages.error(request, 'You need to log in first.')
            return JsonResponse({'success': False, 'message': 'User not authenticated'})

        if request.method == 'POST':
            address_id = request.POST.get('addressId')
            amount = request.POST.get('total')
            
            username = request.session['username']
            coupon_code = request.POST.get('couponCode')
            payment_method = request.POST.get('paymentMethod')
           
            
            amount_decimal = Decimal(amount)


            user = User.objects.get(username=username)
            user_id = user.id
            wallet = Wallet.objects.get(user=user_id)
            balance = wallet.balance
            wallet_id = wallet.id

            if balance < amount_decimal:
                messages.error(request, 'Not enough balance')
                return JsonResponse({'success': False, 'message': 'Not enough balance'})

            total_cart_amount = sum(
                (item.child_variant.price - item.child_variant.discount.is_percentage) * item.quantity 
                if item.child_variant.discount and not item.child_variant.discount.is_percentage
                else
                (item.child_variant.price * (1 - item.child_variant.discount.disc_value / 100)) * item.quantity 
                if item.child_variant.discount and item.child_variant.discount.is_percentage
                else
                item.child_variant.price * item.quantity
                for item in Cart.objects.filter(user_id=user_id)
            )

            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)

                    if coupon.coupon_type == '$':
                        total_cart_amount -= coupon.coupon_value  # Subtract the fixed amount
                    elif coupon.coupon_type == '%':
                        total_cart_amount -= total_cart_amount * coupon.coupon_value / 100  # Subtract the percentage

                except Coupon.DoesNotExist:
                    messages.error(request, 'Invalid coupon code.')
                    return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

            if total_cart_amount + 50 != amount_decimal:
                messages.error(request, 'Something went wrong. Please try again later.')
                return JsonResponse({'success': False, 'message': 'Something went wrong'})

            if payment_method == 'wallet':
                payment_method.capitalize()
            else:
                payment_method.upper()

            
            

            payment_details = PaymentDetails.objects.create(
                amount=amount_decimal,
                payment_method=payment_method,
                user_id=user_id
            )

            payment_id = payment_details.id

            order_details = OrderDetails.objects.create(
                amount=amount_decimal,
                status='success',
                payment_id=payment_id,
                address=address_id,
                coupon=coupon_code,
                user_id=user_id,
            )

            order_id = order_details.id

            all_cart_items = Cart.objects.filter(user_id=user_id)

            for cart_item in all_cart_items:
                product_id = cart_item.child_variant.id
                quantity = cart_item.quantity
                product_price = cart_item.child_variant.price

                # Check if there's a discount on the child variant
                if cart_item.child_variant.discount is not None:
                    # Child variant discount
                    child_discount_type = cart_item.child_variant.discount.is_percentage
                    child_discount_value = cart_item.child_variant.discount.disc_value

                    if not child_discount_type :
                        # Subtract the fixed amount from the original price
                        discounted_price_child = product_price - Decimal(child_discount_value)
                    elif child_discount_type:
                        # Calculate the percentage discount and subtract it from the original price
                        discount_percentage_child = Decimal(child_discount_value) / 100
                        discounted_price_child = product_price * (1 - discount_percentage_child)
                    else:
                        # Default to the original price if discount type is not recognized
                        discounted_price_child = product_price
                else:
                    # If no child variant discount, use the original price
                    discounted_price_child = product_price

                # Check if there's a coupon discount
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)

                        if coupon.coupon_type == '$':
                            # Subtract the fixed amount from the discounted child variant price
                            discounted_price = discounted_price_child - Decimal(coupon.coupon_value)
                        elif coupon.coupon_type == '%':
                            # Calculate the percentage discount and subtract it from the discounted child variant price
                            discount_percentage_coupon = Decimal(coupon.coupon_value) / 100
                            discounted_price = discounted_price_child * (1 - discount_percentage_coupon)
                        else:
                            # Default to the discounted child variant price if coupon discount type is not recognized
                            discounted_price = discounted_price_child
                    except Coupon.DoesNotExist:
                        # If coupon is not found, use the discounted child variant price
                        discounted_price = discounted_price_child
                else:
                    # If no coupon, use the discounted child variant price
                    discounted_price = discounted_price_child

                product_amount = discounted_price * Decimal(quantity)

                OrderItems.objects.create(
                    product_id=product_id,
                    order_id=order_id,
                    quantity=quantity,
                    amount=product_amount,
                )
                inventory_reduction(product_id, quantity_to_reduce=quantity)

            if payment_method == 'Wallet':
                
                withdraw_view(request, wallet_id, amount_decimal, order_id)
            
           


                all_cart_items.delete()

                if coupon_code:
                    AppliedCoupon.objects.create(user_id=user_id, coupon_id=coupon.id)
                    coupon = Coupon.objects.get(id=coupon.id)
                    coupon.count += 1
                    coupon.save()
            else:
                all_cart_items.delete()

                if coupon_code:
                    AppliedCoupon.objects.create(user_id=user_id, coupon_id=coupon.id)
                    coupon = Coupon.objects.get(id=coupon.id)
                    coupon.count += 1
                    coupon.save()
                

            messages.success(request, 'Order placed successfully.')
            return JsonResponse({'success': True})

        else:
            return JsonResponse({'success': False, 'message': 'Invalid request method'})

    except Exception as e:
     

        # Set the payment status to 'Failed' in case of an error
        if payment_method != 'cod':
            payment_details.status = 'Failed'
            payment_details.save()

        # Return a JSON response indicating the failure
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again later.'})


def rporder_checkout(request):
    """
    Handle the Razorpay checkout process for placing orders.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response containing order details or error message.

    """

  
    if 'username' not in request.session:
        messages.error(request, 'You need to log in first.')
        return JsonResponse({'error': 'Authentication error'})
    
   

    if request.method == 'POST':
      
     
        try:
            # Retrieve input data
       
            address_id = request.POST.get('addressId')
            amount = request.POST.get('total', 0)

            username = request.session['username']
            coupon_code = request.POST.get('couponCode')
        
            # Store data in session for later use if needed
            request.session['address_id'] = address_id
            request.session['amount'] = amount
            request.session['username'] = username
            request.session['coupon_code'] = coupon_code
       
            amount=float(amount)
            # Validate amount
            if amount <= 0:
                raise ValueError('Invalid amount')
           
            # Generate a unique receipt identifier
            receipt_identifier = f'receipt_order_{int(datetime.timestamp(datetime.now()))}'

            # Create a Razorpay order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))
           
            payment_data = {
                'amount': int(float(amount) * 100),  # Convert Decimal to float for JSON serialization
                'currency': 'INR',
                'receipt': receipt_identifier,
            }
            order = client.order.create(payment_data)

            # Create an Order record in your database
            user = User.objects.get(username=username)
            user_id = user.pk
            email = user.email
            
           
            Order.objects.create(order_id=order['id'], amount=amount, user_id=user_id, Address_id = address_id, coupon_code = coupon_code)
            
            rpay_order_id = order.get('id')
            
            # Prepare context for response
            
      
            
            
            amount_decimal = Decimal(amount)
           
            total_cart_amount = sum(
                (item.child_variant.price - item.child_variant.discount.disc_value) * item.quantity 
                if item.child_variant.discount and not item.child_variant.discount.is_percentage
                else
                (item.child_variant.price * (1 - item.child_variant.discount.disc_value / 100)) * item.quantity 
                if item.child_variant.discount and item.child_variant.discount.is_percentage
                else
                item.child_variant.price * item.quantity
                for item in Cart.objects.filter(user_id=user_id)
            )
       

         
            
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)

                    if coupon.coupon_type == '$':
                        total_cart_amount -= coupon.coupon_value  # Subtract the fixed amount
                    elif coupon.coupon_type == '%':
                        total_cart_amount -= total_cart_amount * coupon.coupon_value / 100  # Subtract the percentage

                except Coupon.DoesNotExist:
                    messages.error(request, 'Invalid coupon code.')
                    return redirect('check_out')
          
        
            if total_cart_amount + 50 != amount_decimal:
                messages.error(request, 'Something went wrong. Please try again later.')
                return redirect('check_out')

            payment_method = 'razorpay' 
          

          
            

            payment_details = PaymentDetails.objects.create(
                amount=amount_decimal,
                payment_method=payment_method,
                user_id=user_id,
                status = 'Failed'
            )

            payment_id = payment_details.id
      

            order_details = OrderDetails.objects.create(
                amount=amount_decimal,
                
                payment_id=payment_id,
                address=address_id,
                coupon=coupon_code,
                user_id=user_id,
            )

            order_id = order_details.id
         

            all_cart_items = Cart.objects.filter(user_id=user_id)

            for cart_item in all_cart_items:
                product_id = cart_item.child_variant.id
                quantity = cart_item.quantity
                product_price = cart_item.child_variant.price

                # Check if there's a discount on the child variant
                if cart_item.child_variant.discount is not None:
                    # Child variant discount
                    child_discount_type = cart_item.child_variant.discount.is_percentage
                    child_discount_value = cart_item.child_variant.discount.disc_value

                    if not child_discount_type:
                        # Subtract the fixed amount from the original price
                        discounted_price_child = product_price - Decimal(child_discount_value)
                    elif child_discount_type:
                        # Calculate the percentage discount and subtract it from the original price
                        discount_percentage_child = Decimal(child_discount_value) / 100
                        discounted_price_child = product_price * (1 - discount_percentage_child)
                    else:
                        # Default to the original price if discount type is not recognized
                        discounted_price_child = product_price
                else:
                    # If no child variant discount, use the original price
                    discounted_price_child = product_price
              
                # Check if there's a coupon discount
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)

                        if coupon.coupon_type == '$':
                            # Subtract the fixed amount from the discounted child variant price
                            discounted_price = discounted_price_child - Decimal(coupon.coupon_value)
                        elif coupon.coupon_type == '%':
                            # Calculate the percentage discount and subtract it from the discounted child variant price
                            discount_percentage_coupon = Decimal(coupon.coupon_value) / 100
                            discounted_price = discounted_price_child * (1 - discount_percentage_coupon)
                        else:
                            # Default to the discounted child variant price if coupon discount type is not recognized
                            discounted_price = discounted_price_child
                    except Coupon.DoesNotExist:
                        # If coupon is not found, use the discounted child variant price
                        discounted_price = discounted_price_child
                else:
                    # If no coupon, use the discounted child variant price
                    discounted_price = discounted_price_child

                product_amount = (discounted_price * Decimal(quantity))
            
                OrderItems.objects.create(
                    product_id=product_id,
                    order_id=order_id,
                    quantity=quantity,
                    amount=product_amount,
                )
                inventory_reduction(product_id, quantity_to_reduce=quantity)

            all_cart_items.delete()
           
            if coupon_code:
                AppliedCoupon.objects.create(user_id=user_id, coupon_id=coupon.id)

          
            return JsonResponse({
                'order_id': rpay_order_id,
                'razorpay_amount': float(amount) * 100,  # Convert Decimal to float for JSON serialization
                'amount': amount,  # Convert Decimal to float for JSON serialization
                'RAZORPAY_KEY': RAZORPAY_KEY,
                'user': username,
                'success': True,
                'email':email 
            })
            
        except Exception as ex:
            # Handle other generic exceptions
            error_message = f'An error occurred: {str(ex)}'
            return JsonResponse({'error': error_message})

    return JsonResponse({'error': 'Invalid request method'})




@csrf_exempt
@transaction.atomic
def checkout_payment_callback(request):
    """
    Handle the payment callback from Razorpay.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: JSON response indicating the result of the payment verification.

    
    """
    try:
        
 

        if request.method == 'POST':
            data = request.POST

            # Initialize a variable to track payment verification status
            payment_verification_failed = False

            try:
                # Verify the payment signature
                client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
                client.utility.verify_payment_signature(request.POST)

            except SignatureVerificationError as e:
               
                payment_verification_failed = True

            # Update the order status in your database
            order = Order.objects.get(order_id=data['razorpay_order_id'])
            order.status = 'paid' if not payment_verification_failed else 'failed'
            order.save()
            user_id = order.user
            
           
            
            

            

            messages.success(request, 'Order placed successfully.')
            return redirect('order_history')

    except Order.DoesNotExist:
        
        return JsonResponse({'error': 'Order not found'}, status=404)

    except ObjectDoesNotExist as e:
        
        return JsonResponse({'error': 'Object not found'}, status=404)

    except Exception as e:
        
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

    finally:
        # Update PaymentDetails status based on payment verification result
        
        last_payment_entry = PaymentDetails.objects.filter(user_id=user_id).latest('created_on')

        last_payment_entry.status = 'Completed' if not payment_verification_failed else 'Failed'
        last_payment_entry.save()

    return JsonResponse({'status': 'failed'}, status=400)





def inventory_reduction(product_id,quantity_to_reduce):
    """
    Reduce the inventory quantity of a product by the specified amount.

    Args:
        product_id (int): The ID of the product.
        quantity_to_reduce (int): The quantity to reduce.

    Returns:
        None

    Raises:
        Http404: If the product is not found.
    """
    
    
  
    product = get_object_or_404(ProductChildVariant, id=product_id)


    product_inventory = product.inventory_child

    
            

    
    if product_inventory.quantity >= quantity_to_reduce:
            product_inventory.quantity -= quantity_to_reduce
            product_inventory.save()
            return  
    else:
            return   
        
def inventory_return(product_id,quantity_to_add):
    
  
    product = get_object_or_404(ProductChildVariant, id=product_id)


    product_inventory = product.inventory_child
            

    
        
    product_inventory.quantity += quantity_to_add
    product_inventory.save()
    return  
           


    






def order_history(request):
    """
    View function to display the order history for a logged-in user.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - Rendered template displaying the order history for the user, including pagination,
      search functionality, date filtering, and failed orders.
    """
    if 'username' not in request.session:
        return redirect('user_login')

    username = request.session['username']

    user_order_details = OrderDetails.objects.filter(
        user__username=username,
    ).exclude(
        payment__status='Failed'  # Use double underscores to access fields in related models
    ).prefetch_related('orderitems_set__product').order_by('-created_at')

    failed_orders = OrderDetails.objects.filter(
        user__username=username,
        payment__status='Failed' 
    ).prefetch_related('orderitems_set__product').order_by('-created_at')

    # Fetching address details
    address_ids = [order.address for order in user_order_details]
    addresses = Address.objects.filter(id__in=address_ids)

    # Search
    search_query = request.GET.get('search')
    if search_query:
        user_order_details = user_order_details.filter(
            Q(orderitems__product__name__icontains=search_query) |
            Q(amount__icontains=search_query)
        )

    # Filtering by date
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        # Assuming start_date and end_date are in the format 'YYYY-MM-DD'
        user_order_details = user_order_details.filter(created_at__date__range=[start_date, end_date])
    elif start_date:
        # Filter only by start_date if end_date is not provided
        user_order_details = user_order_details.filter(created_at__date=start_date)
    elif end_date:
        # Filter only by end_date if start_date is not provided
        user_order_details = user_order_details.filter(created_at__date=end_date)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(user_order_details, 10)  # Show 10 items per page
    try:
        user_order_details = paginator.page(page)
    except PageNotAnInteger:
        user_order_details = paginator.page(1)
    except EmptyPage:
        user_order_details = paginator.page(paginator.num_pages)

    context = {
        'infos': user_order_details,
        'start_date': start_date,
        'end_date': end_date,
        'failed_order_details': failed_orders,
        'addresses': addresses,  # Passing address details to the template
    }

    return render(request, 'order_history.html', context)


def cancel_product(request, order_item_id):
    order_item = OrderItems.objects.get(id=order_item_id)
    order_item.status = 'Cancel'
    order_item.save()
    return redirect('order_history')

def return_product(request, order_item_id):
    order_item = OrderItems.objects.get(id=order_item_id)
    order_item.status = 'Return'
    order_item.save()
    return redirect('order_history')







def create_order(request): 
   
    if request.method == 'POST':
        amount_in_rupees = float(request.POST.get('amount'))
        amount_in_paise = int(amount_in_rupees * 100)
        client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
        order = client.order.create({'amount': amount_in_paise, 'currency': 'INR'})
        
        # Save the order details to your database
        Order.objects.create(order_id=order['id'], amount=request.POST.get('amount'))
        
        return render(request, 'create_order.html', {'order': order})
    return render(request, 'create_order.html')



@csrf_exempt
def payment_callback(request):
    """
    View function to create a new order.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - Rendered template displaying the order details after creation.
    """
   
    
    if request.method == 'POST':
        data = request.POST
        try:
            # Verify the payment signature
            client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
            client.utility.verify_payment_signature(request.POST)
            
            # Update the order status in your database
            order = Order.objects.get(order_id=data['razorpay_order_id'])
            order.status = 'paid'
            order.save()
            user_id = order.user

            # Fetch wallet and deposit amount
            wallet = Wallet.objects.get(user_id = user_id)
            wallet_id = wallet.id
            amount = Decimal(order.amount)

            # Update the wallet balance
            wallet = Wallet.objects.get(pk=wallet_id)
            wallet.deposit(amount)

            
            transaction_type = 'r'  
            naration = 'Razorpay deposit'
            WalletTranslation.objects.create(
                wallet=wallet,
                type=transaction_type,
                amount=amount,
                naration=naration
            )

            messages.success(request, f"Payment successful. Amount: Rs.{amount}")

            
            return redirect('wallet')
        except SignatureVerificationError as e:
           
            print(f"Signature verification failed: {e}")
        except Order.DoesNotExist:
            
            print("Order not found in the database.")
        except Exception as e:
           
            print(f"An error occurred: {e}")

    return JsonResponse({'status': 'failed'})



@csrf_exempt
def handle_razorpay_payment(request):
    """
    View function to handle Razorpay payment callback.

    Parameters:
    - request: The HTTP request object containing payment data.

    Returns:
    - JSON response indicating the status of the payment processing.
    """
  
    if request.method == 'POST':
        data = request.POST
        razorpay_payment_id = data.get('razorpay_payment_id')
        order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')

        # Verify the payment signature
        client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
        try:
            client.utility.verify_payment_signature(data.dict(), signature)
          
            wallet = Wallet.objects.get(user__username = request.session['username'])
            wallet_id = wallet.id
            wallet = Wallet.objects.get(pk=wallet_id)
            amount = Decimal(data.get('amount')) / 100  
            wallet.deposit(amount)
            transaction_type = 'r'  # Received
            naration = 'Razorpay Deposit'
            WalletTranslation.objects.create(
                wallet=wallet,
                type=transaction_type,
                amount=amount,
                naration=naration
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'error': str(e.get('__all__', [])[0])})
    return JsonResponse({'status': 'failed', 'error': 'Invalid request method'})


def generate_referral(request):
    """
    View function to generate a referral code for the logged-in user.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - Redirects to the view profile page after generating the referral code.
    """
    username = request.session['username']
    user = User.objects.get(username=username)
    user_id = user.id
    referral_code = generate_referral_code(user_id)

   
    referral_obj = Referral(user=user, referral_code=referral_code)
    referral_obj.save()
    
    return redirect('view_profile')

def generate_referral_code(user_id):
    # Combine user ID with a random string of length 3 to ensure uniqueness
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    # Extract last 5 characters of the user ID
    user_id_part = str(user_id)[-5:]
    # Combine both parts to form the 5-character referral code
    referral_code = user_id_part + random_part
    return referral_code


def referral_signup(request,code):
    active_referral_scheme = ReferralRewardSchemes.objects.filter(status=True).first()

    return render(request, 'user_signup.html', {'code':code, 'active_referral_scheme':active_referral_scheme})






def invoice_pdf_view(request, invoice_id):
    """
    View function to generate and serve a PDF invoice for a given invoice ID.

    Parameters:
    - request: The HTTP request object.
    - invoice_id (int): The ID of the invoice for which the PDF is generated.

    Returns:
    - HttpResponse: Response containing the generated PDF invoice.
    """
    invoice = Invoice.objects.get(id=invoice_id)

    order_items = invoice.order_items
    address_id = order_items.order.address
    shipping_address = Address.objects.get(id=address_id)
    grand_total =  order_items.amount 
    tax_rate = 0.1  
    tax = grand_total * tax_rate
    subtotal = grand_total - tax

    context = {
        'invoice': invoice,
        'order_items': order_items,
        'customer_address': shipping_address,
        'subtotal': subtotal,
        'tax': tax,
        'grand_total': grand_total,
    }

    # Render the HTML template
    template_path = 'invoice.html'
    template = get_template(template_path)
    html_content = template.render(context)

  
    css_string = '@page { size: A4 portrait; margin: 1cm; }'
    pdf_file = HTML(string=html_content).write_pdf(stylesheets=[CSS(string=css_string)])



   
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=invoice_{invoice.id}.pdf'

    return response




def history_edit_address(request, address_id):
    """
    View function to edit a shipping address from the order history.

    Parameters:
    - request: The HTTP request object.
    - address_id (int): The ID of the address to edit.

    Returns:
    - HttpResponseRedirect: Redirects to the order history page after editing.
    """
    try:
        address = Address.objects.get(pk=address_id)
        if request.method == 'POST':
            address.name = request.POST.get('name')
            address.address_line_1 = request.POST.get('address_l1')
            address.address_line_2 = request.POST.get('address_l2')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            address.country = request.POST.get('country')
            address.pincode = request.POST.get('pincode')
            address.mobile = request.POST.get('mobile')
            address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('order_history')
        return redirect('order_history') 
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
        return redirect('order_history')
    

def failed_create_order(request):
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')
        
        try:
            order_item = OrderItems.objects.get(id=order_item_id)
        except OrderItems.DoesNotExist:
            return JsonResponse({'error': 'Order item not found'}, status=404)
        
        # Create an order instance
        order = Order.objects.create(
            order_id=generate_unique_order_id(),  # You need to implement this function to generate a unique order ID
            amount=order_item.amount,
            status='pending',  # Assuming the initial status is 'pending'
            user=request.user,  # Assuming you have authenticated users
            Address_id=request.user.address.id,  # Assuming you have an Address model related to the user
            coupon_code=order_item.coupon_code,
        )

        return JsonResponse({'success': True, 'order_id': order.order_id})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)





def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)



def continue_payment_view(request):
    if request.method == 'GET':
        quantity = request.GET.get('quantity')
        amount = request.GET.get('amount')
        order_item_id = request.GET.get('oi_id')

        if quantity is not None and amount is not None and order_item_id is not None:
            quantity = int(quantity)
            amount = Decimal(amount)

            if quantity > 0 and amount > 0:
                try:
                    # Fetch OrderItems instance
                    order_item = OrderItems.objects.get(pk=order_item_id)
                    # Fetch the related OrderDetails instance
                    order_detail = order_item.order
                    # Update payment status to 'success'
                    order_detail.payment.status = 'success'
                    order_detail.payment.save()

                    receipt_identifier = f'receipt_order_{int(datetime.timestamp(datetime.now()))}'
                    client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
                    payment_data = {
                        'amount': int(amount * 100),  # Amount in paise
                        'currency': 'INR',
                        'receipt': receipt_identifier,  # Replace with a unique identifier
                    }

                    order = client.order.create(payment_data)

                    user = User.objects.get(username=request.session['username'])
                    user_id = user.id
                    Order.objects.create(order_id=order['id'], amount=amount, user_id=user_id)
                    order_id = order.get('id')

                    context = {
                        'order_id': order_id,
                        'razorpay_amount': int(amount * 100),
                        'amount': amount,
                        'RAZORPAY_KEY': RAZORPAY_KEY,
                        'user': user,
                    }

                    return render(request, 'continue_payment_deposit_with_razorpay.html', context)
                except OrderItems.DoesNotExist:
                    messages.error(request, "Order does not exist.")
                    return redirect('order_history')
                except OrderDetails.DoesNotExist:
                    messages.error(request, "Order details do not exist.")
                    return redirect('order_history')
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return redirect('order_history')
            else:
                messages.error(request, "Invalid quantity or amount.")
                return redirect('order_history')

    return redirect('order_history')


@csrf_exempt
def continue_payment_callback(request):
    """
    View function to create a new order.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - Rendered template displaying the order details after creation.
    """
   
    
    if request.method == 'POST':
        data = request.POST
        try:
            # Verify the payment signature
            client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
            client.utility.verify_payment_signature(request.POST)
            
            # Update the order status in your database
            order = Order.objects.get(order_id=data['razorpay_order_id'])
            order.status = 'paid'
            order.save()
            

            messages.success(request, f"Payment successful!")

            
            return redirect('order_history')
        except SignatureVerificationError as e:
           
            print(f"Signature verification failed: {e}")
        except Order.DoesNotExist:
            
            print("Order not found in the database.")
        except Exception as e:
           
            print(f"An error occurred: {e}")

    return JsonResponse({'status': 'failed'})









        





