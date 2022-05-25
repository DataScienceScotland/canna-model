import pandas as pd
import os
from datetime import datetime
from ..config import ImportConfig


class PrepActualsData:

    def __init__(self, fortnightly_periods, list_groups, case_contact_volumes_generated):

        # read in output of SQL query
        self.df = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/CTAS_query.csv")
        time_varying_assumptions = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/time_varying_assumptions.csv")
        self.overlap_rate_cases = time_varying_assumptions[['date_created', 'overlap_rate_cases']]

        self.assumptions = ImportConfig('assumptions_config').get_yaml_config()
        self.start_date = datetime.strptime(self.assumptions['start_date'], "%d/%m/%Y")
        self.end_date = datetime.strptime(self.assumptions['end_date'], "%d/%m/%Y")

        # identify fortnightly periods (starting on Mondays)
        self.fortnightly_periods = fortnightly_periods

        self.list_groups = list_groups.copy()
        for group in case_contact_volumes_generated:
            if group in list_groups:
                self.list_groups.remove(group)
            else:
                pass

    def generate_contacts_data(self, df):
        df['contacts_only_household_reached'] = df['n_of_reached_hh_contacts_only']
        df['contacts_only_nonhousehold_reached'] = df['n_of_reached_nhh_contacts_only']

        df['first_contacts_then_cases_household_reached'] = df['n_of_reached_hh_first_contact_then_case']
        df['first_contacts_then_cases_nonhousehold_reached'] = df['n_of_reached_nhh_first_contact_then_case']

        df['contacts_household_reached'] = df['contacts_only_household_reached'] + df[
            'first_contacts_then_cases_household_reached']
        df['contacts_nonhousehold_reached'] = df['contacts_only_nonhousehold_reached'] + df[
            'first_contacts_then_cases_nonhousehold_reached']

        return df

    def generate_cases_PCR_data(self, df):

        df['cases_only_PCR_test_symp'] = df['n_of_cases_only_PCR_Symptomatic_Pillar_2']
        df['cases_only_PCR_test_asymp'] = df['n_of_cases_only_PCR_Asymptomatic_Pillar_2']
        df['cases_only_PCR_test_pillar1'] = df['n_of_cases_only_Symptomatic_Pillar_1'] + df[
            'n_of_cases_only_Asymptomatic_Pillar_1']
        df['cases_only_PCR_test_symp_pillar1'] = df['n_of_cases_only_Symptomatic_Pillar_1']

        df['first_case_then_contact_PCR_test_symp'] = df['n_of_first_case_then_contact_PCR_Symptomatic_Pillar_2']
        df['first_case_then_contact_PCR_test_asymp'] = df['n_of_first_case_then_contact_PCR_Asymptomatic_Pillar_2']
        df['first_case_then_contact_PCR_test_pillar1'] = df['n_of_first_case_then_contact_Symptomatic_Pillar_1'] + df[
            'n_of_first_case_then_contact_Asymptomatic_Pillar_1']
        df['first_case_then_contact_PCR_test_symp_pillar1'] = df['n_of_first_case_then_contact_Symptomatic_Pillar_1']

        df['cases_PCR_test_symp'] = df['cases_only_PCR_test_symp'] + df['first_case_then_contact_PCR_test_symp']
        df['cases_PCR_test_asymp'] = df['cases_only_PCR_test_asymp'] + df['first_case_then_contact_PCR_test_asymp']
        df['cases_PCR_test_pillar1'] = df['cases_only_PCR_test_pillar1'] + df[
            'first_case_then_contact_PCR_test_pillar1']
        df['cases_PCR_test_symp_pillar1'] = df['cases_only_PCR_test_symp_pillar1'] + df[
            'first_case_then_contact_PCR_test_symp_pillar1']

        return df

    def generate_cases_LFD_data(self, df):

        df["cases_only_ConfPCR_test_symp"] = df['n_of_cases_only_CONF_PCR_Symptomatic_Pillar_2']
        df["cases_only_ConfPCR_test_asymp"] = df['n_of_cases_only_CONF_PCR_Asymptomatic_Pillar_2']
        df["cases_only_ConfPCR_test"] = df['cases_only_ConfPCR_test_symp'] + df["cases_only_ConfPCR_test_asymp"]
        df["cases_only_LFD_test_asymp_selftest"] = df['n_of_cases_only_LFT_selfserve'] * self.overlap_rate_cases[
            'overlap_rate_cases']
        df["cases_only_LFD_test_asymp_assisted"] = df['n_of_cases_only_LFT_supervised']

        df["first_case_then_contact_ConfPCR_test_symp"] = df[
            'n_of_first_case_then_contact_CONF_PCR_Symptomatic_Pillar_2']
        df["first_case_then_contact_ConfPCR_test_asymp"] = df[
            'n_of_first_case_then_contact_CONF_PCR_Asymptomatic_Pillar_2']
        df["first_case_then_contact_ConfPCR_test"] = df['first_case_then_contact_ConfPCR_test_symp'] + df[
            "first_case_then_contact_ConfPCR_test_asymp"]
        df["first_case_then_contact_LFD_test_asymp_selftest"] = df['n_of_first_case_then_contact_LFT_selfserve'] * \
                                                                self.overlap_rate_cases['overlap_rate_cases']
        df["first_case_then_contact_LFD_test_asymp_assisted"] = df['n_of_first_case_then_contact_LFT_supervised']

        df["cases_ConfPCR_test_symp"] = df['cases_only_ConfPCR_test_symp'] + df[
            "first_case_then_contact_ConfPCR_test_symp"]
        df["cases_ConfPCR_test_asymp"] = df['cases_only_ConfPCR_test_asymp'] + df[
            "first_case_then_contact_ConfPCR_test_asymp"]
        df["cases_ConfPCR_test"] = df['cases_only_ConfPCR_test'] + df["first_case_then_contact_ConfPCR_test"]
        df["cases_LFD_test_asymp_selftest"] = df['cases_only_LFD_test_asymp_selftest'] + df[
            "first_case_then_contact_LFD_test_asymp_selftest"]
        df["cases_LFD_test_asymp_assisted"] = df['cases_only_LFD_test_asymp_assisted'] + df[
            "first_case_then_contact_LFD_test_asymp_assisted"]

        return df

    def ratio_first_cases_then_contacts(self, df):

        df['all_contacts'] = df['n_of_reached_hh_contacts_only'] + \
                             df['n_of_reached_nhh_contacts_only'] + \
                             df['n_of_reached_hh_first_contact_then_case'] + \
                             df['n_of_reached_nhh_first_contact_then_case']

        df['all_household_contacts'] = df['n_of_reached_hh_contacts_only'] + df['n_of_reached_hh_first_contact_then_case']

        df['all_non_household_contacts'] = df['n_of_reached_nhh_contacts_only'] + df['n_of_reached_nhh_first_contact_then_case']

        df['all_first_case_then_contact'] = df['n_of_first_case_then_contact_PCR_Symptomatic_Pillar_2'] + \
                                            df['n_of_first_case_then_contact_PCR_Asymptomatic_Pillar_2'] + \
                                            df['n_of_first_case_then_contact_Asymptomatic_Pillar_1'] + \
                                            df['n_of_first_case_then_contact_Symptomatic_Pillar_1'] + \
                                            df['n_of_first_case_then_contact_CONF_PCR_Symptomatic_Pillar_2'] + \
                                            df['n_of_first_case_then_contact_CONF_PCR_Asymptomatic_Pillar_2'] + \
                                            df['n_of_first_case_then_contact_LFT_selfserve'] + \
                                            df['n_of_first_case_then_contact_LFT_supervised']

        df['ratio_first_cases_then_contacts'] = df['all_first_case_then_contact'] / (df['all_first_case_then_contact'] +
                                                                                     df['all_contacts'])

        df['prop_household_contacts_prev_cases'] = df['n_of_reached_hh_first_case_then_contact_keep_contact'] / (df['n_of_reached_hh_first_case_then_contact_keep_contact'] + df['all_household_contacts'])
        df['prop_nonhousehold_contacts_prev_cases'] = df['n_of_reached_nhh_first_case_then_contact_keep_contact'] / (df['n_of_reached_nhh_first_case_then_contact_keep_contact'] + df['all_non_household_contacts'])

        return df

    def generate_actuals_data(self):

        df = self.df[['date_created',
                      'n_of_reached_hh_contacts_only',
                      'n_of_reached_nhh_contacts_only',
                      'n_of_reached_hh_first_contact_then_case',
                      'n_of_reached_nhh_first_contact_then_case',

                      'n_of_cases_only_PCR_Symptomatic_Pillar_2',
                      'n_of_cases_only_PCR_Asymptomatic_Pillar_2',
                      'n_of_cases_only_Asymptomatic_Pillar_1',
                      'n_of_cases_only_Symptomatic_Pillar_1',
                      'n_of_cases_only_CONF_PCR_Symptomatic_Pillar_2',
                      'n_of_cases_only_CONF_PCR_Asymptomatic_Pillar_2',
                      'n_of_cases_only_LFT_selfserve',
                      'n_of_cases_only_LFT_supervised',

                      'n_of_first_case_then_contact_PCR_Symptomatic_Pillar_2',
                      'n_of_first_case_then_contact_PCR_Asymptomatic_Pillar_2',
                      'n_of_first_case_then_contact_Asymptomatic_Pillar_1',
                      'n_of_first_case_then_contact_Symptomatic_Pillar_1',
                      'n_of_first_case_then_contact_CONF_PCR_Symptomatic_Pillar_2',
                      'n_of_first_case_then_contact_CONF_PCR_Asymptomatic_Pillar_2',
                      'n_of_first_case_then_contact_LFT_selfserve',
                      'n_of_first_case_then_contact_LFT_supervised',

                      #'n_of_dd_first_case_then_contact_unique',
                      #'n_of_dd_first_contact_then_case_unique',

                      'n_of_reached_hh_first_case_then_contact_keep_contact',
                      'n_of_reached_nhh_first_case_then_contact_keep_contact'

                      ]].copy()

        df['date_created'] = pd.to_datetime(df['date_created'], format="%d/%m/%Y")
        df = df[df['date_created'] <= self.end_date]
        df = df[df['date_created'] >= self.start_date]

        df = pd.merge_asof(df, self.fortnightly_periods, left_on=["date_created"], right_on=["fortnight_date"],
                           direction="backward")

        df = df.groupby(['fortnight_date']).sum().reset_index()

        df = self.generate_contacts_data(df)
        df = self.generate_cases_PCR_data(df)
        df = self.generate_cases_LFD_data(df)
        df = self.ratio_first_cases_then_contacts(df)

        return df
