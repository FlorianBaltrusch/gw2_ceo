# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:54:03 2024

@author: Xarthisius
"""

from tqdm import tqdm
from itertools import combinations
from common.types import BuildSuggestion
import common.general_data as gd

def print_combinations(numbers, suggestion: BuildSuggestion, name_filter_1, name_filter_2, name_filter_3):

    # %% find combinations
    unique_combinations = []

    for num_elements in tqdm(range(1, len(numbers) + 1)):
        for combination in combinations(numbers, num_elements):
            if 0 not in combination and sum(combination) == suggestion.target:
                sorted_combination = tuple(sorted(combination))
                if sorted_combination not in unique_combinations:
                    unique_combinations.append(sorted_combination)
    print('\n')

    # # solution in numbers
    # for combo in unique_combinations:
    #     print(combo)
    print('Numbers of solutions:', len(unique_combinations))

    # solution in names
    name_list = []
    for combo in unique_combinations:
        modified_row = [gd.names[numbers.index(zahl)] for zahl in combo]
        name_list.append(modified_row)

    # %% filter combinations 1
    filtered_name_list_1 = []

    if name_filter_1:
        for row in name_list:
            sgbs = sum('S/G/B' in word for word in row)
            access = sum('Access' in word for word in row)
            if (sgbs == 0 or sgbs == 3) and (access == 0 or access == 2):
                filtered_name_list_1.append(row)
    else:
        filtered_name_list_1 = name_list[:]

    # %% filter combinations 2
    filtered_name_list_2 = []

    if name_filter_2:
        for row in filtered_name_list_1:
            accessCount = sum('Access' in word for word in row)
            lrCount = sum('L/R' in word for word in row)
            amw2Count = sum('Am/W2' in word for word in row)
            backCount = sum('Back' in word for word in row)
            jewCount = sum('Jew' in word for word in row)

            if amw2Count == 0 or amw2Count == 1:
                if lrCount == 1:
                    if (accessCount + amw2Count + backCount == jewCount or
                        accessCount + amw2Count == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                elif lrCount == 0 or lrCount == 2:
                    if (accessCount + lrCount + amw2Count + backCount == jewCount or
                        accessCount + lrCount + amw2Count == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                else:
                    if (accessCount + (lrCount - 1) + amw2Count + backCount == jewCount or
                        accessCount + (lrCount - 1) + amw2Count == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

            elif amw2Count == 2:
                if lrCount == 1:
                    if (accessCount + backCount == jewCount or
                        accessCount == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                elif lrCount == 0 or lrCount == 2:
                    if (accessCount + lrCount + backCount == jewCount or
                        accessCount + lrCount == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                else:
                    if (accessCount + (lrCount - 1) + backCount == jewCount or
                        accessCount + (lrCount - 1) == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)
            else:
                if lrCount == 1:
                    if (accessCount + (amw2Count - 1) + backCount == jewCount or
                        accessCount + (amw2Count - 1) == jewCount or
                        accessCount + backCount == jewCount or
                        accessCount == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                elif lrCount == 0 or lrCount == 2:
                    if (accessCount + lrCount + (amw2Count - 1) + backCount == jewCount or
                        accessCount + lrCount + (amw2Count - 1) == jewCount or
                        accessCount + lrCount + backCount == jewCount or
                        accessCount + lrCount == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

                else:
                    if (accessCount + (lrCount - 1) + (amw2Count - 1) + backCount == jewCount or
                        accessCount + (lrCount - 1) + (amw2Count - 1) == jewCount or
                        accessCount + (lrCount - 1) + backCount == jewCount or
                        accessCount + (lrCount - 1) == jewCount or
                        accessCount + (amw2Count - 1) + backCount == jewCount or
                        accessCount + (amw2Count - 1) == jewCount or
                        accessCount + backCount == jewCount or
                        accessCount == jewCount or
                            backCount == jewCount):
                        filtered_name_list_2.append(row)

            if jewCount == 0 or jewCount == 1 or jewCount == 6:
                if row not in filtered_name_list_2:
                    filtered_name_list_2.append(row)
    else:
        filtered_name_list_2 = filtered_name_list_1[:]

    # remove dublicates
    filtered_name_list_2_unique = []
    [filtered_name_list_2_unique.append(x) for x in filtered_name_list_2 if x not in filtered_name_list_2_unique]

    # %% filter combinations 3
    filtered_name_list_3 = []

    if name_filter_3:
        filtered_name_list_3 = [Ausdruck for Ausdruck in filtered_name_list_2_unique if 'Infu' not in Ausdruck]
    else:
        filtered_name_list_3 = filtered_name_list_2_unique[:]

    print('Swap out the following', suggestion.base_gear, 'pieces:')
    for row in filtered_name_list_3:
        print(row)
