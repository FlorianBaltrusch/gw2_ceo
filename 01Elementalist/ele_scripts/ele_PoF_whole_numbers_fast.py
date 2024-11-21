# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:54:03 2024

@author: Xarthisius
"""
# %% find whole numbers
if gear_environment:
    wn_numbers = elements_of_rage * low_gear
else:
    if weapon_type:
        walk_gear = Pc3Min1h if weapon_rarity else Pc3Min1hL
    else:
        walk_gear = Pc3Min2h if weapon_rarity else Pc3Min2hL

    wn_numbers = elements_of_rage * (walk_gear - low_gear)


def find_combinations(wn_numbers, target):
    wn_target = round(target % 1, 2)  # Nachkommastellen von target
    sum_combinations = defaultdict(list)
    unique_combinations = set()  # Set, um Duplikate zu vermeiden
    minimum_sum = None  # Variable für die Speicherung der minimalen Summe

    for wn_num_elements in tqdm(range(1, len(wn_numbers) + 1)):
        for wn_combination in combinations(wn_numbers, wn_num_elements):
            if 0 not in wn_combination:
                rounded_combination = tuple(round(num, 2) for num in wn_combination)
                comb_sum = round(sum(rounded_combination), 2)
                sum_decimals = round(comb_sum % 1, 2)
                sorted_combination = tuple(sorted(rounded_combination))
                if sorted_combination not in unique_combinations:
                    unique_combinations.add(sorted_combination)
                    if sum_decimals == wn_target:
                        # Prüfen, ob dies die kleinste Summe ist oder ob es die erste Kombination mit der richtigen Nachkommastelle ist
                        if minimum_sum is None or comb_sum < minimum_sum:
                            minimum_sum = comb_sum
                            sum_combinations[sum_decimals] = [sorted_combination]
                        elif comb_sum == minimum_sum:
                            sum_combinations[sum_decimals].append(sorted_combination)

    # Rückgabe der Kombinationen mit minimaler Summe und der minimalen Summe selbst
    if wn_target in sum_combinations:
        return sum_combinations[wn_target], minimum_sum
    else:
        return None, None


wn_combinations, minimum_sum = find_combinations(wn_numbers, target)

# solution in names
wn_numbers_list = wn_numbers.round(2).tolist()  # Konvertiere die Series in eine Liste und runde auf zwei Dezimalstellen

wn_name_list = []
for wn_combo in wn_combinations:
    wn_modified_row = [names[wn_numbers_list.index(round(zahl, 2))] for zahl in wn_combo]
    wn_name_list.append(wn_modified_row)

# for row in wn_name_list:
#     print(row)

n = 0
print('Use the following Walkyrie gear:', wn_name_list[n])


def modify_numbers(n, wn_combinations, wn_numbers, numbers, low_gear):
    wn_walk_gear = wn_combinations[n]

    indices = []
    for num in wn_walk_gear:
        for idx, val in enumerate(wn_numbers):
            if val == num:
                indices.append(idx)
                wn_numbers[idx] = None
                break

    for index in indices:
        numbers[index] = 0  # Stelle sicher, dass `numbers` eine Liste ist, keine Tuple

    # Elemente aus walk_gear basierend auf den gefundenen Indices sammeln
    used_low_gear = [low_gear[index] for index in indices]
    wn_walk_precision = sum(used_low_gear)

    return numbers, used_low_gear, wn_walk_precision


modified_numbers, used_low_gear, wn_walk_precision = modify_numbers(n, wn_combinations, wn_numbers, numbers, low_gear)

target += wn_walk_precision - minimum_sum
target = int(target)

print('The new target is:', target)

if not weapon_rarity:
    if weapon_type:
        numbers.remove(5)
    else:
        numbers.remove(5)
        numbers.remove(5)

if target < 0:
    numbers = [-abs(num) for num in numbers]
else:
    numbers = [abs(num) for num in numbers]

if not weapon_rarity:
    numbers += [5] if weapon_type else [5, 5]
