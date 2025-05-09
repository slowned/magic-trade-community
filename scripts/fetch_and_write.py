import requests
import json

# Especificar el código de la edición 2011 (Magic 2011 - "M11" en este ejemplo)
set_code = "M11"
url = f"https://api.scryfall.com/cards/search?q=set:{set_code}"

cards = []
has_more = True

# Realizar la solicitud y obtener todos los resultados paginados
while has_more:
    response = requests.get(url)
    data = response.json()
    # Agregar las cartas a la lista
    cards.extend(data['data'])
    # Verificar si hay más páginas
    has_more = data.get('has_more', False)
    url = data.get('next_page', None)

filtered_cards = [
    {
        "id": card["id"],
        "name": card["name"],
        "set_name": card["set_name"],
        "color_identity": card["color_identity"],
        "uri": card["uri"],
        "scryfall_uri": card["scryfall_uri"],
        "image_uri": card.get("image_uris", {}).get("normal"),
    }

    for card in cards
]

print(cards[0])

# Guardar el resultado en un archivo JSON
with open('scryfall_m11_filtered.json', 'w') as file:
    json.dump(filtered_cards, file, indent=4)

print("Dump completo guardado en scryfall_m11_edition.json")
