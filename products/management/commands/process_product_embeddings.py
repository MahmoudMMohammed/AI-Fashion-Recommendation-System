import os
import subprocess
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from products.models import Product
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Generates embeddings for products that are missing them. Can process a single product or all products.'

    def add_arguments(self, parser):
        # --- Argument to select a specific mode ---
        parser.add_argument(
            '--productId',
            type=str,
            help='The UUID of a specific product to process.'
        )
        parser.add_argument(
            '--all',
            action='store_true',  # This makes it a flag: --all
            help='Process all products where embedding is null.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of products to process when using --all.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-processing of products that already have an embedding.'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        product_id = options['productId']
        process_all = options['all']
        limit = options['limit']
        force = options['force']

        if not product_id and not process_all:
            raise CommandError("You must specify either --productId <ID> or --all.")

        if product_id:
            try:
                products_to_process = [Product.objects.get(productId=product_id)]
                self.stdout.write(f"--- Processing single product: {product_id} ---")
            except Product.DoesNotExist:
                raise CommandError(f'Product with ID "{product_id}" does not exist.')
        else:  # --all was specified
            self.stdout.write(self.style.SUCCESS("--- Processing all products with missing embeddings ---"))

            products = Product.objects.filter(embedding__isnull=True)
            if force:
                self.stdout.write(self.style.WARNING("--force flag detected. Processing ALL products."))
                products = Product.objects.all()

            if limit:
                products = products[:limit]
                self.stdout.write(self.style.SUCCESS(f"Limiting to the first {limit} products."))

            products_to_process = list(products)  # Convert queryset to list for progress bar

        if not products_to_process:
            self.stdout.write(self.style.SUCCESS("No products to process."))
            return

        # Initialize counters for the summary
        success_count = 0
        skipped_count = 0
        error_count = 0

        # Get paths once
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
        venv_python = os.path.join(project_root, 'style2vec_env', 'Scripts', 'python.exe')
        script_path = os.path.join(project_root, 'recommendations', 'ai_services', 'style2vec_singleton.py')

        if not os.path.exists(venv_python) or not os.path.exists(script_path):
            raise CommandError(
                f"Python interpreter or script not found. Check paths.\nVENV: {venv_python}\nSCRIPT: {script_path}")

        # Wrap the loop with tqdm for a progress bar
        for product in tqdm(products_to_process, desc="Processing Products"):
            if product.embedding is not None and not force and not product_id:
                skipped_count += 1
                continue

            primary_image = product.images.first()
            if not primary_image:
                tqdm.write(self.style.WARNING(f"SKIPPING: Product {product.name} (SKU: {product.sku}) has no images."))
                skipped_count += 1
                continue

            try:
                result = subprocess.run(
                    [venv_python, script_path, primary_image.image.path],
                    capture_output=True, text=True, check=True, timeout=60  # Add a timeout
                )

                json_line = next((line for line in result.stdout.splitlines() if line.strip().startswith('{')), None)

                if json_line:
                    embedding_data = json.loads(json_line)
                    embedding_vector = embedding_data.get('embedding')
                    if embedding_vector:
                        product.embedding = embedding_vector
                        product.save(update_fields=['embedding'])
                        success_count += 1
                    else:
                        tqdm.write(self.style.ERROR(f"ERROR: No 'embedding' key in JSON for product {product.sku}."))
                        error_count += 1
                else:
                    tqdm.write(self.style.ERROR(f"ERROR: No JSON output from script for product {product.sku}."))
                    error_count += 1

            except subprocess.CalledProcessError as e:
                tqdm.write(self.style.ERROR(f"ERROR: Subprocess failed for product {product.sku}."))
                tqdm.write(e.stderr)
                error_count += 1
            except subprocess.TimeoutExpired:
                tqdm.write(self.style.ERROR(f"ERROR: Script timed out for product {product.sku}."))
                error_count += 1
            except Exception as e:
                tqdm.write(self.style.ERROR(f"ERROR: An unexpected error occurred for product {product.sku}: {e}"))
                error_count += 1

        # --- Final Summary ---
        self.stdout.write("\n" + self.style.SUCCESS("--- Processing Complete ---"))
        self.stdout.write(f"Successfully processed: {success_count}")
        self.stdout.write(f"Skipped: {skipped_count}")
        self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))