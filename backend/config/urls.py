"""Rutas principales del backend."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.graph.urls")),
    path('api/', include('api.urls')),
]
