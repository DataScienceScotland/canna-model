from ..utils.config import ImportConfig
from ..utils.support_functions import SupportFunctions

from ..utils.assumption_prep.generate_actuals_data import PrepActualsData
from ..utils.assumption_prep.generate_attack_rate_assumptions import PrepAttackRateInput
from ..utils.assumption_prep.generate_day_to_isolate_assumptions import PrepDayToIsolateInput
from ..utils.assumption_prep.generate_compliance_assumptions import PrepComplianceInput
from ..utils.assumption_prep.generate_time_varying_assumption import PrepTimeVaryingAssumptionInput
from ..utils.assumption_prep.prep_ONS_data import PrepONSData

import pandas as pd
from datetime import timedelta, datetime
import os


class CentralAssumptions:

    def __init__(self, groups):
        """
        Return a single dictionary containing all input data and central assumptions as arrays / matrices.

        Output is used as a single input into the Transmission Reduction calculation.

        :param groups: list of case & contact groups to be consider in the calculations
        :type groups: list

        """
        self.support_functions = SupportFunctions()
        self.assumptions = ImportConfig('assumptions_config').get_yaml_config()

        start_date = datetime.strptime(self.assumptions['start_date'], "%d/%m/%Y")
        end_date = datetime.strptime(self.assumptions['end_date'], "%d/%m/%Y")
        self.fortnightly_periods = pd.DataFrame(self.support_functions.create_fortnight_df(start_date, end_date, timedelta(days=14)),columns=['fortnight_date'])

        self.groups, self.list_group_excl_derived, self.case_contact_volumes_generated = self.support_functions.rearrange_list_of_groups(groups)

        cumulative_transmission_abated = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/cumulative_transmission_abated.csv")
        cumulative_transmission_abated = zip(cumulative_transmission_abated['days_post_infection'], cumulative_transmission_abated['cumulative_transmission_abated'])
        self.cumulative_transmission_abated_dict = dict(cumulative_transmission_abated)

    def check_group_order(self, df, list_groups):
        """
        Ensures case & contact groups are always in the same order to ensure matrices align.

        :param df: the input dataframe containing case/contact group specific data
        :param list_groups: the required order of case/contact groups
        :return: an updated df with correctly ordered case/contact group data
        """
        column_order = ["fortnight_date"] + list_groups
        df = df[column_order]

        return df

    def check_fortnight_periods(self, df):
        """
        Ensures time varying inputs are using the correct fortnightly periods
        :param df: the input dataframe containing data that varies across fortnights
        :return: a dataframe containing the correct fortnightly periods, with nas replaced with 0s
        """
        df = pd.merge(self.fortnightly_periods, df, on="fortnight_date", validate="one_to_one", how = 'left')
        df = df.fillna(0)

        return df

    def convert_time_varying_df_to_array(self, df):
        """
        Translates time varying dataframe into matrix / array
        :param df: input dataframe containing data that varies across fortnights
        :return: array/matrix of df data
        """
        df = df.set_index('fortnight_date')
        array = df.to_numpy()

        return array

    def time_varying_assump_array_by_group(self, df, group):
        """
        Translates time varying dataframe that is split by case/contact group into a matrix/array
        :param df: dataframe containing data that varies across fortnights and by case/contact groups
        :param group: a list of case/contact groups
        :return: an array of the data contained in the input df
        """
        df = self.check_group_order(df, group)
        df = self.check_fortnight_periods(df)
        array = self.convert_time_varying_df_to_array(df)

        return array

    def generate_time_varying_assumption_dfs(self):
        """
        Reads in individual time varying input assumptions
        :return: a list of the assumption names, a list of the assumption data
        """
        transmission_abated_pcr = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("transmission_abated_pcr")
        transmission_abated_lfd = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("transmission_abated_lfd")
        transmission_abated_symptom_onset = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("transmission_abated_symptom_onset")
        proportion_cases_symptomatic = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("proportion_cases_symptomatic")
        app_exposure_notifications_sent = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("app_exposure_notifications_sent")
        days_to_isolate_app = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("days_to_isolate_app")
        contacts_schools = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("contacts_schools")
        days_to_isolate_schools = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("days_to_isolate_schools")
        PPV_LFD = PrepTimeVaryingAssumptionInput(self.fortnightly_periods).generate_time_varying_assumption("PPV_LFD")

        list_time_varying_assumption_names = ['transmission_abated_pcr',
                                              'transmission_abated_lfd',
                                              'transmission_abated_symptom_onset',
                                              'proportion_cases_symptomatic',
                                              'app_exposure_notifications_sent',
                                              'days_to_isolate_app',
                                              'contacts_schools',
                                              'days_to_isolate_schools',
                                              'PPV_LFD']

        list_time_varying_assumption_df = [transmission_abated_pcr,
                                           transmission_abated_lfd,
                                           transmission_abated_symptom_onset,
                                           proportion_cases_symptomatic,
                                           app_exposure_notifications_sent,
                                           days_to_isolate_app,
                                           contacts_schools,
                                           days_to_isolate_schools,
                                           PPV_LFD]

        return list_time_varying_assumption_names, list_time_varying_assumption_df

    def add_time_varying_assumptions_to_dict(self, dictionary, list_time_varying_assumption_names, list_time_varying_assumption_df):
        """
        Returns an updated dictionary
        :param dictionary:
        :param list_time_varying_assumption_names:
        :param list_time_varying_assumption_df:
        :return:
        """
        new_dictionary = dictionary.copy()

        for i in range(0, len(list_time_varying_assumption_names)):
            assumption_name = list_time_varying_assumption_names[i]
            assumption_df = list_time_varying_assumption_df[i]

            new_dictionary[assumption_name] = self.time_varying_assump_array_by_group(assumption_df, [assumption_name])

        return new_dictionary

    def prep_ons_data(self):
        prep_ons_data = PrepONSData()
        ons_fortnight, ons_popn_testing_positive, ons_proportion_popn_covid, incidence_per_10000 = prep_ons_data.prep_ONS_data(self.fortnightly_periods)
        ons_r_rate = prep_ons_data.prep_r_estimates(self.fortnightly_periods)

        return ons_fortnight, ons_popn_testing_positive, ons_proportion_popn_covid, ons_r_rate, incidence_per_10000

    def create_inputs_for_attack_rate(self):
        attack_rates = PrepAttackRateInput(self.fortnightly_periods).get_time_varying_assumption()
        attack_rates = self.check_fortnight_periods(attack_rates)

        attack_rate_non_household = attack_rates[['fortnight_date', 'Adjusted_Non_Household_Attack_rate']].set_index('fortnight_date').to_numpy()
        attack_rate_household = attack_rates[['fortnight_date', 'Adjusted_Household_Attack_rate']].set_index( 'fortnight_date').to_numpy()
        attack_rate_nhh_2_16 = attack_rates[['fortnight_date', 'nhh_2-16_attack_rate']].set_index('fortnight_date').to_numpy()

        return attack_rate_non_household, attack_rate_household, attack_rate_nhh_2_16

    def create_individual_inputs_for_derivation_of_actuals(self, df_actuals):
        df = self.check_fortnight_periods(df_actuals)

        actuals_data_dictionary = dict()

        actuals_data_dictionary['contacts_household_reached'] = df[['fortnight_date', 'contacts_household_reached']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['contacts_nonhousehold_reached'] = df[['fortnight_date', 'contacts_nonhousehold_reached']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_PCR_test_symp'] = df[['fortnight_date', 'cases_PCR_test_symp']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_PCR_test_asymp'] = df[['fortnight_date', 'cases_PCR_test_asymp']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_LFD_test_asymp_assisted'] = df[['fortnight_date', 'cases_LFD_test_asymp_assisted']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_LFD_test_asymp_selftest'] = df[['fortnight_date', 'cases_LFD_test_asymp_selftest']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_ConfPCR_test'] = df[['fortnight_date', 'cases_ConfPCR_test']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['cases_ConfPCR_test_symp'] = df[['fortnight_date', 'cases_ConfPCR_test_symp']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['prop_household_contacts_prev_cases'] = df[['fortnight_date', 'prop_household_contacts_prev_cases']].set_index('fortnight_date').to_numpy()
        actuals_data_dictionary['prop_nonhousehold_contacts_prev_cases'] = df[['fortnight_date', 'prop_nonhousehold_contacts_prev_cases']].set_index('fortnight_date').to_numpy()

        return actuals_data_dictionary

    def dictionary_central_assumptions(self):
        central_assumptions = dict()

        # Preps data to be included in dictionary
        actuals_df = PrepActualsData(self.fortnightly_periods, self.groups, self.case_contact_volumes_generated).generate_actuals_data()
        list_time_varying_assumption_names, list_time_varying_assumption_df = self.generate_time_varying_assumption_dfs()
        ons_fortnight, ons_popn_testing_positive, ons_propn_popn_testing_positive, r_rate, incidence_per_10000 = self.prep_ons_data()
        attack_rate_non_household, attack_rate_household, attack_rate_nhh_2_16 = self.create_inputs_for_attack_rate()
        list_day_to_isolate_assump = PrepDayToIsolateInput(self.fortnightly_periods).return_individual_day_to_isolate_assumptions()
        list_compliance_assump = PrepComplianceInput(self.fortnightly_periods).return_individual_compliance_assumptions()

        incidence_per_10000['population_testing_positive'] = incidence_per_10000["incidence_per_10000"] * (self.assumptions["population_size"]/10000)

        # adds assumptions to the dictionary
        ## adds a time varying assumption to the dictionary
        ## converts the assumption to array if a single column, or converts it into a matrix in order of inputter list
        central_assumptions['actuals_data'] = self.time_varying_assump_array_by_group(actuals_df, self.list_group_excl_derived)
        central_assumptions['proportion_population_testing_positive'] = self.time_varying_assump_array_by_group(ons_propn_popn_testing_positive, ['ons_proportion_popn_covid'])
        central_assumptions['incidence_per_10000'] = self.time_varying_assump_array_by_group(incidence_per_10000, ['incidence_per_10000'])
        central_assumptions['population_testing_positive'] = self.time_varying_assump_array_by_group(incidence_per_10000, ['population_testing_positive'])
        central_assumptions['r_rate'] = self.time_varying_assump_array_by_group(r_rate, ['r_rate'])
        central_assumptions['household_ctas_days_to_isolate'] = self.time_varying_assump_array_by_group(list_day_to_isolate_assump[0], ["household_ctas_days_to_isolate"])
        central_assumptions['nonhousehold_ctas_days_to_isolate'] = self.time_varying_assump_array_by_group(list_day_to_isolate_assump[1], ["nonhousehold_ctas_days_to_isolate"])
        central_assumptions['contact_compliance'] = self.time_varying_assump_array_by_group(list_compliance_assump[0], ["contact_compliance"])
        central_assumptions['case_symp_compliance'] = self.time_varying_assump_array_by_group(list_compliance_assump[1], ["case_symp_compliance"])
        central_assumptions['case_positive_test_compliance'] = self.time_varying_assump_array_by_group(list_compliance_assump[2], ["case_positive_test_compliance"])

        ## add time varying assumptions from the specific time varying assumption csv
        central_assumptions = self.add_time_varying_assumptions_to_dict(central_assumptions, list_time_varying_assumption_names, list_time_varying_assumption_df)

        ## adds assumptions that are already in the correct format (i.e. an array or a dictionary of arrays)
        central_assumptions['attack_rate_non_household'] = attack_rate_non_household
        central_assumptions['attack_rate_household'] = attack_rate_household
        central_assumptions['attack_rate_nhh_2_16'] = attack_rate_nhh_2_16
        central_assumptions['dictionary_of_group_indices'] = self.support_functions.create_dictionary_of_group_indices(self.groups, self.assumptions["groupings"])
        central_assumptions['dictionary_of_subgroup_indices'] = self.support_functions.create_dictionary_of_indices(self.groups)
        central_assumptions['actuals_data_dictionary'] = self.create_individual_inputs_for_derivation_of_actuals(actuals_df)

        # adds assumptions directly from assumption config, including mappings
        central_assumptions['PCR_sensitivity'] = self.assumptions["PCR_sensitivity"]
        central_assumptions['PCR_specificity'] = self.assumptions["PCR_specificity"]
        central_assumptions['population_size'] = self.assumptions["population_size"]
        central_assumptions['static_assumptions'] = self.assumptions["static_assumptions"]
        central_assumptions['variance_correlations'] = self.assumptions["variance_correlations"]
        central_assumptions['isolation_compliance_mapping'] = self.assumptions["isolation_compliance_mapping"]
        central_assumptions['attack_rate_mapping'] = self.assumptions["attack_rate_mapping"]
        central_assumptions['onward_transmission_abated_mapping'] = self.assumptions["onward_transmission_abated_mapping"]
        central_assumptions['cumulative_transmission_abated_lookup'] = self.cumulative_transmission_abated_dict

        return central_assumptions, self.fortnightly_periods['fortnight_date'].values
