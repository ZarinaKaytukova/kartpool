from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from .models import Store
from .services import get_nearby_stores_within
from .serializers import (StoreSerializer, NearbyStoreSerializer)

# Create your views here.

class StoreView(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def list(self, request):
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lng')
        category = self.request.query_params.get('category', None)

        radius = 10 # in kilometres
        number_of_stores_to_return = 100
        
        stores = get_nearby_stores_within(
            latitude=float(latitude),
            longitude=float(longitude),
            km=radius,
            limit=number_of_stores_to_return
        )
        if category:
            stores = [store for store in stores if store.category == category]

        stores_data = NearbyStoreSerializer(stores, many=True)
        return Response(stores_data.data)


class StorePageView(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'stores/index.html'
    
    def list(self, request):
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lng')
        category = self.request.query_params.get('category', None)

        radius = 10 # in kilometres
        number_of_stores_to_return = 100
        
        stores = get_nearby_stores_within(
            latitude=float(latitude),
            longitude=float(longitude),
            km=radius,
            limit=number_of_stores_to_return
        )
        
        if category:
            stores = [store for store in stores if store.category == category]
            
        categories = Store.CATEGORY_CHOICES

        stores_data = NearbyStoreSerializer(stores, many=True)
        return Response({
            'stores': stores_data.data,
            'categories': categories,
            'selected_category': category
        })

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления избранными магазинами.
    Доступ только для авторизованных пользователей.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """Возвращает только избранное текущего пользователя"""
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('store').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Создание записи в избранном с дополнительными проверками безопасности.
        """
        # Проверка входных данных
        store_id = request.data.get('store_id')
        
        if not store_id:
            return Response(
                {"error": "store_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка существования магазина
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {"error": f"Store with id {store_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверка, не превышен ли лимит избранного (опционально)
        user_favorites_count = Favorite.objects.filter(user=request.user).count()
        MAX_FAVORITES = 50
        if user_favorites_count >= MAX_FAVORITES:
            return Response(
                {"error": f"Maximum favorites limit ({MAX_FAVORITES}) reached"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
        except IntegrityError:
            # Запись уже существует
            return Response(
                {"detail": "This store is already in your favorites."},
                status=status.HTTP_409_CONFLICT
            )
        
        headers = self.get_success_headers(serializer.data)
        
        # Логирование действия (для аудита безопасности)
        self._log_favorite_action(request.user, store, 'added')
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        """Автоматически связывает запись с текущим пользователем"""
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление записи из избранного с проверкой прав.
        """
        instance = self.get_object()
        
        # Дополнительная проверка: только владелец может удалить
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to delete this favorite"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        store = instance.store
        self.perform_destroy(instance)
        
        # Логирование действия
        self._log_favorite_action(request.user, store, 'removed')
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _log_favorite_action(self, user, store, action):
        """
        Логирование действий пользователя для аудита безопасности.
        В production можно использовать Django logging или сохранять в БД.
        """
        import logging
        logger = logging.getLogger('favorites')
        logger.info(
            f"User '{user.username}' {action} store '{store.name}' (id: {store.id}) "
            f"to favorites at {timezone.now()}"
        )