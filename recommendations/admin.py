from django.contrib import admin
from django.utils.html import format_html

from recommendations.models import StyleImage, ImageSegment, StyleEmbedding, RecommendationLog, Feedback


class ImageSegmentInline(admin.TabularInline):
    model = ImageSegment
    extra = 1
    autocomplete_fields = ['category_type']


class StyleEmbeddingInline(admin.StackedInline):  # Stacked might be better here for the long vector
    model = StyleEmbedding
    extra = 0
    can_delete = False
    readonly_fields = ('created_at',)


class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'is_good')
    fields = ('user', 'is_good')


# --- ModelAdmin Registrations ---

@admin.register(StyleImage)
class StyleImageAdmin(admin.ModelAdmin):
    inlines = [ImageSegmentInline]
    list_display = ('styleImageId', 'user', 'get_thumbnail', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ['user__username', 'styleImageId']
    autocomplete_fields = ['user']

    @admin.display(description='Image')
    def get_thumbnail(self, obj):
        if obj.image_url:
            return format_html(f'<img src="{obj.image_url.url}" width="100" />')
        return "No Image"


@admin.register(ImageSegment)
class ImageSegmentAdmin(admin.ModelAdmin):
    # This model doesn't need to be managed separately as it's part of StyleImage.
    # We register it just in case direct access is needed.
    inlines = [StyleEmbeddingInline]
    list_display = ('segmentId', 'style_image', 'category_type')
    autocomplete_fields = ['style_image', 'category_type']
    search_fields = ['segmentId', 'style_image__styleImageId']


@admin.register(StyleEmbedding)
class StyleEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('embeddingId', 'segment', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ['embeddingId', 'segment__segmentId', 'product__name']
    autocomplete_fields = ['segment', 'product']
    # The 'embeddings' field is a JSON blob, so it's not very useful here,
    # but we can show its presence.
    readonly_fields = ('embeddings', 'created_at')


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    inlines = [FeedbackInline]
    list_display = ('logId', 'user', 'style_image', 'created_at')
    list_filter = ('created_at',)
    search_fields = ['logId', 'user__username', 'style_image__styleImageId']
    autocomplete_fields = ['user', 'style_image', 'recommended_products']
    # recommended_products is a ManyToManyField, so autocomplete_fields is great here
    filter_horizontal = ('recommended_products',)  # An alternative to autocomplete for M2M fields


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedbackId', 'log', 'user', 'is_good')
    list_filter = ('is_good',)
    autocomplete_fields = ['log', 'user']
