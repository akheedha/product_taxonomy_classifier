"""
Serializers for Classification Results and Curator Reviews.
"""

from rest_framework import serializers
from products.serializers import ProductSummarySerializer
from taxonomy.serializers import CategorySummarySerializer
from taxonomy.models import Category
from .models import ClassificationResult


class ClassificationResultListSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    predicted_category = CategorySummarySerializer(read_only=True)

    class Meta:
        model = ClassificationResult
        fields = [
            'id',
            'product',
            'job',
            'predicted_category',
            'confidence',
            'alternative_categories',
            'extracted_attributes',
            'needs_manual_review',
            'status',
            'error_message',
            'reviewed_by',
            'approved',
            'created_at',
            'updated_at',
        ]


class ClassificationResultDetailSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    predicted_category = CategorySummarySerializer(read_only=True)

    class Meta:
        model = ClassificationResult
        fields = '__all__'


class ClassificationReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for approving or overriding a classification result."""
    category_id = serializers.CharField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = ClassificationResult
        fields = ['approved', 'reviewed_by', 'category_id']

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        if category_id:
            category = Category.objects.filter(id=category_id).first()
            if category:
                instance.predicted_category = category
                instance.confidence = 1.0  # Curator override sets 100% confidence
                instance.needs_manual_review = False

        if 'approved' in validated_data:
            instance.approved = validated_data['approved']
            if instance.approved:
                instance.needs_manual_review = False

        if 'reviewed_by' in validated_data:
            instance.reviewed_by = validated_data['reviewed_by']

        instance.save()
        return instance

    def to_representation(self, instance):
        return ClassificationResultDetailSerializer(instance, context=self.context).data
