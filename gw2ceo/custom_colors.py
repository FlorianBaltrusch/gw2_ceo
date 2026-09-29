"""
Created on Thu Nov 14 14:20:38 2024

@author: baltrusch
"""

# %% Imports
try:
    from matplotlib.colors import LinearSegmentedColormap  # noqa: I001  # pyright: ignore[reportMissingImports, reportMissingModuleSource]
except ImportError:  # matplotlib is optional: the color constants work without it
    LinearSegmentedColormap = None

# %% Define colors
aureus = "#edb227ff"
incandescent = "#ffec4cff"

molten = "#9c5915ff"
sunfire_lava = "#ff9303ff"

crimson_lion = "#810000ff"
ruby_red = "#bd000bff"

phthalo_blue = "#001c67ff"
legend = "#144382ff"
sand_shark = "#1a8ac5ff"

violite = "#664785ff"
glints_rebellion = "#c0a8d3ff"

verdant_jade = "#085c08ff"
growth = "#009400ff"

destroyer_orange = "#f05000ff"
warband = "#a94900ff"
torment = "#680968ff"

silver_satin = "#898989ff"
slate = "#585858ff"

shadow_abyss = "#000000ff"


# %% Per-profession palettes (Guild Wars 2 Class Colors.md; RGB from gw2_colors_sorted.xlsx)
# (dark: backgrounds - replaces phthalo blue; mid: buttons/borders - replaces
#  ruby red; bright: text - replaces aureus). The site uses them once a
#  profession is chosen; before that the default phthalo/ruby/aureus theme.
profession_palettes = {
    #                 dark (color 1)   mid (color 2)    bright (color 3)
    "Elementalist": ("#0f0000", "#810000", "#edb227"),  # Shadow Orange, Crimson Lion, Aureus
    "Mesmer": ("#080009", "#680968", "#c0a8d3"),  # Shadow Purple, Torment, Glint's Rebellion
    "Necromancer": ("#001000", "#085c08", "#009400"),  # Shadow Green, Verdant Jade, Growth
    "Engineer": ("#210000", "#9c5915", "#ffec4c"),  # Midnight Bronze, Molten, Incandescent
    "Ranger": ("#002911", "#004a00", "#8b2e12"),  # Enameled Longevity, Canopy, Flame
    "Thief": ("#000000", "#bd000b", "#ffffff"),  # Shadow Abyss, Ruby Red, Permafrost
    "Guardian": ("#00030c", "#0c203d", "#1a8ac5"),  # Shadow Blue, Resolution, Sand Shark
    "Revenant": ("#110000", "#330202", "#c40000"),  # Shadow Red, Hydra, Magma
    "Warrior": ("#080900", "#580000ff", "#ff9303"),  # Shadow Yellow, Rosewood, Sunfire Lava
}

# %% Define color lists
color_list = [sand_shark, sunfire_lava, growth, ruby_red, violite, molten]
symbol_list = ["o", "^", "s", "v", "p"]

# %% Defince color maps

cmap_colors = [shadow_abyss, crimson_lion, ruby_red, destroyer_orange, sunfire_lava, aureus, incandescent]

if LinearSegmentedColormap is not None:
    crucible = LinearSegmentedColormap.from_list("crucible", cmap_colors, N=256)
