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
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('store')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)