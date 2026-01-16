from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('services', views.services, name='services'),
    path('service_details/<slug:slug>', views.service_details, name='service_details'),
    path('gallery', views.gallery, name='gallery'),
    path('gallery_single/<str:pk>/', views.gallery_single, name='gallery_single'),
    path('agents', views.agents, name='agents'),
    path('contact', views.contact, name='contact'),
    path('dialog', views.dialog, name='dialog'),
]
