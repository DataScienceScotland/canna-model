import pandas as pd
import math
import numpy as np
from .config import ImportConfig


class SupportFunctions:

    def __init__(self):
        assumptions = ImportConfig('assumptions_config').get_yaml_config()
        self.case_contact_volumes_generated = assumptions['case_contact_volumes_generated']

    def rearrange_list_of_groups(self, groups):

        list_group_excl_derived = groups.copy()
        groups_to_be_derived = []
        for group in self.case_contact_volumes_generated:
            if group in groups:
                list_group_excl_derived.remove(group)
                groups_to_be_derived.append(group)
            else:
                pass

        groups_sorted = list_group_excl_derived.copy()
        groups_sorted.extend(groups_to_be_derived)

        return groups_sorted, list_group_excl_derived, self.case_contact_volumes_generated

    def create_fortnight_periods(self, start, end, delta):
        curr = start
        while curr < end:
            yield curr
            curr += delta

    def create_fortnight_df(self, start, end, delta):

        fortnightly_periods = []

        for fortnight in self.create_fortnight_periods(start, end, delta):
            fortnightly_periods.append(fortnight)

        df = pd.DataFrame({'fortnight_date': fortnightly_periods})

        df['fortnight_date'] = pd.to_datetime(df['fortnight_date'])

        return df

    def get_dictionary_value_by_interpolation(self, key, dict_to_use):
        key = float(key)

        if key == 0:
            key = 0.01
        if key > 20:
            key = 20

        key_lower = math.floor(key * 100) / 100
        key_upper = math.ceil(key * 100) / 100
        key_difference = key - key_lower

        dict_value_lower = dict_to_use.get(key_lower)
        dict_value_upper = dict_to_use.get(key_upper)

        returned_dict_value = dict_value_lower + ((dict_value_upper - dict_value_lower) * key_difference)

        return returned_dict_value

    def apply_PPV(self, cases, prevalence, test_sensitivity, test_specificity):

        sensitivity_prevalence = test_sensitivity * prevalence
        inverse_specificity = 1 - test_specificity
        inverse_prevalence = 1 - prevalence

        PPV = sensitivity_prevalence / (sensitivity_prevalence + (inverse_specificity * inverse_prevalence))

        true_positive_actuals_data = cases * PPV

        return true_positive_actuals_data, PPV

    def calc_PPV(self, prevalence, test_sensitivity, test_specificity):

        sensitivity_prevalence = test_sensitivity * prevalence
        inverse_specificity = 1 - test_specificity
        inverse_prevalence = 1 - prevalence

        PPV = sensitivity_prevalence / (sensitivity_prevalence + (inverse_specificity * inverse_prevalence))

        return PPV

    def generate_PPV_for_tests(self, dictionary):

        prevalence = dictionary['proportion_population_testing_positive']

        PCR_sensitivity = dictionary["PCR_sensitivity"]
        PCR_specificity = dictionary["PCR_specificity"]

        PCR_PPV = self.calc_PPV(prevalence, PCR_sensitivity, PCR_specificity)

        return PCR_PPV

    def create_dictionary_of_indices(self, group_list):

        dictionary_of_indices = dict()

        for i in range(0, len(group_list)):
            group = group_list[i]

            dictionary_of_indices[group] = i

        return dictionary_of_indices

    def create_list_of_group_indices(self, dictionary_of_indices, groups_to_include):

        list_of_group_indices = []

        for group in groups_to_include:

            try:
                idx = dictionary_of_indices.get(group)
                list_of_group_indices.append(idx)
            except:
                pass

        return list_of_group_indices

    def create_dictionary_of_group_indices(self, group_list, dict_groups_to_include):

        dictionary_of_indices = self.create_dictionary_of_indices(group_list)

        dictionary_of_group_indices = dict()

        for grouping in dict_groups_to_include:
            groups_to_include = dict_groups_to_include.get(grouping)

            dictionary_of_group_indices[grouping] = self.create_list_of_group_indices(dictionary_of_indices,
                                                                                      groups_to_include)

        return dictionary_of_group_indices

    def create_array_specific_groups(self, name_of_grouping, dictionary_of_group_indices, array_to_use):

        indices = dictionary_of_group_indices.get(name_of_grouping)

        array_of_grouping = array_to_use[:, indices]

        return array_of_grouping

    def create_dictionary_of_grouped_arrays(self, dictionary_of_group_indices, array_to_use):

        dictionary_of_group_arrays = dict()

        for grouping in dictionary_of_group_indices:
            temp_array = self.create_array_specific_groups(grouping, dictionary_of_group_indices, array_to_use)
            temp_array = temp_array.sum(axis=1)
            dictionary_of_group_arrays[grouping] = np.reshape(temp_array, (-1, 1))

        return dictionary_of_group_arrays

    def create_dictionary_of_subgrouped_arrays(self, dictionary_of_group_indices, array_to_use):

        dictionary_of_group_arrays = dict()

        for subgroup in dictionary_of_group_indices:
            temp_array = array_to_use[:, dictionary_of_group_indices.get(subgroup)]
            #temp_array = np.sum(temp_array, keepdims = True)
            dictionary_of_group_arrays[subgroup] = np.reshape(temp_array, (-1, 1))

        return dictionary_of_group_arrays

    def translate_assumptions_into_matrix(self, groups, dictionary, mapping_name, fortnightly_periods):

        length_of_matrix = len(fortnightly_periods)

        mapping = dictionary.get(mapping_name)

        assumption_matrix = np.empty(shape=(length_of_matrix, 0), dtype='float')
        blank_assumption_na = np.full((length_of_matrix, 1), 1)

        for group in groups:

            if group in mapping:
                assumption_to_use = mapping.get(group)
                assumption_matrix = np.append(assumption_matrix, dictionary.get(assumption_to_use), axis=1)

            else:
                assumption_matrix = np.append(assumption_matrix, blank_assumption_na, axis=1)

        return assumption_matrix

    def calc_possible_transmission_abated(self, days_to_isolate, cumulative_transmission_abated_lookup):

        forward_transmission_abated = days_to_isolate.copy()

        for x in range(0, days_to_isolate.shape[0]):
            forward_transmission_abated[x, 0] = self.get_dictionary_value_by_interpolation(
                days_to_isolate[x, 0], cumulative_transmission_abated_lookup)

        return forward_transmission_abated
