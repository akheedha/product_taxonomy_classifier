from django.contrib import admin
from .models import Category, Attribute, AttributeValue


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'level', 'parent', 'full_name', 'attribute_count')
    list_filter = ('level',)
    search_fields = ('id', 'name', 'full_name')
    autocomplete_fields = ('parent',)
    ordering = ('level', 'name')

    @admin.display(description="Attributes Count")
    def attribute_count(self, obj):
        return obj.attributes.count()


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'categories_count', 'values_count')
    search_fields = ('id', 'name')
    filter_horizontal = ('categories',)
    ordering = ('name',)

    @admin.display(description="Linked Categories")
    def categories_count(self, obj):
        return obj.categories.count()

    @admin.display(description="Allowed Values")
    def values_count(self, obj):
        return obj.values.count()


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'attribute_name', 'attribute')
    list_filter = ('attribute',)
    search_fields = ('id', 'value', 'attribute__name', 'attribute__id')
    autocomplete_fields = ('attribute',)
    ordering = ('attribute', 'value')

    @admin.display(description="Attribute Name", ordering="attribute__name")
    def attribute_name(self, obj):
        return obj.attribute.name
