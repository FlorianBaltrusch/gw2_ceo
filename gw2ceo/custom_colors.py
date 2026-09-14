# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 14:20:38 2024

@author: baltrusch
"""
# %% Imports
try:
    from matplotlib.colors import LinearSegmentedColormap
except ImportError:  # matplotlib is optional: the color constants work without it
    LinearSegmentedColormap = None

# %% Define colors
aureus = '#edb227ff'
incandescent = '#ffec4cff'

molten = '#9c5915ff'
sunfire_lava = '#ff9303ff'

crimson_lion = '#810000ff'
ruby_red = '#bd000bff'

phthalo_blue = '#001c67ff'
legend = '#144382ff'
sand_shark = '#1a8ac5ff'

violite = '#664785ff'
glints_rebellion = '#c0a8d3ff'

verdant_jade = '#085c08ff'
growth = '#009400ff'

destroyer_orange = '#f05000ff'
warband = '#a94900ff'
torment = '#680968ff'

silver_satin = '#898989ff'
slate = '#585858ff'

shadow_abyss = '#000000ff'

# %% Define color lists
color_list = [sand_shark, sunfire_lava, growth, ruby_red, violite, molten]
symbol_list = ['o', '^', 's', 'v', 'p']

# %% Defince color maps

cmap_colors = [
    shadow_abyss,
    crimson_lion,
    ruby_red,
    destroyer_orange,
    sunfire_lava,
    aureus,
    incandescent
]

if LinearSegmentedColormap is not None:
    crucible = LinearSegmentedColormap.from_list("crucible", cmap_colors, N=256)
