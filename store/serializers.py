from decimal import Decimal

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from . import models


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = ['id', 'title', 'products_count']

    products_count = serializers.IntegerField(read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return models.ProductImage.objects.create(product_id=self.context['product_id'], **validated_data)

    class Meta:
        model = models.ProductImage
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    collection = serializers.SlugRelatedField(
        slug_field='title',
        queryset=models.Collection.objects
    )
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = models.Product
        fields = [
            'id',
            'title',
            'description',
            'slug',
            'unit_price',
            'collection',
            'last_update',
            'images',
        ]

    def validate_title(self, value):
        if models.Product.objects.filter(slug=slugify(value)).exists():
            raise serializers.ValidationError('A product with this title is already exists.')
        return value


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item):
        return cart_item.product.unit_price * cart_item.quantity

    class Meta:
        model = models.CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    # id = serializers.UUIDField(read_only=True)
    cartitems = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum([item.product.unit_price * item.quantity for item in cart.cartitems.all()])

    class Meta:
        model = models.Cart
        fields = ['id', 'cartitems', 'total_price']
        read_only_fields = ['id']


class AddCartItemSerializer(serializers.ModelSerializer):
    # product_id = serializers.IntegerField()

    def save(self, **kwargs):
        product = self.validated_data['product']
        quantity = self.validated_data['quantity']
        cart_id = self.context['cart_id']
        try:
            cart_item = models.CartItem.objects.get(product=product, cart_id=cart_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except models.CartItem.DoesNotExist:
            self.instance = models.CartItem.objects.create(**self.validated_data, cart_id=cart_id)
        return self.instance
        
    class Meta:
        model = models.CartItem
        fields = ['id', 'product', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ['quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = models.OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    orderitems = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = models.Order
        fields = ['id', 'user', 'placed_at', 'orderitems']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not models.Cart.objects.filter(id=cart_id).exists():
            raise serializers.ValidationError('No cart with given ID was found')

        if models.CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('The given cart has no items')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            order = models.Order.objects.create(user=self.context['user'])

            cartitems = models.CartItem.objects.filter(cart_id=self.validated_data['cart_id'])

            orderitems = [
                models.OrderItem(
                    order=order,
                    product=cartitem.product,
                    quantity=cartitem.quantity,
                    unit_price=cartitem.product.unit_price,
                ) for cartitem in cartitems
            ]

            models.OrderItem.objects.bulk_create(orderitems)

            models.Cart.objects.get(id=self.validated_data['cart_id']).delete()

            return order