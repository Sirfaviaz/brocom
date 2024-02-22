"""
URL configuration for Brocom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings




urlpatterns = [
    path('', views.user_login, name= 'user_login'),
    path('user_signup', views.user_signup, name= 'user_signup'),
    path('view_signup', views.view_signup, name='view_signup'),
    path('index', views.index, name= 'index'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp', views.verify_otp, name='verify_otp'),
    path('user_logout', views.user_logout, name='user_logout'),
    path('not_verified',views.not_verified, name='not_verified'),
    path('click_here',views.click_here, name='click_here'),
    path('change_email', views.change_email, name = 'change_email'),
    path('forgot_password', views.forgot_password, name= 'forgot_password'),
    path('enter_mail',views.enter_mail, name= 'enter_mail'),
    path('reset_password', views.reset_password, name='reset_password'),
   
    
    #product view
    path('product_list', views.product_list, name = 'product_list'),
    path('list_product_search', views.list_product_search, name = 'list_product_search'),
    path('product_filter/', views.product_filter, name='product_filter'),
    path('single_product/<int:product_id>', views.single_product, name='single_product'),
    path('prod_add_button/<int:cart_id>',views.prod_add_button, name='prod_add_button'),
    path('product_rating', views.product_rating, name = 'product_rating'),
    # path('get_variant_info',views.get_variant_info, name = 'get_variant_info'),
    path('api/child_variant_details/', views.child_variant_details, name='child_variant_details'),

  

    

      # user management
    path('admin_login', views.admin_login,name='admin_login'),
    path('user_admin', views.user_admin,name='user_admin'),
    path('admin_logout',views.admin_logout,name='admin_logout'),
    path('create', views.create, name='create'),
 
    path('update/<str:id>', views.update, name='update'),
    path('delete/<str:id>', views.delete, name='delete'),
    path('search', views.search, name='search'),
    
    # User edit
    path('view_profile', views.view_profile, name='view_profile'),
    path('edit_profile', views.edit_profile, name = 'edit_profile'),

    # User Address
    path('address', views.address, name = 'address'),
    path('add_address', views.add_address, name = 'add_address'),
    path('edit_address/<str:id>/', views.edit_address, name = 'edit_address'),
    path('delete_address/<int:id>/',views.delete_address, name = 'delete_address'),

    #wallet
    path('wallet', views.wallet, name = 'wallet'),
    path('deposit_view/<int:wallet_id>/', views.deposit_view, name = 'deposit_view'),
    

    # check out
    path('order_admin',views.order_admin, name = 'order_admin' ),
    path('approve_cancel_refund/<int:order_item_id>/', views.approve_cancel_refund, name='approve_cancel_refund'),
    path('delivery_status/<int:order_item_id>/', views.delivery_status, name='delivery_status'),
    # path('combined_orders/', views.combined_order_list, name='combined_order_list'),

    # order_confirmation
    path('order_confirmation',views.order_confirmation, name = 'order_confirmation'),

    #order_history
    path('order_history', views.order_history, name = 'order_history'),
    path('cancel_product/<int:order_item_id>/', views.cancel_product, name='cancel_product'),
    path('return_product/<int:order_item_id>/', views.return_product, name='return_product'),
    path('invoice/<int:invoice_id>', views.invoice_pdf_view, name='invoice'),
    path('history_edit_address/<int:address_id>/', views.history_edit_address, name='history_edit_address'),

    path('create_order/', views.create_order, name='create_order'),
    path('payment_callback/', views.payment_callback, name='payment_callback'),
    path('handle_razorpay_payment/', views.handle_razorpay_payment, name='handle_razorpay_payment'),

    path('create_razorpay_order/', views.create_razorpay_order, name='create_razorpay_order'),

    path('continue-payment/', views.continue_payment_view, name='continue_payment_view'),
    path('continue_payment_callback', views.continue_payment_callback, name='continue_payment_callback'),

    #rpaycheckout
    path('rporder_checkout/', views.rporder_checkout, name='rporder_checkout'),
    path('checkout_payment_callback/', views.checkout_payment_callback, name='checkout_payment_callback'),


    # generate_referral
    path('generate_referral',views.generate_referral, name='generate_referral'),
    path('rsu/<str:code>/', views.referral_signup,name = 'rsu')

   
    
]
urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)