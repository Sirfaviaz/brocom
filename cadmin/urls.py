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
from django.urls import path, include, re_path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve

urlpatterns = [
       
    path('admin_index', views.admin_index,name='admin_index'),
    path('get_filtered_data/', views.get_filtered_data, name='get_filtered_data'),
    path('get_filtered_data_amount/', views.get_filtered_data_amount, name='get_filtered_data_amount'),
    path('get_filtered_data_user/', views.get_filtered_data_user, name='get_filtered_data_user'),
    path('chart-data/<str:time_range>/', views.chart_data, name='chart_data'),
    path('fetch_product_details/', views.fetch_product_details, name='fetch_product_details'),
    
    #User management 
    path('admin_user', views.admin_user, name = 'admin_user'),
    path('user_block/<str:id>', views.user_block, name = 'user_block'),
    path('user_search',views.user_search,name='user_search'),

    # Product management
    path('admin_product',views.admin_product,name='admin_product'),
    path('add_product', views.add_product, name = 'add_product'),
    path('search_product',views.search_product,name= 'search_product'),
    path('edit_product/<str:id>', views.edit_product, name='edit_product'),
    path('edit_main_image/<int:product_id>',views.edit_main_image,name = 'edit_main_image'),
    path('edit_image<int:product_id>/<int:image_id>/',views.edit_image,name = 'edit_image'),
    path('product_inactive/<str:id>', views.product_inactive, name='product_inactive'),
    path('admin_product_create',views.admin_product_create, name = 'admin_product_create'),
    # path('variant/form/<int:inventory_id>/', views.ProductVariantFormView.as_view(), name='product_variant_form'),
    path('variant_edit_image<int:variant_id>/<int:image_id>/',views.variant_edit_image,name = 'variant_edit_image'),
    path('get_child_variant_sizes/', views.get_child_variant_sizes, name='get_child_variant_sizes'),
    path('get_parent_variants',views.get_parent_variants,name = 'get_parent_variants'),
    path('view_product_variants/<int:product_id>',views.view_product_variants,name = 'view_product_variants'),
    path('add_product_child_variant',views.add_product_child_variant, name = 'add_product_child_variant'),
    path('add_product_parent_variant',views.add_product_parent_variant, name = 'add_product_parent_variant'),
    path('edit_product_child_variant/<int:child_variant_id>/', views.edit_product_child_variant, name='edit_product_child_variant'),
    path('edit_product_parent_variant',views.edit_product_parent_variant, name = 'edit_product_parent_variant'),
    
    
    # Category Management
    path('admin_category',views.admin_category,name='admin_category'),
    path('add_category',views.add_category,name='add_category'),
    path('search_category',views.search_category,name= 'search_category'),
    path('edit_category/<str:id>',views.edit_category,name='edit_category'),
    path('category_inactive/<str:id>', views.category_inactive, name='category_inactive'),

    #Inventory Management
    path('admin_inventory', views.admin_inventory, name = 'admin_inventory'),
    path('add_inventory', views.add_inventory, name = 'add_inventory'),
    path('search_inventory',views.search_inventory, name = 'search_inventory'),
    path('inventory_inactive/<str:id>', views.inventory_inactive, name = 'inventory_inactive'),
    path('edit_inventory/<int:inventory_id>', views.edit_inventory, name = 'edit_inventory'),
     #Inventory Management-variants
     path('variant-inventory/<str:id>', views.variant_inventory_display, name='variant_inventory_display'),
     path('edit_parent_variant/<int:variant_id>/', views.edit_parent_variant, name='edit_parent_variant'),
     path('add_parent_variant/', views.add_parent_variant, name='add_parent_variant'),
     path('edit_child_variant/<int:child_variant_id>/', views.edit_child_variant, name='edit_child_variant'),
     path('add_child_variant/', views.add_child_variant, name='add_child_variant'),

    #Coupon Management
    path('admin_coupon', views.admin_coupon, name = 'admin_coupon'),
    path('add_coupon', views.add_coupon, name = 'add_coupon'),
    path('edit_coupon/<str:id>', views.edit_coupon, name = 'edit_coupon'),


    #Order Management
    path('admin_order_history', views.admin_order_history, name ='admin_order_history'),



    # Referral Management

    path('referral_schemes_view', views.referral_schemes_view, name= 'referral_schemes_view'),
    path('edit_referral', views.edit_referral, name= 'edit_referral'),
    path('change_status', views.change_status, name= 'change_status'),
    path('create_referral_reward_scheme', views.create_referral_reward_scheme, name='create_referral_reward_scheme'),
    # discount
    path('admin_discount', views.admin_discount, name='admin_discount'),
    path('add_new_discount', views.add_new_discount, name='add_new_discount'),
    path('create_discount_category', views.create_discount_category, name='create_discount_category'),
    path('create_discount_product', views.create_discount_product, name='create_discount_product'),
    path('create_discount_parent_variant', views.create_discount_parent_variant, name = 'create_discount_parent_variant'),
    path('create_discount_child_variant',views.create_discount_child_variant, name='create_discount_child_variant'),
    path('edit_discount/<int:discount_id>/', views.edit_discount, name='edit_discount'),

    #banner
    path('admin_banner', views.admin_banner, name='admin_banner' ),
    path('add_banner', views.add_banner, name='add_banner'),
    path('create_banner', views.create_banner, name= 'create_banner'),

    


    
    
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, }), ]