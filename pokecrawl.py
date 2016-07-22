from cell_handler import CellHandler

import os
import sys
import json
import logging
import argparse
import getpass
import re

# import Pokemon Go API lib
from pgoapi import pgoapi
from pgoapi import utilities as util

from pokecli import get_cell_ids, get_pos_by_name
from s2sphere import Cell, CellId


# add directory of this file to PATH, so that the package will be found
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


log = logging.getLogger(__name__)


def get_nearby_positions(lat, lon):
    m_per_deg_lat = 111132.954 - 559.822 * cos( 2 * latMid ) + 1.175 * cos( 4 * latMid);
    m_per_deg_lon = 111132.954 * cos ( latMid );
    return []



def get_pokemons_from_call(response):

    cells = response['responses']['GET_MAP_OBJECTS']['map_cells']

    pokemons = []
    for cell in cells:
        pokemons.extend(CellHandler(cell).get_cell_pokemons())

    return pokemons


def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')", default="google")
    parser.add_argument("-u", "--username", help="Username")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-l", "--location", help="Location")
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.set_defaults(DEBUG=False, TEST=False)
    config = parser.parse_args()

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load and config.__dict__[key] == None:
            config.__dict__[key] = str(load[key])

    if config.__dict__["password"] is None:
        log.info("Secure Password Input (if there is no password prompt, use --password <pw>):")
        config.__dict__["password"] = getpass.getpass()

    if config.auth_service not in ['ptc', 'google']:
      log.error("Invalid Auth service specified! ('ptc' or 'google')")
      return None

    return config


def main():
    # log settings
    # log format
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s'
    )
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)

    config = init_config()
    if not config:
        return

    if config.debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.DEBUG)

    position = get_pos_by_name(config.location)
    if config.test:
        return

    # instantiate pgoapi
    api = pgoapi.PGoApi()

    if not api.login(config.auth_service, config.username, config.password):
        return


    all_cell_ids = get_cell_ids(position[0], position[1], radius=100)

    batch = 10
    batch_count = int(len(all_cell_ids) / batch)
    pokemon = []

    try:
        #we batch the querys
        for i in range(batch_count - 1):
            cell_ids = all_cell_ids[i * batch_count:(i * batch_count) + batch]
            center_cell = CellId(cell_ids[int(batch / 2)])

            gpsre = "LatLng: (?P<lat>\d+.\d+),(?P<lon>\d+.\d+)"
            center_gps = re.search(gpsre, str(center_cell.to_lat_lng()))

            lat = float(center_gps.group('lat'))
            lon = float(center_gps.group('lon'))

            # provide player position on the earth
            api.set_position(lat, lon, 0.0)
            timestamps = [0, ] * len(cell_ids)
            api.get_map_objects(
                latitude=util.f2i(lat),
                longitude=util.f2i(lon),
                since_timestamp_ms=timestamps,
                cell_id=cell_ids
            )

            api.download_settings(hash="05daf51635c82611d1aac95c0b051d3ec088a930")

            # execute the RPC call
            response_dict = api.call()

            pokemon.extend(get_pokemons_from_call(response_dict))

    finally:
        with open('web/result.json', "w") as f:
            f.write(json.dumps(
                {
                    "Latitude": position[0],
                    "Longitude": position[1],
                    "Pokemons": pokemon
                },
                sort_keys=True,
                indent=2
            ))


if __name__ == '__main__':
    main()
