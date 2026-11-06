from django.urls import path

from . import views

app_name = "tableau"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("login/", views.connexion, name="connexion"),
    path("logout/", views.deconnexion, name="deconnexion"),
    path("search/", views.recherche, name="recherche"),
    path("donations/", views.dons, name="dons"),
    path("messages/", views.boite, name="messages"),
    path("messages/<int:pk>/", views.message, name="message"),
    path("settings/", views.reglages, name="reglages"),
    path("account/", views.compte, name="compte"),
    path("<slug:code>/", views.liste, name="liste"),
    path("<slug:code>/new/", views.edition, name="ajouter"),
    path("<slug:code>/<int:pk>/", views.edition, name="modifier"),
    path("<slug:code>/<int:pk>/delete/", views.supprimer, name="supprimer"),
]
