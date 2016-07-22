from cell_handler import CellHandler

import os
import sys
import json
import logging
import argparse
import getpass

# import Pokemon Go API lib
from pgoapi import pgoapi
from pgoapi import utilities as util

from pokecli import get_cell_ids, get_pos_by_name


# add directory of this file to PATH, so that the package will be found
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


log = logging.getLogger(__name__)


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

    # provide player position on the earth
    api.set_position(*position)

    cell_ids = get_cell_ids(position[0], position[1])
    timestamps = [0, ] * len(cell_ids)
    api.get_map_objects(latitude=util.f2i(position[0]), longitude=util.f2i(position[1]),
                        since_timestamp_ms=timestamps, cell_id=cell_ids)

    api.download_settings(hash="05daf51635c82611d1aac95c0b051d3ec088a930")

    # execute the RPC call
    response_dict = api.call()

    with open('web/result.json', "w") as f:
        f.write(json.dumps(
            {
                "Latitude": position[0],
                "Longitude": position[1],
                "Pokemons": get_pokemons_from_call(response_dict)
            },
            sort_keys=True,
            indent=2
        ))


if __name__ == '__main__':
    main()
