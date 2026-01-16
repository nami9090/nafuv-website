from django.contrib import admin
from .models import homeSilde,whoWeareHome, whoWeareHomeimage,servicesModel,serviceDetail,agentsModel,address,callUs,emailUs,Galleries,GalleryImages
# Register your models here.
class ServiceAdmin(admin.ModelAdmin):
	list_display = ("title", "details", "iskingdom")
	prepopulated_fields = {"slug":("title",)}

class AgentAdmin(admin.ModelAdmin):
	list_display = ("name", "role", "image_pic")

admin.site.register(homeSilde)
admin.site.register(whoWeareHome)
admin.site.register(whoWeareHomeimage)
admin.site.register(servicesModel, ServiceAdmin)
admin.site.register(serviceDetail)
admin.site.register(agentsModel, AgentAdmin)
admin.site.register(address)
admin.site.register(callUs)
admin.site.register(emailUs)
admin.site.register(Galleries)
admin.site.register(GalleryImages)