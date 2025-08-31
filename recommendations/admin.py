from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Avg
from recommendations.models import StyleImage, ImageSegment, StyleEmbedding, RecommendationLog, Feedback


class ImageSegmentInline(admin.TabularInline):
    model = ImageSegment
    extra = 0
    readonly_fields = ('segmentId', 'get_segment_preview')
    fields = ('get_segment_preview', 'category_type', 'image_url')
    autocomplete_fields = ['category_type']
    
    @admin.display(description='Segment Preview')
    def get_segment_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 4px; object-fit: cover;" />',
                obj.image_url.url
            )
        return "No image"


class StyleEmbeddingInline(admin.StackedInline):
    model = StyleEmbedding
    extra = 0
    readonly_fields = ('embeddingId', 'created_at', 'get_embedding_info')
    fields = ('get_embedding_info', 'created_at')
    can_delete = False
    
    @admin.display(description='Embedding Info')
    def get_embedding_info(self, obj):
        if obj.embeddings is not None and len(obj.embeddings):
            return format_html(
                '<span style="color: #27ae60;">✓ Generated</span><br/>'
                '<small>Vector length: {} dimensions</small>',
                len(obj.embeddings) if obj.embeddings else 0
            )
        return format_html('<span style="color: #e74c3c;">✗ Not generated</span>')


class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    readonly_fields = ('feedbackId', 'user', 'is_good')
    fields = ('user', 'is_good')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Feedback is created by users, not admin


@admin.register(StyleImage)
class StyleImageAdmin(admin.ModelAdmin):
    inlines = [ImageSegmentInline]
    
    list_display = (
        'get_user_info', 'get_image_preview', 'get_segments_count', 
        'uploaded_at', 'get_recommendations_count'
    )
    
    list_filter = ('uploaded_at',)
    search_fields = ['user__username', 'user__email', 'styleImageId']
    autocomplete_fields = ['user']
    readonly_fields = ('styleImageId', 'uploaded_at', 'get_full_image')
    
    fieldsets = (
        ('Image Details', {
            'fields': ('user', 'image_url', 'get_full_image')
        }),
        ('System Info', {
            'fields': ('styleImageId', 'uploaded_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='User')
    def get_user_info(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return mark_safe('<span style="color: #999;">Anonymous</span>')
    
    @admin.display(description='Preview')
    def get_image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="80" height="80" style="border-radius: 8px; object-fit: cover; cursor: pointer;" '
                'onclick="window.open(\'{}\')"/>',
                obj.image_url.url, obj.image_url.url
            )
        return "No Image"
    
    @admin.display(description='Full Image')
    def get_full_image(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.image_url.url
            )
        return "No Image"
    
    @admin.display(description='Segments', ordering='segments_count')
    def get_segments_count(self, obj):
        count = obj.segments.count()
        if count > 0:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">{} segments</span>',
                count
            )
        return format_html('<span style="color: #e74c3c;">No segments</span>')
    
    @admin.display(description='Recommendations')
    def get_recommendations_count(self, obj):
        count = obj.recommendationlog_set.count()
        if count > 0:
            return f"{count} logs"
        return "No recommendations"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').annotate(segments_count=Count('segments'))


@admin.register(ImageSegment)
class ImageSegmentAdmin(admin.ModelAdmin):
    inlines = [StyleEmbeddingInline]
    
    list_display = (
        'get_style_image_info', 'category_type', 
        'get_segment_preview', 'get_embedding_status'
    )
    
    list_filter = ('category_type', 'style_image__uploaded_at')
    search_fields = (
        'segmentId', 'style_image__styleImageId', 
        'style_image__user__username', 'category_type__name'
    )
    autocomplete_fields = ['style_image', 'category_type']
    readonly_fields = ('segmentId', 'get_segment_preview')
    
    fieldsets = (
        ('Segment Details', {
            'fields': ('style_image', 'category_type', 'image_url', 'get_segment_preview')
        }),
        ('System Info', {
            'fields': ('segmentId',),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Style Image')
    def get_style_image_info(self, obj):
        url = reverse('admin:recommendations_styleimage_change', args=[obj.style_image.styleImageId])
        user_info = obj.style_image.user.username if obj.style_image.user else 'Anonymous'
        return format_html('<a href="{}">{}</a>', url, user_info)
    
    @admin.display(description='Preview')
    def get_segment_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 8px; object-fit: cover;" />',
                obj.image_url.url
            )
        return "No image"
    
    @admin.display(description='AI Embedding')
    def get_embedding_status(self, obj):
        try:
            embedding = obj.styleembedding
            if embedding.embeddings is not None and len(embedding.embeddings):
                return format_html('<span style="color: #27ae60;">✓ Generated</span>')
            return format_html('<span style="color: #f39c12;">✓ Created, no data</span>')
        except StyleEmbedding.DoesNotExist:
            return format_html('<span style="color: #e74c3c;">✗ Missing</span>')


@admin.register(StyleEmbedding)
class StyleEmbeddingAdmin(admin.ModelAdmin):
    list_display = (
        'get_source_info', 'get_embedding_status', 'created_at'
    )
    
    list_filter = ('created_at',)
    search_fields = (
        'embeddingId', 'segment__segmentId', 'product__name', 
        'product__sku', 'segment__style_image__user__username'
    )
    autocomplete_fields = ['segment', 'product']
    readonly_fields = ('embeddingId', 'created_at', 'get_embedding_info')
    
    fieldsets = (
        ('Source', {
            'fields': ('segment', 'product'),
            'description': 'Either segment OR product should be set, not both'
        }),
        ('Embedding Data', {
            'fields': ('embeddings', 'get_embedding_info'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('embeddingId', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Source')
    def get_source_info(self, obj):
        if obj.segment:
            return format_html(
                'Segment: <a href="{}">{}</a>',
                reverse('admin:recommendations_imagesegment_change', args=[obj.segment.segmentId]),
                obj.segment.category_type.name
            )
        elif obj.product:
            return format_html(
                'Product: <a href="{}">{}</a>',
                reverse('admin:products_product_change', args=[obj.product.productId]),
                obj.product.name
            )
        return mark_safe('<span style="color: #e74c3c;">No source</span>')
    
    @admin.display(description='Status')
    def get_embedding_status(self, obj):
        if obj.embeddings  is not None and len(obj.embeddings):
            vector_length = len(obj.embeddings) if obj.embeddings is not None else 0
            return format_html(
                '<span style="color: #27ae60;">✓ Generated</span><br/>'
                '<small>{} dimensions</small>',
                vector_length
            )
        return format_html('<span style="color: #e74c3c;">✗ No data</span>')
    
    @admin.display(description='Embedding Details')
    def get_embedding_info(self, obj):
        if obj.embeddings is not None and len(obj.embeddings):
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
                '<strong>Vector Length:</strong> {} dimensions<br/>'
                '<strong>Sample Values:</strong> {}...'
                '</div>',
                len(obj.embeddings),
                str(obj.embeddings[:5]) if obj.embeddings else 'None'
            )
        return "No embedding data"


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    inlines = [FeedbackInline]
    
    list_display = (
        'get_user_info', 'get_style_image_info', 
        'get_products_count', 'get_feedback_summary', 'created_at'
    )
    
    list_filter = ('created_at',)
    search_fields = (
        'logId', 'user__username', 'user__email',
        'style_image__styleImageId', 'recommended_products__name'
    )
    autocomplete_fields = ['user', 'style_image', 'recommended_products']
    readonly_fields = ('logId', 'created_at')
    
    filter_horizontal = ('recommended_products',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('user', 'style_image', 'recommended_products')
        }),
        ('System Info', {
            'fields': ('logId', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='User')
    def get_user_info(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Style Image')
    def get_style_image_info(self, obj):
        url = reverse('admin:recommendations_styleimage_change', args=[obj.style_image.styleImageId])
        return format_html('<a href="{}">View Image</a>', url)
    
    @admin.display(description='Products', ordering='products_count')
    def get_products_count(self, obj):
        count = obj.recommended_products.count()
        return f"{count} products"
    
    @admin.display(description='Feedback')
    def get_feedback_summary(self, obj):
        total_feedback = obj.feedbacks.count()
        positive_feedback = obj.feedbacks.filter(is_good=True).count()
        
        if total_feedback == 0:
            return mark_safe('<span style="color: #999;">No feedback</span>')
        
        percentage = (positive_feedback / total_feedback) * 100
        
        if percentage >= 70:
            color = '#27ae60'
        elif percentage >= 40:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}% positive</span><br/>'
            '<small>({}/{})</small>',
            color, percentage, positive_feedback, total_feedback
        )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'style_image').annotate(
            products_count=Count('recommended_products')
        )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_info', 'get_recommendation_info', 
        'get_feedback_display', 'get_recommendation_date'
    )
    
    list_filter = ('is_good', 'log__created_at')
    search_fields = (
        'user__username', 'user__email', 'log__logId',
        'log__user__username'
    )
    autocomplete_fields = ['log', 'user']
    readonly_fields = ('feedbackId',)
    
    @admin.display(description='User')
    def get_user_info(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Recommendation')
    def get_recommendation_info(self, obj):
        url = reverse('admin:recommendations_recommendationlog_change', args=[obj.log.logId])
        return format_html('<a href="{}">View Log</a>', url)
    
    @admin.display(description='Feedback')
    def get_feedback_display(self, obj):
        if obj.is_good:
            return format_html('<span style="color: #27ae60; font-size: 16px;">✓ Positive</span>')
        return format_html('<span style="color: #e74c3c; font-size: 16px;">✗ Negative</span>')
    
    @admin.display(description='Recommendation Date', ordering='log__created_at')
    def get_recommendation_date(self, obj):
        return obj.log.created_at
