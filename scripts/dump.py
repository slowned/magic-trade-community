import sqlite3
import json

# Conectar a la base de datos y crear la tabla
conn = sqlite3.connect('scryfall_cards.sqlite')
cursor = conn.cursor()
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS cards (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT,
#     image_uri TEXT,
#     type_line TEXT
# )
# ''')
# conn.commit()

# Cargar el JSON y agregar cada carta a la base de datos
with open('scryfall_m11_edition_filtered.json', 'r') as file:
    cards = json.load(file)

for card in cards:
    cursor.execute('''
    INSERT INTO cards (
        id,
        name,
        set_name,
        color_identity,
        uri,
        scryfall_uri,
        image_uri
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        card['id'],
        card['name'],
        card['set_name'],
        card['color_identity'],
        card['uri'],
        card['scryfall_uri'],
        card['image_uri']
    ))

conn.commit()
print("Datos insertados exitosamente en la base de datos.")
conn.close()
