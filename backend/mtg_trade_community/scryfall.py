import requests

headers = {'content-type': 'Application/json'}


class CardNotFound(BaseException):
    pass


class ScryfallRequestError(BaseException):

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'ScryfallRequestError: {self.message}'


class Scryfall:
    scryfall_base_url = 'https://api.scryfall.com'

    def fetch_card(self, card_name):
        resource_url = f'{self.scryfall_base_url}/cards/search?q={card_name}'

        response = requests.get(resource_url, headers=headers)

        r = response.json()
        if r['total_cards'] != 1:
            raise CardNotFound()

        return {
            'id': r['data'][0]['id'],
            'name': r['data'][0]['name'],
            'prints_search_uri': r['data'][0]['prints_search_uri']
        }

    # def fetch_card_sets(self, card):
    #     response = requests.get(card['prints_search_uri'], headers=headers)
    #     r = response.json()
    #     return r

    def get_all_sets(self):
        resource_url = f'{self.scryfall_base_url}/sets/'
        response = requests.get(resource_url, headers=headers)
        if (response.ok):
            return response.json()
        raise ScryfallRequestError(f'get_all_sets: {set_code} - {response.status_code}')

    def get_all_cards_by_set(self, set_code):
        resource_url = f'{self.scryfall_base_url}/cards/search?q=set:{set_code}'
        response = requests.get(resource_url, headers=headers)
        if (response.ok):
            return response.json()
        raise ScryfallRequestError(f'get_all_cards_by_set: {set_code} - {response.status_code}')
