import pandas as pd
import os
from ..config import ImportConfig


class PrepDayToIsolateInput:

    def __init__(self, fortnightly_periods):
        self.assumptions = ImportConfig('assumptions_config').get_yaml_config()
        self.fortnightly_periods = fortnightly_periods
        self.raw_actuals_data = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/mean_days_exposure_completion.csv")

    def return_ctas_day_to_isolate(self):

        temp_df = self.raw_actuals_data[['date_completed', "mean_days_between_exposure_completion_contact_household", "mean_days_between_exposure_completion_contact_non_household"]].copy()
        temp_df["date_completed"] = pd.to_datetime(temp_df["date_completed"], format = "%d/%m/%Y")

        df = pd.merge_asof(temp_df, self.fortnightly_periods, left_on=["date_completed"], right_on=["fortnight_date"],
                           direction="backward")
        df = df.drop(['date_completed'], axis=1)

        df = df.groupby(['fortnight_date']).mean().reset_index()



        return df

    def return_individual_day_to_isolate_assumptions(self):

        ctas_assumptions = self.return_ctas_day_to_isolate()

        ctas_assumptions = ctas_assumptions.rename(
            columns={'mean_days_between_exposure_completion_contact_household': 'household_ctas_days_to_isolate',
                     'mean_days_between_exposure_completion_contact_non_household': 'nonhousehold_ctas_days_to_isolate'})

        household_ctas_days_to_isolate = ctas_assumptions[["fortnight_date", 'household_ctas_days_to_isolate']]
        nonhousehold_ctas_days_to_isolate = ctas_assumptions[["fortnight_date", 'nonhousehold_ctas_days_to_isolate']]

        list_days_to_isolate_assumptions = [household_ctas_days_to_isolate, nonhousehold_ctas_days_to_isolate]

        return list_days_to_isolate_assumptions
