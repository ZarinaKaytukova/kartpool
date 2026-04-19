from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreViewSet, FavoriteViewSet 

router = DefaultRouter()
router.register(r'stores', StoreViewSet)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('api/', include(router.urls)),
]