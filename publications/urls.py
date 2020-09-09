from django.urls import path
from . import views


urlpatterns = [

    path("", views.publication_index, name="publication_index"),

    path("<int:pk>/", views.publication_detail, name="publication_detail"),

]