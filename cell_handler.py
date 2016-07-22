import logging
from pokemon import Pokemon


logger = logging.getLogger(__name__)


class CellHandler(object):

    def __init__(self, cell_dict):
        self.cell = cell_dict

    def get_cell_pokemons(self):
        wilds = self.cell.get('wild_pokemons', [])
        catchables = self.cell.get('catchable_pokemons', [])

        pokemons = []

        pokemons.extend([Pokemon.from_wild(wild).to_dict() for wild in wilds])
        pokemons.extend([Pokemon.from_catch(catch).to_dict() for catch in catchables])

        return pokemons
