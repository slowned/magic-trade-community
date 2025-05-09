import os
import json
from django.core.management.base import BaseCommand
from binders.models import Card


class Command(BaseCommand):
    help = 'Load cards data from a JSON file into the Card model'

    def handle(self, *args, **kwargs):
        # Obtener la ruta absoluta del archivo JSON
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Directorio actual del script
        file_path = os.path.join(base_dir, 'scryfall_m11_filtered.json')

        with open(file_path, 'r') as file:
            cards_data = json.load(file)

        for card_data in cards_data:
            # Insertar cada carta en la base de datos
            card, created = Card.objects.update_or_create(
                id=card_data["id"],
                defaults={
                    "name": card_data["name"],
                    "set_name": card_data["set_name"],
                    "color_identity": ",".join(card_data["color_identity"]),  # Convierte la lista a cadena
                    "uri": card_data["uri"],
                    "scryfall_uri": card_data["scryfall_uri"],
                    "image_uri": card_data["image_uri"] if card_data["image_uri"] else ""
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Card "{card.name}" created successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Card "{card.name}" updated successfully'))

        self.stdout.write(self.style.SUCCESS('Data loaded successfully'))
