import pandas as pd
import os


class PrepONSData:

    def __init__(self):

        self.ons_estimates = pd.read_excel(os.getcwd() + "/modellingvfm/inputs/ons_estimates.xlsx", sheet_name="ONS_model_input")
        self.ons_r_estimates = pd.read_excel(os.getcwd() + "/modellingvfm/inputs/ons_r_estimates.xlsx", sheet_name="ons_daily")
        self.ons_incidence_estimates = pd.read_excel(os.getcwd() + "/modellingvfm/inputs/ons_estimates.xlsx", sheet_name="incidence")

    def prep_ONS_data(self, fortnightly_periods):

        ons_estimates = self.ons_estimates
        ons_estimates = ons_estimates.rename(
            columns={'Estimated % testing positive for COVID-19': 'ons_proportion_popn_covid',
                     'Estimated number of people testing positive for COVID-19': 'ons_popn_testing_positive',
                     #'End of Period as Date': 'end_ons_period',
                     'Beginning of Period as Date': 'beginning_ons_period'})

        ons_estimates['beginning_ons_period'] = pd.to_datetime(
            ons_estimates['beginning_ons_period'], format="%d/%m/%Y")

        #ons_estimates['end_ons_period'] = pd.to_datetime(
        #    ons_estimates['end_ons_period'], format="%d/%m/%Y")

        ons_estimates = self.select_fortnight_periods_from_ONS(ons_estimates, fortnightly_periods)

        ons_proportion_popn_covid = ons_estimates[['fortnight_date', 'ons_proportion_popn_covid']]
        ons_popn_testing_positive = ons_estimates[['fortnight_date', 'ons_popn_testing_positive']]
        incidence_per_10000 = self.ons_incidence_estimates


        return ons_estimates, ons_popn_testing_positive, ons_proportion_popn_covid, incidence_per_10000

    def select_fortnight_periods_from_ONS(self, df, fortnightly_periods):

        list_of_fortnight_periods = list(fortnightly_periods['fortnight_date'])

        df_filtered = df[df['beginning_ons_period'].isin(list_of_fortnight_periods)]

        if df_filtered.shape[0] <= 0:
            print("error, fortnight periods chosen not in ONS periods")
        else:
            pass

        df_filtered = df_filtered.rename(
            columns={'beginning_ons_period': 'fortnight_date'})

        return df_filtered

    def prep_r_estimates(self, fortnightly_periods):

        ons_r_estimates = self.ons_r_estimates

        ons_r_estimates = ons_r_estimates.rename(
            columns={'Mean': 'r_rate'})

        ons_r_estimates['Date'] = pd.to_datetime(
            ons_r_estimates['Date'], format="%d/%m/%Y")

        df = pd.merge_asof(ons_r_estimates, fortnightly_periods, left_on=["Date"], right_on=["fortnight_date"],
                           direction="backward")

        df = df[['r_rate', 'fortnight_date']]

        df = df.groupby(['fortnight_date']).mean().reset_index()

        return df


