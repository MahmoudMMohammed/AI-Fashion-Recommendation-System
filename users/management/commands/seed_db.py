import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
import numpy as np

from recommendations.models import ImageSegment, StyleImage
# Import all your models
from users.models import User, UserProfile
from products.models import Category, ProductSize, Product, ProductImage  # <--- IMPORT ProductImage
from orders.models import Order, OrderItem
from wallet.models import Wallet

# --- Configuration ---
NUM_USERS = 10
NUM_SIZES = 4
NUM_PRODUCTS = 50
NUM_IMAGES_PER_PRODUCT = 3
NUM_ORDERS_PER_USER = 3
MAX_ITEMS_PER_ORDER = 5
EMBEDDING_DIM = 1024

AI_CATEGORIES = [
    'top', 'skirt', 'leggings', 'dress', 'outer', 'pants', 'bag',
    'neckwear', 'headwear', 'eyeglass', 'belt', 'footwear', 'hair',
    'skin', 'face'
]


class Command(BaseCommand):
    help = 'Seeds the database with realistic test data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        faker = Faker()

        # --- 1. Clean the Database ---
        self.stdout.write('Deleting old data...')
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Wallet.objects.all().delete()
        UserProfile.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        ImageSegment.objects.all().delete()
        StyleImage.objects.all().delete()
        Category.objects.all().delete()
        ProductSize.objects.all().delete()
        User.objects.all().delete()

        # --- 2. Create Essential Categories and Sizes ---
        self.stdout.write('Creating Categories and Sizes...')
        categories = []
        for cat_name in AI_CATEGORIES:
            category, _ = Category.objects.get_or_create(
                name=cat_name.capitalize(),
                defaults={'description': f'Products related to {cat_name}'}
            )
            categories.append(category)

        sizes = []
        size_labels = ['S', 'M', 'L', 'XL']
        for label in size_labels:
            size, _ = ProductSize.objects.get_or_create(label=label)
            sizes.append(size)

        # --- 3. Create Users ---
        self.stdout.write('Creating Users, Profiles, and Wallets...')
        users = []
        # Create a superuser for easier admin access
        User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password123',
            first_name='Admin', last_name='User'
        )

        # Create regular users
        for _ in range(NUM_USERS):
            user = User.objects.create_user(
                username=faker.unique.user_name(), email=faker.unique.email(), password='password123',
                first_name=faker.first_name(), last_name=faker.last_name()
            )
            users.append(user)
        test_user = User.objects.create_user(
            username='Test',
            email='test@example.com',
            password='password123',  # Use a known password
            first_name='Test',
            last_name='User'
        )
        users.append(test_user)

        # Create Profiles and Wallets for all created users (including superuser)
        for user in User.objects.all():
            UserProfile.objects.get_or_create(user=user,
                                              defaults={'avg_style_vector': np.random.rand(EMBEDDING_DIM).tolist()})
            Wallet.objects.get_or_create(user=user, defaults={
                'balance': faker.pydecimal(left_digits=3, right_digits=2, positive=True)})

        self.stdout.write(self.style.SUCCESS(f'{User.objects.count()} users created.'))

        # --- 4. Create Products and their Images ---
        self.stdout.write('Creating Products and Product Images...')
        products = []
        for _ in range(NUM_PRODUCTS):
            # Create the Product instance first
            fake_embedding = np.random.rand(EMBEDDING_DIM).tolist()

            product = Product.objects.create(
                sku=faker.ean(length=13),
                name=faker.bs().capitalize(),
                description=faker.paragraph(nb_sentences=5),
                base_price=faker.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=10, max_value=200),
                discount_percent=random.choice([0, 10, 15, 20, 25]),
                stock_quantity=random.randint(0, 100),
                embedding=fake_embedding
            )

            # --- NEW LOGIC: Create associated ProductImage objects ---
            for i in range(random.randint(1, NUM_IMAGES_PER_PRODUCT)):
                # We assign a fake path. Django won't try to access it unless you
                # render it in a template or API response that hits the filesystem.
                # For DB seeding, this is sufficient and fast.
                fake_image_path = f"products/fake_image_{product.productId}_{i}.jpg"
                ProductImage.objects.create(
                    product=product,
                    image=fake_image_path,
                    alt_text=f"Image {i + 1} for {product.name}"
                )

            # Add Many-to-Many relationships
            product.categories.set(random.sample(categories, k=random.randint(1, 3)))
            product.sizes.set(random.sample(sizes, k=random.randint(1, len(sizes))))
            products.append(product)

        self.stdout.write(self.style.SUCCESS(f'{NUM_PRODUCTS} products created with images.'))

        # --- 5. Create Orders and OrderItems ---
        self.stdout.write('Creating Orders...')
        for user in users:  # Use the list of non-admin users for orders
            for _ in range(NUM_ORDERS_PER_USER):
                order = Order.objects.create(user=user, status=random.choice([s[0] for s in Order.Status.choices]))

                num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
                order_products = random.sample(products, k=num_items)

                for product in order_products:
                    if product.is_in_stock(1):
                        OrderItem.objects.create(
                            order=order, product=product,
                            quantity=random.randint(1, 3), unit_price=product.get_final_price()
                        )

        self.stdout.write(self.style.SUCCESS('Orders created.'))
        self.stdout.write(self.style.SUCCESS('Database seeding complete!'))