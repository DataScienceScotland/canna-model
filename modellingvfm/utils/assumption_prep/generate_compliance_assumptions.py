import pandas as pd
import os

from ..config import ImportConfig


class PrepComplianceInput:

    def __init__(self, fortnightly_periods):
        self.assumptions = ImportConfig('assumptions_config').get_yaml_config()
        self.compliance_mapping = self.assumptions['isolation_compliance_mapping']
        self.compliance_rates = pd.read_csv(os.getcwd() + "/modellingvfm/inputs/compliance_rates.csv")
        self.fortnightly_periods = fortnightly_periods

    def generate_compliance_rates(self, groups):
        df = self.compliance_rates[['Date']].copy()
        df['Date'] = pd.to_datetime(df['Date'], format = "%d/%m/%Y")

        for group in groups:
            df[group] = self.compliance_rates[self.compliance_mapping.get(group)]

        df = df.dropna()

        df = pd.merge_asof(self.fortnightly_periods, df.sort_values('Date'), left_on="fortnight_date", right_on="Date",
                           direction="forward")

        df = df.drop(["Date"], axis=1)

        return df

    def return_individual_compliance_assumptions(self):

        df = self.compliance_rates.copy()
        df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
        df = pd.merge_asof(self.fortnightly_periods, df.sort_values('Date'), left_on="fortnight_date", right_on="Date",
                           direction="forward")


        contact_compliance = df[["fortnight_date", 'contact_compliance']]
        case_symp_compliance = df[["fortnight_date", 'case_symp_compliance']]
        case_positive_test_compliance = df[["fortnight_date", 'case_positive_test_compliance']]


        compliance_assumptions = [contact_compliance,
                                            case_symp_compliance,
                                            case_positive_test_compliance]

        return compliance_assumptions


