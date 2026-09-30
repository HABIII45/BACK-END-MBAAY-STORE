"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/',include("boutiques.urls")),
    path("api/auth/",include("utilisateurs.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/livraisons/", include("livraisons.urls")),
    path("api/abonnements/", include("abonnements.urls")),
    path("api/paiements/", include("paiements.urls")),
    path("api/produits/", include("produits.urls")),
    path("api/paniers/", include("paniers.urls"),),
    path("api/livraison/", include("livraisons.urls"),),
    path("api/commandes/",include("commandes.urls")),
    path("api/informations-agricoles/",include("informations.urls")),
    
]
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)


