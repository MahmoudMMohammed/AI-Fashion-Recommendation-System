from pgvector.django import L2Distance, CosineDistance
from ..models import StyleEmbedding, Product, ImageSegment, StyleImage, RecommendationLog
from django.db import transaction

def get_recommendations(user_segment_id, top_n=10):
    """
    Finds the top N most similar products to a user's style segment using Cosine Distance
    and logs the recommendation.
    """
    try:
        # 1. Get the embedding for the user's style segment
        user_embedding_obj = StyleEmbedding.objects.get(segment__segmentId=user_segment_id)
        user_embedding = user_embedding_obj.embeddings
        user_style_image = user_embedding_obj.segment.style_image
        user = user_style_image.user
        segment = user_embedding_obj.segment  # already linked
    except StyleEmbedding.DoesNotExist:
        print(f"❌ No StyleEmbedding found for segment {user_segment_id}")
        return []

    # 2. Query the database for similar products
    # Using pgvector's CosineDistance for similarity search on Product.embedding
    recommended_products = Product.objects.filter(
        embedding__isnull=False,  # Only consider products with embeddings
        categories=segment.category_type
    ).annotate(
        # Calculate the distance between the user's embedding and product embeddings
        # CosineDistance(a, b) = 1 - cos(theta), so smaller values are more similar
        distance=CosineDistance('embedding', user_embedding)
    ).order_by(
        'distance'  # Order from smallest distance (most similar) to largest
    )[:top_n]

    # 3. Log the recommendations
    with transaction.atomic():
        # re-use the existing log (or create it if this is the first category)
        recommendation_log, _ = RecommendationLog.objects.get_or_create(
            user=user,
            style_image=user_style_image
        )
        # append the newly-found products; duplicates are ignored automatically
        recommendation_log.recommended_products.add(*recommended_products)

        print(f"✅ Recommendations logged for user: {user.username}")
        print(f"📊 Found {len(recommended_products)} recommendations")

    return list(recommended_products)


def get_recommendations_by_embedding(user_embedding, top_n=10):
    """
    Finds the top N most similar products directly from a given embedding vector
    using Cosine Distance.
    """
    recommended_products = Product.objects.filter(
        embedding__isnull=False
    ).annotate(
        distance=CosineDistance('embedding', user_embedding)
    ).order_by(
        'distance'
    )[:top_n]
    
    return list(recommended_products)


def debug_recommendations(user_segment_id, top_n=10):
    """
    Debug function to see what's happening in the recommendation process
    """
    print(f"🔍 Debugging recommendations for segment: {user_segment_id}")
    
    try:
        # 1. Get the user's embedding
        user_embedding_obj = StyleEmbedding.objects.get(segment__segmentId=user_segment_id)
        user_embedding = user_embedding_obj.embeddings
        print(f"✅ User embedding found: {len(user_embedding)} dimensions")
        
        # 2. Check available products
        total_products = Product.objects.count()
        products_with_embeddings = Product.objects.filter(embedding__isnull=False).count()
        print(f"📦 Products: {total_products} total, {products_with_embeddings} with embeddings")
        
        if products_with_embeddings == 0:
            print("❌ No products with embeddings found!")
            return []
        
        # 3. Get recommendations with distance info
        recommended_products = Product.objects.filter(
            embedding__isnull=False
        ).annotate(
            distance=CosineDistance('embedding', user_embedding)
        ).order_by('distance')[:top_n]
        
        print(f"🎯 Found {len(recommended_products)} recommendations:")
        for i, product in enumerate(recommended_products, 1):
            print(f"   {i}. {product.name} (SKU: {product.sku}) - Distance: {product.distance:.4f}")
        
        return list(recommended_products)
        
    except StyleEmbedding.DoesNotExist:
        print(f"❌ No StyleEmbedding found for segment {user_segment_id}")
        return []
    except Exception as e:
        print(f"❌ Error in debug_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return []
