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
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
        #Inventory management
    path('inventory_admin', views.inventory_admin,name='inventory_admin'),
    path('inventory_create', views.inventory_create, name='inventory_create'),
    path('inventory_update/<str:id>', views.inventory_Update, name='inventory_update'),
    path('inactive_inventory/<str:id>', views.inactive_inventory, name='inactive_inventory'),
    path('inventory_search', views.inventory_search, name='inventory_search'),

    path('add_variant/', views.add_variant, name='add_variant'),
   

    #category management
    path('category_admin', views.category_admin,name='category_admin'),
    path('category_create', views.category_create, name='category_create'),
    path('category_update/<str:id>', views.category_Update, name='category_update'),
    path('inactive_category/<str:id>', views.inactive_category, name='inactive_category'),
    path('category_search', views.category_search, name='category_search'),

    #Product management
    path('product_admin', views.product_admin,name='product_admin'),
    # path('product_create', views.product_create, name='product_create'),
    path('product_update/<str:id>', views.product_update, name='product_update'),
    path('inactive_product/<str:id>', views.inactive_product, name='inactive_product'),
    path('product_search', views.product_search, name='product_search'),
    path('update_main_image/<int:product_id>/', views.update_main_image, name='update_main_image'),
    path('update_image/<int:product_id>/<int:image_id>/', views.update_image, name='update_image'),
    # path('add_productimage/', views.add_productimage, name='add_productimage'),
    
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)