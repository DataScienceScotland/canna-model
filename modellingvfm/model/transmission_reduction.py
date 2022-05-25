from ..utils.derived_cases_contacts import DerivedCasesContacts
from ..utils.support_functions import SupportFunctions
import numpy as np


class TransmissionReduction:

    def __init__(self, dict_assumptions, group_list, fortnight_dates_array):
        self.support_functions = SupportFunctions()

        self.dict_assumptions = DerivedCasesContacts().update_actuals_data(dict_assumptions, group_list)
        self.group_list, self.list_group_excl_derived, self.case_contact_volumes_generated = self.support_functions.rearrange_list_of_groups(
            group_list)
        self.fortnightly_periods = fortnight_dates_array
        self.attack_rates = self.support_functions.translate_assumptions_into_matrix(self.group_list,
                                                                                     self.dict_assumptions,
                                                                                     "attack_rate_mapping",
                                                                                     self.fortnightly_periods)

        self.list_static_assumptions = self.dict_assumptions['static_assumptions']

    def generate_matrix_onward_transmission_abated(self):
        new_dict = self.dict_assumptions.copy()
        household_ctas_days_to_isolate = self.dict_assumptions['household_ctas_days_to_isolate']
        nonhousehold_ctas_days_to_isolate = self.dict_assumptions['nonhousehold_ctas_days_to_isolate']
        days_to_isolate_app = self.dict_assumptions['days_to_isolate_app']
        days_to_isolate_schools = self.dict_assumptions['days_to_isolate_schools']
        cumulative_transmission_abated_lookup = self.dict_assumptions['cumulative_transmission_abated_lookup']

        new_dict['household_ctas_contacts_transmission_abated'] = self.support_functions.calc_possible_transmission_abated(
            household_ctas_days_to_isolate, cumulative_transmission_abated_lookup)
        new_dict['nonhousehold_ctas_contacts_transmission_abated'] = self.support_functions.calc_possible_transmission_abated(
            nonhousehold_ctas_days_to_isolate, cumulative_transmission_abated_lookup)
        new_dict['transmission_abated_app_contacts'] = self.support_functions.calc_possible_transmission_abated(
            days_to_isolate_app, cumulative_transmission_abated_lookup)
        new_dict['transmission_abated_school_contacts'] = self.support_functions.calc_possible_transmission_abated(
            days_to_isolate_schools, cumulative_transmission_abated_lookup)


        forward_transmission_abated = self.support_functions.translate_assumptions_into_matrix(self.group_list,
                                                                                               new_dict,
                                                                                               "onward_transmission_abated_mapping",
                                                                                               self.fortnightly_periods)

        list_transmission_abated = ['household_ctas_contacts_transmission_abated', 'nonhousehold_ctas_contacts_transmission_abated', 'transmission_abated_app_contacts', 'transmission_abated_school_contacts']

        dictionary_transmission_abated = {key: new_dict[key] for key in list_transmission_abated}

        return forward_transmission_abated, dictionary_transmission_abated


    def calc_effective_isolation_by_group(self):
        forward_transmission_abated, dictionary_transmission_abated = self.generate_matrix_onward_transmission_abated()
        compliance = self.support_functions.translate_assumptions_into_matrix(self.group_list, self.dict_assumptions,
                                                                              "isolation_compliance_mapping",
                                                                              self.fortnightly_periods)
        attack_rates = self.attack_rates
        true_positive_actuals_data = self.dict_assumptions['actuals_data_PPV']

        effective_isolation_by_group = true_positive_actuals_data * attack_rates * compliance * forward_transmission_abated

        return effective_isolation_by_group

    def calc_prop_transmission_reduction_over_time_by_group(self):
        population_testing_positive = self.dict_assumptions['population_testing_positive']
        effective_isolation_by_group = self.calc_effective_isolation_by_group()
        prop_transmission_reduction = effective_isolation_by_group / population_testing_positive

        return prop_transmission_reduction

    def calc_prop_transmission_reduction_over_time(self):
        prop_transmission_reduction_over_time_by_group = self.calc_prop_transmission_reduction_over_time_by_group()
        prop_transmission_reduction_over_time = prop_transmission_reduction_over_time_by_group.sum(axis=1)

        return prop_transmission_reduction_over_time

    def calc_average_prop_transmission_reduction(self):
        prop_transmission_reduction_over_time = self.calc_prop_transmission_reduction_over_time()
        average_prop_transmission_reduction = np.mean(prop_transmission_reduction_over_time)

        return average_prop_transmission_reduction

    def create_dictionary_storing_outputs(self):
        output_results = dict()

        dictionary_of_group_indices = self.dict_assumptions['dictionary_of_group_indices']
        dictionary_of_subgroup_indices = self.dict_assumptions['dictionary_of_subgroup_indices']
        r_rate = self.dict_assumptions['r_rate']
        prop_transmission_reduction = self.calc_prop_transmission_reduction_over_time_by_group()
        infected_individuals = self.dict_assumptions['actuals_data_PPV'] * self.attack_rates

        dict_prop_transmission_reduction = self.support_functions.create_dictionary_of_grouped_arrays(
            dictionary_of_group_indices, prop_transmission_reduction)
        dict_prop_transmission_reduction = {f'pta_{k}': v for k, v in
                                            dict_prop_transmission_reduction.items()}

        dict_prop_transmission_reduction_sub = self.support_functions.create_dictionary_of_subgrouped_arrays(
            dictionary_of_subgroup_indices, prop_transmission_reduction)
        dict_prop_transmission_reduction_sub = {f'pta_{k}': v for k, v in dict_prop_transmission_reduction_sub.items()}

        dict_infected_individuals = self.support_functions.create_dictionary_of_grouped_arrays(
            dictionary_of_group_indices, infected_individuals)
        dict_infected_individuals = {f'infected_individuals_{k}': v for k, v in dict_infected_individuals.items()}

        dict_r = self.calc_r_reduction(dict_prop_transmission_reduction, r_rate)
        secondary_case_reduction = self.calc_secondary_case_reduction(dict_r, dict_infected_individuals)

        forward_transmission_abated, dictionary_transmission_abated = self.generate_matrix_onward_transmission_abated()

        output_results = {**output_results, **dict_prop_transmission_reduction}
        output_results = {**output_results, **dict_infected_individuals}
        output_results = {**output_results, **dict_r}
        output_results = {**output_results, **secondary_case_reduction}
        output_results = {**output_results, **dict_prop_transmission_reduction_sub}
        output_results = {**output_results, **dictionary_transmission_abated}

        return output_results

    def calc_r_reduction(self, dict_prop_transmission_reduction, r_rate):
        dict_r = dict()

        r_without_TTI = r_rate / (1 - dict_prop_transmission_reduction['pta_TTI_total'])
        r_with_counter = r_without_TTI * (
                    1 - dict_prop_transmission_reduction['pta_counter_total'])
        r_reduction_from_TTI = r_without_TTI - r_rate
        r_reduction_from_NHSTT = r_with_counter - r_rate

        dict_r['r_observed'] = r_rate
        dict_r['r_without_TTI'] = r_without_TTI
        dict_r['r_with_counter'] = r_with_counter
        dict_r['r_red_from_TTI'] = r_reduction_from_TTI
        dict_r['r_red_from_NHSTT'] = r_reduction_from_NHSTT

        return dict_r

    def calc_secondary_case_reduction(self, dict_r, dict_infected_individuals):
        dict_secondary_case_reduction = dict()

        r_reduction_from_NHSTT = dict_r['r_red_from_NHSTT']
        r_reduction_from_TTI = dict_r['r_red_from_TTI']

        infected_individuals_NHSTT_total = dict_infected_individuals['infected_individuals_NHSTT_total']
        infected_individuals_TTI_total = dict_infected_individuals['infected_individuals_TTI_total']

        secondary_case_reduction_NHSTT = r_reduction_from_NHSTT * infected_individuals_NHSTT_total
        secondary_case_reduction_TTI = r_reduction_from_TTI * infected_individuals_TTI_total

        dict_secondary_case_reduction['secondary_case_reduction_NHSTT'] = secondary_case_reduction_NHSTT
        dict_secondary_case_reduction['secondary_case_reduction_TTI'] = secondary_case_reduction_TTI
        dict_secondary_case_reduction['secondary_case_reduction_self_isolation_symp'] = secondary_case_reduction_TTI - secondary_case_reduction_NHSTT

        return dict_secondary_case_reduction
