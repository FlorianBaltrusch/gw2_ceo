# %%

from base64 import b64decode
from construct import Array, BitsInteger, Bitwise, Byte, Const, Enum, Struct, Int16ul
import requests

from gw2ceo.api import get_api_data



link = b"[&DQYpHx89MBcAACcPwxJQAb4BAADLAMsAJgCWAAAAAAAAAAAAAAAAAAAAAAADVgAxAFkAAA==]"
data = b64decode(link)
" ".join([hex(b) for b in data])



parsed = Struct(
    "header" / Const(b"\x0d"),
    "profession" / Byte,
    "specializations" / Array(3, Struct(
        "id" / Byte,
        "mask" / Bitwise(Array(4, BitsInteger(2)))
    )),
    "skills" / Array(10, Int16ul)
).parse(data)



profession = get_api_data("professions")[parsed["profession"]-1]
specialisations = []
traits = []
for specialisation in parsed["specializations"]:
    spec_data = get_api_data(f"specializations/{specialisation.id}")
    specialisations.append(spec_data["name"])
    for trait in spec_data["minor_traits"]:
        traits.append(get_api_data(f"traits/{trait}")["name"])
    if specialisation["mask"][3] > 0:
        traits.append(get_api_data(f"traits/{spec_data["major_traits"][-1+specialisation["mask"][3]]}")["name"])
    if specialisation["mask"][2] > 0:
        traits.append(get_api_data(f"traits/{spec_data["major_traits"][2+specialisation["mask"][2]]}")["name"])
    if specialisation["mask"][1] > 0:
        traits.append(get_api_data(f"traits/{spec_data["major_traits"][5+specialisation["mask"][1]]}")["name"])


skills_by_palette = dict(get_api_data(f"professions/{profession}")['skills_by_palette'])
skills = [get_api_data(f"skills/{skills_by_palette.get(palette, None)}")["name"] for palette in parsed.skills if palette]

