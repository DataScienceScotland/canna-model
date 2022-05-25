from .transmission_reduction import TransmissionReduction
from ..utils.derived_cases_contacts import DerivedCasesContacts
import numpy as np
import pandas as pd
import os


class OutputExcel(TransmissionReduction):

    def __init__(self, dict_assumptions, group_list, fortnight_dates_array):
        super().__init__(dict_assumptions, group_list, fortnight_dates_array)

        self.output_filename = os.getcwd() + "/modellingvfm/outputs/output_all_inputs.xlsx"
        self.directory = os.getcwd()

    def format_time_matrix_to_df(self, matrix, column_names):

        df = pd.DataFrame(data = matrix, index = self.fortnightly_periods, columns = column_names)
        df.reset_index(level = 0, inplace = True)
        df = df.rename(columns = {df.columns[0]: "fortnight_start_date"})

        return df

    def format_matrix_to_df(self, matrix, column_names):

        df = pd.DataFrame(data = matrix.reshape(-1, len(matrix)), columns = column_names)

        return df

    def calc_prop_transmission_reduction_by_group_df(self):

        prop_transmission_reduction = self.calc_prop_transmission_reduction_over_time_by_group()
        prop_transmission_reduction_df = self.format_time_matrix_to_df(prop_transmission_reduction, self.group_list)

        return prop_transmission_reduction_df

    def calc_r_reduction_outputs(self):
        proportion_population_testing_positive = self.dict_assumptions['proportion_population_testing_positive']
        dictionary_of_group_indices = self.dict_assumptions['dictionary_of_group_indices']
        r_rate = self.dict_assumptions['r_rate']
        prop_transmission_reduction = self.calc_prop_transmission_reduction_over_time_by_group()

        dict_prop_transmission_reduction = self.support_functions.create_dictionary_of_grouped_arrays(dictionary_of_group_indices, prop_transmission_reduction)
        dict_prop_transmission_reduction = {f'pta_{k}': v for k, v in dict_prop_transmission_reduction.items()}

        dict_r = self.calc_r_reduction(dict_prop_transmission_reduction, r_rate)

        output_df = pd.DataFrame()
        output_df['fortnight_date'] = self.fortnightly_periods
        output_df['proportion_population_testing_positive'] = proportion_population_testing_positive

        output_df['r_observed'] = dict_r.get("r_observed")
        output_df['r_without_TTI'] = dict_r.get("r_without_TTI")
        output_df['r_with_counter'] = dict_r.get("r_with_counter")
        output_df['r_red_from_TTI'] = dict_r.get("r_red_from_TTI")
        output_df['r_red_from_NHSTT'] = dict_r.get("r_red_from_NHSTT")

        return output_df

    def calc_output_dfs(self):
        dictionary_of_group_indices = self.dict_assumptions['dictionary_of_group_indices']
        prop_transmission_reduction = self.calc_prop_transmission_reduction_over_time_by_group()
        infected_individuals = self.dict_assumptions['actuals_data_PPV'] * self.support_functions.translate_assumptions_into_matrix(self.group_list, self.dict_assumptions, "attack_rate_mapping", self.fortnightly_periods)


        dict_prop_transmission_reduction = self.support_functions.create_dictionary_of_grouped_arrays(
            dictionary_of_group_indices, prop_transmission_reduction)
        dict_prop_transmission_reduction = {f'pta_{k}': v for k, v in
                                            dict_prop_transmission_reduction.items()}

        dict_infected_individuals = self.support_functions.create_dictionary_of_grouped_arrays(dictionary_of_group_indices, infected_individuals)
        dict_infected_individuals = {f'infected_individuals_{k}': v for k, v in dict_infected_individuals.items()}

        infected_individuals_output = self.create_df_from_output_dict(dict_infected_individuals)
        prop_transmission_reduction_output = self.create_df_from_output_dict(dict_prop_transmission_reduction)

        r_rate = self.dict_assumptions['r_rate']
        r_dict = self.calc_r_reduction(dict_prop_transmission_reduction, r_rate)

        secondary_case_reduction = self.calc_secondary_case_reduction(r_dict, dict_infected_individuals)

        secondary_case_reduction_output = self.create_df_from_output_dict(secondary_case_reduction)

        return infected_individuals_output, prop_transmission_reduction_output, secondary_case_reduction_output



    def create_df_from_output_dict(self, dict):

        output_df = pd.DataFrame()
        output_df['fortnight_date'] = self.fortnightly_periods

        for group in dict:
            output_df[group] = dict.get(group)

        return output_df


    def output_df(self):

        static_assumptions = pd.DataFrame()
        static_assumptions_values = []

        for assumption in self.list_static_assumptions:
            static_assumptions_values.append(self.dict_assumptions[assumption])

        static_assumptions['assumption'] = self.list_static_assumptions
        static_assumptions['value'] = static_assumptions_values

        r_rate = self.calc_r_reduction_outputs()

        infected_individuals_output, prop_transmission_reduction_output, secondary_case_reduction_output = self.calc_output_dfs()

        ons_input = self.format_time_matrix_to_df(self.dict_assumptions['proportion_population_testing_positive'], ['proportion_population_testing_positive'])
        ons_input['incidence_per_10000'] = self.dict_assumptions['incidence_per_10000']
        ons_input['population_testing_positive'] = self.dict_assumptions['population_testing_positive']
        ons_input['r_rate'] = self.dict_assumptions['r_rate']
        transmission_abated = pd.DataFrame.from_dict(self.dict_assumptions['cumulative_transmission_abated_lookup'], orient = 'index', columns =['cumulative_transmission_abated_from_ashcroft_curve'])
        transmission_abated = transmission_abated.rename_axis("day_of_isolation").reset_index()

        days_to_isolate = self.format_time_matrix_to_df(self.dict_assumptions['household_ctas_days_to_isolate'], ['household_ctas_days_to_isolate'])
        days_to_isolate['nonhousehold_ctas_days_to_isolate'] = self.dict_assumptions['nonhousehold_ctas_days_to_isolate']
        days_to_isolate['days_to_isolate_app'] = self.dict_assumptions['days_to_isolate_app']
        days_to_isolate['days_to_isolate_schools'] = self.dict_assumptions['days_to_isolate_schools']

        forward_transmission_abated, dictionary_transmission_abated = self.generate_matrix_onward_transmission_abated()
        forward_transmission_abated = self.format_time_matrix_to_df(forward_transmission_abated, self.group_list)
        compliance = self.format_time_matrix_to_df(self.support_functions.translate_assumptions_into_matrix(self.group_list, self.dict_assumptions, "isolation_compliance_mapping", self.fortnightly_periods), self.group_list)
        actuals_data = self.format_time_matrix_to_df(self.dict_assumptions['actuals_data'], self.list_group_excl_derived)
        PCR_PPV = self.support_functions.generate_PPV_for_tests(self.dict_assumptions)
        LFD_PPV = self.dict_assumptions['PPV_LFD']
        PPV = self.format_time_matrix_to_df(PCR_PPV, ["PCR_PPV"])
        PPV['LFD_PPV'] = LFD_PPV
        PPV['PPV_adjustment_for_contacts'] = DerivedCasesContacts().calc_PPV_adjustment_for_contacts(self.dict_assumptions['actuals_data_dictionary'], self.dict_assumptions['actuals_data_PPV_dictionary'])
        true_positive_actuals_data = self.format_time_matrix_to_df(self.dict_assumptions['actuals_data_PPV'], self.group_list)
        effective_isolation = self.format_time_matrix_to_df(self.calc_effective_isolation_by_group(), self.group_list)
        prop_transmission_reduction_time_group = self.calc_prop_transmission_reduction_by_group_df()

        attack_rates = self.support_functions.translate_assumptions_into_matrix(self.group_list, self.dict_assumptions, "attack_rate_mapping", self.fortnightly_periods)
        attack_rates = self.format_time_matrix_to_df(attack_rates.astype(np.float), self.group_list)

        prop_transmission_reduction_time = ons_input.copy()
        prop_transmission_reduction_time['proportion_transmission_reduction'] = self.calc_prop_transmission_reduction_over_time()
        prop_transmission_reduction_time['total_effective_isolation'] = self.calc_effective_isolation_by_group().sum(axis = 1)


        time_varying_assumption = self.format_time_matrix_to_df(self.dict_assumptions['proportion_cases_symptomatic'], ["proportion_cases_symptomatic"])
        time_varying_assumption['household_contacts_per_case_counterfactual'] = self.dict_assumptions['household_contacts_per_case_counterfactual']
        time_varying_assumption['app_exposure_notifications_sent'] = self.dict_assumptions['app_exposure_notifications_sent']
        time_varying_assumption['contacts_schools'] = self.dict_assumptions['contacts_schools']
        time_varying_assumption['prop_household_contacts_prev_cases'] = self.dict_assumptions['actuals_data_dictionary']['prop_household_contacts_prev_cases']
        time_varying_assumption['prop_nonhousehold_contacts_prev_cases'] = self.dict_assumptions['actuals_data_dictionary']['prop_nonhousehold_contacts_prev_cases']
        with pd.ExcelWriter(self.output_filename, datetime_format= 'dd/mm/yyyy') as writer:

            static_assumptions.to_excel(writer, sheet_name="INPUT_static_assumptions", index=False)
            ons_input.to_excel(writer, sheet_name="INPUT_ONS_estimates", index=False)
            transmission_abated.to_excel(writer, sheet_name="INPUT_ashcroft_abated", index=False)
            time_varying_assumption.to_excel(writer, sheet_name="INPUT_time_varying_assump", index=False)
            #cases_PCR_test_symp_pillar1.to_excel(writer, sheet_name="INPUT_symp_cases_split", index=False)
            days_to_isolate.to_excel(writer, sheet_name="INPUT_days_to_isolate", index=False)
            compliance.to_excel(writer, sheet_name="INPUT_compliance", index=False)
            attack_rates.to_excel(writer, sheet_name="INPUT_attack_rates", index=False)
            actuals_data.to_excel(writer, sheet_name="INPUT_actuals_data", index=False)
            PPV.to_excel(writer, sheet_name="CALC_PPV", index=False)
            true_positive_actuals_data.to_excel(writer, sheet_name="CALC_actuals_data_PPV", index=False)
            forward_transmission_abated.to_excel(writer, sheet_name="CALC_forward_transm_abated", index=False)
            effective_isolation.to_excel(writer, sheet_name="CALC_effective_isolation", index=False)
            prop_transmission_reduction_time_group.to_excel(writer, sheet_name="CALC_prop_transm_abated", index=False)
            prop_transmission_reduction_output.to_excel(writer, sheet_name="OUTPUT_prop_transm_abated", index=False)
            r_rate.to_excel(writer, sheet_name="CALC_r_rate", index=False)
            infected_individuals_output.to_excel(writer, sheet_name="OUTPUT_infected_population", index=False)
            secondary_case_reduction_output.to_excel(writer, sheet_name="CALC_secondary_case_reduction", index=False)

