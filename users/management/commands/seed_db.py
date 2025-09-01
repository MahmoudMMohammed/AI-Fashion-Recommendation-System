import csv
import os
import random
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from faker import Faker
import numpy as np

from fashionRecommendationSystem import settings
from recommendations.models import ImageSegment, StyleImage
# Import all your models
from users.models import User, UserProfile
from products.models import Category, ProductSize, Product, ProductImage  # <--- IMPORT ProductImage
from orders.models import Order, OrderItem
from wallet.models import Wallet

# --- Configuration ---
NUM_USERS = 10
NUM_SIZES = 4
NUM_ORDERS_PER_USER = 3
MAX_ITEMS_PER_ORDER = 5
EMBEDDING_DIM = 2048

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
        size_labels = ['S', 'M', 'L', 'XL', 'One Size']
        for label in size_labels:
            size, _ = ProductSize.objects.get_or_create(label=label)
            sizes.append(size)
        self.stdout.write(self.style.SUCCESS(f'{len(sizes)} sizes ensured in database.'))

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
        self.stdout.write('Seeding products from CSV file...')
        # Define the path to the dataset relative to the project's BASE_DIR
        dataset_path = os.path.join(settings.BASE_DIR, 'dataset')
        csv_file_path = os.path.join(dataset_path, 'inventory_subset.csv')
        images_dir_path = os.path.join(dataset_path, 'images')

        product_count = 0
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # --- Find or Create the Category ---
                    category_name = row['category'].strip().capitalize()
                    if not category_name:
                        self.stdout.write(self.style.WARNING(f"Skipping row with empty category. SKU: {row['sku']}"))
                        continue

                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'description': f'A collection of {category_name} items.'}
                    )
                    if created:
                        self.stdout.write(f"  Created new category: {category_name}")

                    # --- Create the Product ---
                    product, created = Product.objects.get_or_create(
                        sku=row['sku'].strip(),
                        defaults={
                            'name': row['name'].strip(),
                            'base_price': row['price'].strip(),
                            'gender': row['gender'].strip(),
                            # Add fake data for other fields
                            'description': faker.paragraph(nb_sentences=5),
                            'discount_percent': random.choice([0, 5, 10, 15, 20]),
                            'stock_quantity': random.randint(10, 100)
                            # 'embedding' is left null by default
                        }
                    )

                    if not created:
                        self.stdout.write(
                            self.style.WARNING(f"Product with SKU {product.sku} already exists. Skipping."))
                        continue

                    # --- Attach Category and Sizes ---
                    product.categories.add(category)
                    product.sizes.set(random.sample(sizes, k=random.randint(1, len(sizes))))

                    # --- Find and Attach the Image ---
                    image_filename = row['image'].split('/')[-1]
                    image_path = os.path.join(images_dir_path, image_filename)

                    if os.path.exists(image_path):
                        # Create the ProductImage instance first, without the image file.
                        product_image = ProductImage.objects.create(
                            product=product,
                            alt_text=f"Image for {product.name}"
                        )

                        # Open the file and read its content.
                        with open(image_path, 'rb') as img_f:
                            image_content = img_f.read()

                        # Wrap the content in a ContentFile object.
                        django_content_file = ContentFile(image_content)

                        # Call the save() method on the ImageField of the instance.
                        # This is the correct way to do it.
                        product_image.image.save(image_filename, django_content_file, save=True)
                    else:
                        self.stdout.write(self.style.WARNING(f"Image not found for SKU {product.sku}: {image_path}"))

                    product_count += 1

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: The file was not found at {csv_file_path}"))
            self.stdout.write(self.style.ERROR("Please make sure the 'dataset' directory is in your project root."))
            return  # Exit the command
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {product_count} products from the CSV.'))

        # # --- 5. Create Orders and OrderItems ---
        # self.stdout.write('Creating Orders...')
        # for user in users:  # Use the list of non-admin users for orders
        #     for _ in range(NUM_ORDERS_PER_USER):
        #         order = Order.objects.create(user=user, status=random.choice([s[0] for s in Order.Status.choices]))
        #
        #         num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
        #         order_products = random.sample(products, k=num_items)
        #
        #         for product in order_products:
        #             if product.is_in_stock(1):
        #                 OrderItem.objects.create(
        #                     order=order, product=product,
        #                     quantity=random.randint(1, 3), unit_price=product.get_final_price()
        #                 )
        #
        # self.stdout.write(self.style.SUCCESS('Orders created.'))
        self.stdout.write(self.style.SUCCESS('Database seeding complete!'))
