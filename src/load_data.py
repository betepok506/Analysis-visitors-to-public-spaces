import os
import config
import sys
from bokeh.palettes import *
import random

config.initConfig()


color_plt = PRGn
# color_plt = Spectral
# color_plt = Bokeh
# color_plt = turbo(15)
# colors = color_plt
colors = color_plt[max([int(s) for s in color_plt.keys()])]

module = sys.modules[__name__]
def load_roads():
    if os.path.exists(config.getCell('file_roads')):
        with open(config.getCell('file_roads'), 'r') as f:
            roads = f.readlines()
        all_info_roads = []
        for idx, road_ in enumerate(roads):
            info_road = road_.split('|')
            info_road[1]=info_road[1].rstrip('\n')
            info_road.append(colors[(idx + 7) % len(colors)])
            all_info_roads.append(info_road)

        return all_info_roads
    else:
        print(FileNotFoundError)
        return None

# По индексу дороги выдаем ее статистику
def load_stat_road(num_road):
    if os.path.exists(os.path.join(config.getCell('path_info_roads'), f"info_road_{num_road}.txt")):
        with open(os.path.join(config.getCell('path_info_roads'), f"info_road_{num_road}.txt"), 'r', encoding='utf-8') as f:
            stat_road = f.readlines()
        return stat_road
    else:
        print(f"No info about zone {num_road}")
        return []

if __name__=="__main__":
    pass
