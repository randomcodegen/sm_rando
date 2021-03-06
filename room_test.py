from world_rando import concrete_map
from world_rando import item_order_graph
from world_rando import map_gen
from world_rando import map_viz
from world_rando import room_gen
from world_rando import settings
from world_rando import pattern

from rom_tools import rom_manager
from encoding import sm_global
import random
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def get_path_info(paths):
    npaths = len(paths)
    lens = [len(p[2]) for p in paths]
    total_length = sum(lens)
    return total_length, npaths

#TODO: config file for editing settings so that it's easier to change the settings.

if __name__ == "__main__":
    patterns = pattern.load_patterns("encoding/patterns")
    o, g, rsg, es, ro = item_order_graph.abstract_map(settings.abstract_map_settings)
    region_cmaps = {}
    region_room_defs = {}
    ntiles = 0
    room_dims = []
    path_length = 0
    npaths = 0
    for region, graph in rsg.items():
        graph.visualize("output/" + region + "/graph")
        print("Generating map for " + region)
        # At most 64,32
        dimensions = concrete_map.Coord(54,30)
        cmap, rooms, paths = map_gen.less_naive_gen(dimensions, graph, es, settings.concrete_map_settings)
        region_cmaps[region] = cmap
        region_room_defs[region] = room_gen.make_rooms(rooms, cmap, paths, settings.room_gen_settings, patterns)
        # Various info
        ntiles += len(region_cmaps[region])
        for room in rooms.values():
            room_dims.append(len(room))
        l,n = get_path_info(paths)
        path_length += l
        npaths += n

    print("Tiles: " + str(ntiles))
    print("Average room size: " + str(sum(room_dims)/len(room_dims)))
    print("Average path length: " + str(path_length/npaths))

    for region, cmap in region_cmaps.items():
        map_viz.map_viz(cmap, "output/" + region + "/cmap.png", "encoding/map_tiles")
    for region, room_defs in region_room_defs.items():
        for room_def in room_defs.values():
            room_def.viz_cmap("output/" + region)
            room_def.viz_graph("output/" + region)
            room_def.viz_level("output/" + region)

