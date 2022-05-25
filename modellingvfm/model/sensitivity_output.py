from .transmission_reduction import TransmissionReduction
from .apply_variance import ApplyVariance
from .monte_carlo_simulation import MonteCarlo
import pandas as pd
import os



class SensitivityAnalysis:

    def __init__(self, groups):
        self.groups = groups
        self.output_filename_sensitivities = os.getcwd() + "/modellingvfm/outputs/sensitivity_variation.xlsx"

    def run_calc_for_sd_sensitivities(self, output_name):
        standard_deviation_assumptions, dict_of_means, fortnightly_periods, dict_assumptions, central_outputs = MonteCarlo(self.groups).generate_inputs()

        dict_static_variance = dict()
        for varying_assumption in standard_deviation_assumptions:
            dict_static_variance[varying_assumption] = 1

        input_values = ApplyVariance(standard_deviation_assumptions).merge_input_dictionaries(dict_of_means)

        sensitivity_table_dict = dict()
        sd_to_vary = [-2, -1, 0, 1, 2]

        for varying_assumption in standard_deviation_assumptions:
            temp_dict = dict()

            for variance in sd_to_vary:
                dict_of_variance = ApplyVariance(standard_deviation_assumptions).generate_dictionary_of_variance_sd_sensitivities(input_values, varying_assumption, dict_static_variance, variance)
                dict_assumptions_adjusted = ApplyVariance(standard_deviation_assumptions).update_dictionary_with_variance(dict_assumptions, dict_of_variance)
                output_of_sim = TransmissionReduction(dict_assumptions_adjusted, self.groups,fortnightly_periods).create_dictionary_storing_outputs()
                output_value = output_of_sim.get(output_name)
                output_value_summarised = output_value.mean()
                temp_dict[variance] = output_value_summarised

            sensitivity_table_dict[varying_assumption] = temp_dict

        df = self.generate_df_from_sensitivies_dict(sensitivity_table_dict)

        return df

    def get_normalised_sensitivities(self):
        standard_deviation_assumptions, dict_of_means, fortnightly_periods, dict_assumptions, central_outputs = MonteCarlo(self.groups).generate_inputs()
        dict_of_sensitivities = ApplyVariance(standard_deviation_assumptions).generate_dictionary_of_sensitivities(dict_of_means)

        sensitivity_df = pd.DataFrame.from_dict(dict_of_sensitivities, orient = "index", columns = ["normalised_sd_sensitivity"])
        sensitivity_df = sensitivity_df.rename_axis("assumption").reset_index()
        sensitivity_df = sensitivity_df.sort_values(by = ['normalised_sd_sensitivity'], ascending= False)

        return sensitivity_df

    def generate_df_from_sensitivies_dict(self, sensitivity_table_dict):

        df = pd.DataFrame.from_dict(sensitivity_table_dict)
        df = df.rename_axis("assumption").reset_index()
        df['assumption'] = "sd_" + df['assumption'].astype(str)
        df['assumption'] = df['assumption'].apply(lambda x: x.replace("-", "minus_"))

        df = df.T.reset_index()
        headers = df.iloc[0]
        df = df[1:]
        df.columns = headers

        return df

    def output_excel_sensitivites(self, list_outputs):

        with pd.ExcelWriter(self.output_filename_sensitivities) as writer:

            normalised_sensitivities = self.get_normalised_sensitivities()
            normalised_sensitivities.to_excel(writer, sheet_name="normalised_sensitivities", index=False)

            for output in list_outputs:
                df = SensitivityAnalysis(self.groups).run_calc_for_sd_sensitivities(output)

                if len(output) >= 31:
                    output = output[0:30]
                df.to_excel(writer, sheet_name=output, index=False)
