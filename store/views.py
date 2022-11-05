from django.db.models.aggregates import Count
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from . import models
from . import serializers
from .filters import ProductFilter
from .pagination import DefaultPageNumberPagination


class ProductViewSet(ModelViewSet):
    queryset = models.Product.objects.all().select_related('collection').prefetch_related('images')
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_class = ProductFilter
    pagination_class = DefaultPageNumberPagination
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ['title', 'description']
    ordering = ['unit_price', 'unit_price']
    ordering_fields = ['id', 'unit_price', 'last_update']


class CollectionViewSet(ModelViewSet):
    queryset = models.Collection.objects.annotate(products_count=Count('products'))
    serializer_class = serializers.CollectionSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def destroy(self, request, *args, **kwargs):
        if models.Product.objects.filter(collection_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)


class ProductImageViewSet(ModelViewSet):
    serializer_class = serializers.ProductImageSerializer

    def get_queryset(self):
        return models.ProductImage.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}