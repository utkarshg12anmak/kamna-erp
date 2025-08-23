from django.urls import path
from . import admin_views

urlpatterns = [
    path('preview/<int:pli_id>/', admin_views.preview_price, name='sales_admin_preview_price'),
]
