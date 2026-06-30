from django.contrib import admin
from django.urls import path

from trials import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index),
    path("postgres/studies/", views.postgres_studies),
    path("mongo/studies/", views.mongo_studies),
    path("comparison/", views.comparison),
]
