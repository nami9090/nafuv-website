from django.shortcuts import render, get_object_or_404
from .models import homeSilde, whoWeareHome, servicesModel, agentsModel, whoWeareHomeimage, Galleries, GalleryImages
from django.template import loader
from django.http import HttpResponse

# Create your views here.
def index(request):
    template = loader.get_template('index.html')
    slideHome = homeSilde.objects.all()
    whoWeare = whoWeareHome.objects.prefetch_related('images').all()
    homeService = servicesModel.objects.all()
    teams = agentsModel.objects.all()
    singleItem =whoWeareHomeimage.objects.all()
    context = {
        'slideHome':slideHome,
        'whoWeare':whoWeare,
        'homeService':homeService,
        'teams': teams,
        'singleItem':singleItem
    }
    return HttpResponse(template.render(context, request))

def about(request):
    template = loader.get_template('about.html')
    value = 'none'
    value2 = 'block'
    about = whoWeareHome.objects.all()
    context = {
        'about':about,
        'value':value,
        'value2':value2
    }
    return HttpResponse(template.render(context, request))

def services(request):
    template = loader.get_template('services.html')
    services = servicesModel.objects.all()
    context = {
        'services':services
    }
    return HttpResponse(template.render(context, request))

def service_details(request, slug):
    template = loader.get_template('service-details.html')
    # singleService = get_object_or_404(servicesModel, title=pk)
    OneService = servicesModel.objects.get(slug=slug)
    serviceD = OneService.detail.all()
    services = servicesModel.objects.all()
    context = {
        'services':services,
        'singleService':OneService,
        'serviceD':serviceD
    }
    return HttpResponse(template.render(context, request))

def gallery(request):
    template = loader.get_template('gallery.html')
    galleries = Galleries.objects.all()
    context = {
        'galleries':galleries
    }
    return HttpResponse(template.render(context, request))

def gallery_single(request, pk):
    template = loader.get_template('gallery-single.html')
    getGallery = get_object_or_404(Galleries, title=pk)
    gallery = getGallery.images.all()
    context = {
        'singleGallery':getGallery,
        'gallery':gallery
    }
    return HttpResponse(template.render(context, request))

def agents(request):
    template = loader.get_template('agents.html')
    teams = agentsModel.objects.all()
    context = {
        'teams':teams
    }
    return HttpResponse(template.render(context, request))

def contact(request):
    template = loader.get_template('contact.html')
    return HttpResponse(template.render())

def dialog(request):
    template = loader.get_template('dialog.html')
    return HttpResponse(template.render())