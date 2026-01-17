from datetime import date
from django.db import models

# Create your models here.
class homeSilde(models.Model):
    image_pic = models.ImageField(upload_to='images/')
    span = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    details = models.CharField(max_length=100)

    def __self__(self):
        return self.title
        

class whoWeareHome(models.Model):
    title = models.CharField(max_length=100)
    first_paragraph = models.CharField(max_length=1000)
    second_paragraph = models.CharField(max_length=1000)
    
    def __str__(self):
        return self.title
    
class whoWeareHomeimage(models.Model):
    whoWeare = models.ForeignKey(whoWeareHome, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="images/")

    def __str__(self):
        return f"Image for {self.whoWeare.title}"

class servicesModel(models.Model):
    title = models.CharField(max_length=100)
    details = models.CharField(max_length=10000000)
    iskingdom = models.BooleanField(default=False)
    image_pic = models.ImageField(upload_to='images/')
    slug = models.SlugField(default="", null=False)
    
    def __str__(self):
        return f"service {self.title}"
    
class serviceDetail(models.Model):
    service = models.ForeignKey(servicesModel, related_name='detail', on_delete=models.CASCADE)
    completeName = models.CharField(max_length=100)
    yearOfTaken = models.DateField()
    encore_vivant = models.BooleanField(default=False)
    yearOfDeath = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='images/')
    def __str__(self):
        if self.encore_vivant:
            annees = date.today().year - self.yearOfTaken.year
            return f"{self.completeName}, au pouvoir depuis {self.yearOfTaken.year} ({annees} ans de règne)"
        elif self.yearOfDeath:
            return f"{self.completeName} de {self.yearOfTaken.year} à {self.yearOfDeath.year} soit {self.yearOfDeath.year - self.yearOfTaken.year} ans de règne"
        else:
            return f"{self.completeName}, au pouvoir depuis {self.yearOfTaken.year}"

class Galleries(models.Model):
    title = models.CharField(max_length=100)
    subtile = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)
    image = models.ImageField(upload_to='images/')
    def __str__(self):
        return self.title

class GalleryImages(models.Model):
    gallery = models.ForeignKey(Galleries, related_name='images', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/')
    description = models.CharField(max_length=10000)
    slug = models.SlugField(default="", null=False)
    
    # def __str__(self):
    #     return f"Image de {self.gallery.title}"
    
class agentsModel(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    image_pic = models.ImageField(upload_to='images/')
    lien_1 = models.CharField(max_length=100000)
    lien_2 = models.CharField(max_length=100000)
    lien_3 = models.CharField(max_length=100000)
    lien_4 = models.CharField(max_length=100000)

    def __str__(self):
        return f'agent {self.name}'

class address(models.Model):
    name = models.CharField(max_length=100)

class callUs(models.Model):
    name = models.CharField(max_length=100)

class emailUs(models.Model):
    name = models.CharField(max_length=100)