from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, ProductImage
from products.signals import generate_embedding_from_image


class Command(BaseCommand):
    help = 'Generate embeddings for products that don\'t have embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Generate embedding for a specific product ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate embeddings for all products without embeddings',
        )

    def handle(self, *args, **options):
        if options['product_id']:
            # Generate embedding for specific product
            try:
                product = Product.objects.get(productId=options['product_id'])
                self.generate_embedding_for_product(product)
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Product with ID {options["product_id"]} not found')
                )
        elif options['all']:
            # Generate embeddings for all products without embeddings
            products_without_embeddings = Product.objects.filter(embedding__isnull=True)
            self.stdout.write(f'Found {products_without_embeddings.count()} products without embeddings')
            
            for product in products_without_embeddings:
                self.generate_embedding_for_product(product)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --product-id or --all')
            )

    def generate_embedding_for_product(self, product):
        """Generate embedding for a specific product"""
        self.stdout.write(f'Processing product: {product.name}')
        
        # Get the first product image
        first_image = product.images.first()
        if not first_image or not first_image.image:
            self.stdout.write(
                self.style.WARNING(f'No image found for product: {product.name}')
            )
            return
        
        try:
            # Generate embedding using Style2Vec
            embedding = generate_embedding_from_image(first_image.image.path)
            if embedding:
                # Update the product with the generated embedding
                product.embedding = embedding
                product.save(update_fields=['embedding'])
                self.stdout.write(
                    self.style.SUCCESS(f'Generated embedding for product: {product.name}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to generate embedding for product: {product.name}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating embedding for product {product.name}: {e}')
            ) 