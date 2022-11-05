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