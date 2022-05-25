import pandas as pd
import os

from ..config import ImportConfig


class PrepAttackRateInput:

    def __init__(self, fortnightly_periods):
        self.assumptions = ImportConfig('assumptions_config').get_yaml_config()
        self.attack_rates = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/attack_rates.csv")
        self.fortnightly_periods = fortnightly_periods

    def get_time_varying_assumption(self):
        df = self.attack_rates.copy()
        df['date_created'] = pd.to_datetime(df['date_created'], format = "%d/%m/%Y")


        df = pd.merge_asof(self.fortnightly_periods, df.sort_values('date_created'), left_on="fortnight_date",
                           right_on="date_created",
                           direction="forward")

        df = df.drop(["date_created"], axis=1)

        return df


