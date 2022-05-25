import pandas as pd
import os


class PrepTimeVaryingAssumptionInput:

    def __init__(self, fortnightly_periods):
        self.time_varying_assumptions = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/time_varying_assumptions.csv")
        self.fortnightly_periods = fortnightly_periods

    def generate_time_varying_assumption(self, assumption_name):
        df = self.time_varying_assumptions[['date_created', assumption_name]].copy()
        df['date_created'] = pd.to_datetime(df['date_created'], format = "%d/%m/%Y")

        df = df.dropna()

        df = pd.merge_asof(self.fortnightly_periods, df.sort_values('date_created'), left_on="fortnight_date", right_on="date_created",
                           direction="forward")

        df = df.drop(["date_created"], axis=1)

        return df