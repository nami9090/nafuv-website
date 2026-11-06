from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about", views.about, name="about"),
    path("services", views.services, name="services"),
    path("service_details/<slug:slug>", views.service_details, name="service_details"),
    path("gallery", views.gallery, name="gallery"),
    path("gallery_single/<int:id>/", views.gallery_single, name="gallery_single"),
    path("agents", views.agents, name="agents"),
    path("contact", views.contact, name="contact"),
    path("donate", views.donate, name="donate"),
    path("donate/thank-you", views.donate_thanks, name="donate_thanks"),
    # Old address, redirected to the donation page
    path("dialog", views.dialog, name="dialog"),
]
