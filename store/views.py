from django.db.models.aggregates import Count
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
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
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        return models.ProductImage.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    queryset = models.Cart.objects.prefetch_related('cartitems__product')
    serializer_class = serializers.CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return models.CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .prefetch_related('product')


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateOrderSerializer(
            data=request.data,
            context={'user': self.request.user},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = serializers.OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateOrderSerializer
        return serializers.OrderSerializer
        
    def get_queryset(self):
        user =self.request.user
        if user.is_staff:
            return models.Order.objects.all().prefetch_related('orderitems')
        return models.Order.objects.filter(user=user).prefetch_related('orderitems')