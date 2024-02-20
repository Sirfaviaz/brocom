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
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('view_cart/', views.view_cart, name = 'view_cart'),
    path('update-quantity/', views.update_quantity, name='update_quantity'),
    path('toggle_product/', views.toggle_product, name='toggle_product'),
    path('delete_button/<int:cart_id>', views.delete_button, name='delete_button'),
    path('add_button/<int:cart_id>',views.add_button, name='add_button'),
    path('sub_button/<int:cart_id>',views.sub_button, name='sub_button'),
    
    path('check_out', views.check_out, name='check_out'),
    path('check_out_delete_address/<int:id>',views.check_out_delete_address, name = 'check_out_delete_address'),
    path('check_out_edit_address/<int:id>',views.check_out_edit_address, name = 'check_out_edit_address'),
    path('check_out_add_address',views.check_out_add_address, name = 'check_out_add_address'),

    path('coupon_admin', views.coupon_admin,name='coupon_admin'),   
    path('coupon_create', views.coupon_create, name='coupon_create'), 
    path('coupon_edit/<str:id>', views.coupon_edit, name='coupon_edit'),
    path('coupon_delete/<str:id>', views.coupon_delete, name='coupon_delete'),

    path('select_address_ajax/', views.select_address_ajax, name='select_address_ajax'),
    path('validate_coupon/', views.validate_coupon, name='validate_coupon'),

]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
