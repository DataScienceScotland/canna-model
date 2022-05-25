from .generate_central_assumptions import CentralAssumptions
from .transmission_reduction import TransmissionReduction
from .apply_variance import ApplyVariance
from ..utils.config import ImportConfig
import numpy as np
import time
import pandas as pd
import os
import matplotlib.pyplot as plt


class MonteCarlo:

    def __init__(self, groups):
        self.groups = groups
        self.output_filepath = os.getcwd() + "/modellingvfm/outputs/"
        self.output_filename_plot = os.getcwd() + "/modellingvfm/outputs/charts/"
        self.output_filename_plot_assumptions = os.getcwd() + "/modellingvfm/outputs/charts/assumptions/"
        self.output_filename_sensitivities = os.getcwd() + "/modellingvfm/outputs/sensitivities.csv"
        self.output_filename_plot_outputs = os.getcwd() + "/modellingvfm/outputs/charts/outputs/"

    def generate_inputs(self):
        standard_deviation_assumptions = ImportConfig('standard_deviation_assumptions').get_yaml_config()
        dict_assumptions, fortnightly_periods = CentralAssumptions(self.groups).dictionary_central_assumptions()
        dict_of_means = ApplyVariance(standard_deviation_assumptions).generate_dictionary_of_means(dict_assumptions)

        dict_of_variance = ApplyVariance(standard_deviation_assumptions).generate_dictionary_of_variance(dict_of_means)
        dict_of_variance = {x: 1 for x in dict_of_variance}
        dict_assumptions_adjusted = ApplyVariance(standard_deviation_assumptions).update_dictionary_with_variance(dict_assumptions, dict_of_variance)

        central_outputs = TransmissionReduction(dict_assumptions_adjusted, self.groups, fortnightly_periods).create_dictionary_storing_outputs()


        return standard_deviation_assumptions, dict_of_means, fortnightly_periods, dict_assumptions, central_outputs

    def create_list_of_varying_assumptions(self, sd_assumptions, dictionary):
        variance_correlations = dictionary.get('variance_correlations')
        list_varying_assumptions = [*sd_assumptions]
        output_list = []

        for assumption in list_varying_assumptions:
            if assumption in dictionary:
                output_list.append(assumption)
            else:
                correlated_assumptions = variance_correlations.get(assumption)
                output_list.extend(correlated_assumptions)


        return output_list

    def monte_carlo_simulation(self, n_of_sims):
        start_data_prep = time.time()
        standard_deviation_assumptions, dict_of_means, fortnightly_periods, dict_assumptions, central_outputs = self.generate_inputs()
        dict_of_outputs = central_outputs.copy()

        list_varying_assumptions = self.create_list_of_varying_assumptions(standard_deviation_assumptions, dict_assumptions)
        dict_of_assumption_outputs = {list_varying_assumptions: dict_assumptions[list_varying_assumptions] for list_varying_assumptions in list_varying_assumptions}
        end_data_prep = time.time()


        print("Data prep complete. It took " + str(round((end_data_prep - start_data_prep), 3)) + " seconds")

        start_simulation = time.time()

        for i in range(0, n_of_sims):
            dict_of_variance = ApplyVariance(standard_deviation_assumptions).generate_dictionary_of_variance(dict_of_means)
            dict_assumptions_adjusted = ApplyVariance(standard_deviation_assumptions).update_dictionary_with_variance(dict_assumptions, dict_of_variance)
            output_of_sim = TransmissionReduction(dict_assumptions_adjusted, self.groups, fortnightly_periods).create_dictionary_storing_outputs()
            dict_of_outputs = {key: np.append(dict_of_outputs[key], output_of_sim[key], axis=1) for key in dict_of_outputs}

            dict_assumptions_adjusted = {list_varying_assumptions: dict_assumptions_adjusted[list_varying_assumptions] for list_varying_assumptions in list_varying_assumptions}
            for key in dict_of_assumption_outputs:
                if isinstance(dict_of_assumption_outputs[key], float):
                    list_of_assumptions = [dict_of_assumption_outputs[key], dict_assumptions_adjusted[key]]
                    dict_of_assumption_outputs[key] = np.array(list_of_assumptions)
                elif dict_of_assumption_outputs[key].ndim <= 1:
                    dict_of_assumption_outputs[key] = np.append(dict_of_assumption_outputs[key],dict_assumptions_adjusted[key])
                else:
                    dict_of_assumption_outputs[key] = np.append(dict_of_assumption_outputs[key], dict_assumptions_adjusted[key], axis = 1)

        end_simulation = time.time()
        time_to_run_all_sims = end_simulation - start_simulation
        time_per_sim = time_to_run_all_sims / n_of_sims

        print("Monte Carlo simulations complete. " + str(n_of_sims) + " simulations ran in " + str(round(time_to_run_all_sims / 60, 3)) + " minutes")
        print("On average, each simulation took " + str(round(time_per_sim,3)) + " seconds")
        print("It would take approximately " + str(round((time_per_sim * 100000)/60, 3)) + " minutes to run 100,000 simulations")


        return dict_of_outputs, dict_of_assumption_outputs, n_of_sims

    def average_output_from_monte_carlo(self, dict_of_outputs, n_of_sims):
        start_summarisation = time.time()

        summarised_monte_carlo_outputs = dict()

        for output in dict_of_outputs:
            temp_dict = dict()
            array_to_summarise = dict_of_outputs.get(output)
            temp_dict['central_assumptions'] = [row[0] for row in array_to_summarise]
            temp_dict['mean'] = np.mean(array_to_summarise, axis=1, keepdims = True)
            temp_dict['sd'] = np.std(array_to_summarise, axis=1, keepdims = True)
            temp_dict['percentile_95'] = np.percentile(array_to_summarise, 95, axis=1, keepdims = True)
            temp_dict['percentile_5'] = np.percentile(array_to_summarise, 5, axis=1, keepdims=True)

            summarised_monte_carlo_outputs[output] = temp_dict

        end_summarisation = time.time()
        time_taken_to_summarise_data = end_summarisation - start_summarisation

        print("Aggregations of Monte Carlo outputs complete. It took " + str(round(time_taken_to_summarise_data, 3)) + " seconds to aggregate outputs for " + str(n_of_sims)+ " simulations")

        return summarised_monte_carlo_outputs

    def average_output_from_monte_carlo_assumptions(self, dict_of_outputs):
        summarised_monte_carlo_outputs = dict()

        for output in dict_of_outputs:
            temp_dict = dict()
            array_to_summarise = dict_of_outputs.get(output)

            if array_to_summarise.ndim <= 1:
                mean_central_assumptions = array_to_summarise
            else:
                mean_central_assumptions = [row[0] for row in array_to_summarise]

            temp_dict['central_assumptions'] = np.mean(mean_central_assumptions)
            temp_dict['mean'] = np.mean(array_to_summarise)
            temp_dict['sd'] = np.std(array_to_summarise)
            temp_dict['percentile_95'] = np.percentile(array_to_summarise, 95)
            temp_dict['percentile_5'] = np.percentile(array_to_summarise, 5)

            summarised_monte_carlo_outputs[output] = temp_dict

        return summarised_monte_carlo_outputs

    def generate_histogram(self, array_to_use, file_path, file_name):
        output_name = file_path + file_name + ".png"
        plt.clf()
        plt.hist(array_to_use, bins = 50)
        plt.title(file_name)
        plt.savefig(output_name)

    def output_multiple_charts(self, dict_of_outputs, filepath):
        filepath_name = None
        if filepath == "outputs":
            filepath_name = self.output_filename_plot_outputs
        elif filepath == "assumptions":
            filepath_name = self.output_filename_plot_assumptions
        else:
            print("error: no filepath set")

        for assumption in dict_of_outputs:
            array_to_use = dict_of_outputs.get(assumption)
            mean_per_sim = array_to_use.mean(axis = 0)
            self.generate_histogram(mean_per_sim, filepath_name, assumption)



    def high_level_outputs(self, dict_of_outputs):

        r_reduction_from_NHSTT = dict_of_outputs.get('r_red_from_NHSTT')
        r_reduction_from_TTI = dict_of_outputs.get('r_red_from_TTI')
        prop_transmission_abated_NHSTT = dict_of_outputs.get('pta_NHSTT_total')

        r_reduction_from_NHSTT_overall_per_sim = r_reduction_from_NHSTT.mean(axis = 0)
        r_reduction_from_TTI_overall_per_sim = r_reduction_from_TTI.mean(axis=0)
        prop_transmission_abated_NHSTT_overall_per_sim = prop_transmission_abated_NHSTT.mean(axis=0)

        r_reduction_from_NHSTT_overall = r_reduction_from_NHSTT_overall_per_sim.mean()
        r_reduction_from_TTI_overall = r_reduction_from_TTI_overall_per_sim.mean()
        prop_transmission_abated_NHSTT_overall = prop_transmission_abated_NHSTT_overall_per_sim.mean()

        self.generate_histogram(r_reduction_from_NHSTT_overall_per_sim, self.output_filename_plot, "histogram_r_reduction_NHSTT")
        self.generate_histogram(r_reduction_from_TTI_overall_per_sim,self.output_filename_plot, "histogram_r_reduction_TTI")
        self.generate_histogram(prop_transmission_abated_NHSTT_overall_per_sim,self.output_filename_plot, "histogram_prop_transmission_abated_NHSTT")

        print("Overall reduction from NHSTT is " + str(r_reduction_from_NHSTT_overall))
        print("Overall reduction from TTI is " + str(r_reduction_from_TTI_overall))


    def format_time_matrix_to_df(self, output, fortnightly_periods):

        df = pd.DataFrame(data = output.get('central_assumptions'), index = fortnightly_periods, columns = ['central_assumptions'])
        df['mean'] = output.get('mean')
        df['sd'] = output.get('sd')
        df['percentile_95'] = output.get('percentile_95')
        df['percentile_5'] = output.get('percentile_5')

        df.reset_index(level = 0, inplace = True)
        df = df.rename(columns = {df.columns[0]: "fortnight_start_date"})

        return df

    def export_output_dict_to_excel(self, summarised_monte_carlo_outputs):
        dict_assumptions, fortnightly_periods = CentralAssumptions(self.groups).dictionary_central_assumptions()

        filename = self.output_filepath + "summarised_monte_carlo_output.xlsx"

        with pd.ExcelWriter(filename, datetime_format= 'dd/mm/yyyy') as writer:

            for output in summarised_monte_carlo_outputs:
                output_formatted = self.format_time_matrix_to_df(summarised_monte_carlo_outputs.get(output), fortnightly_periods)

                if len(output) >= 31:
                    output = output[0:30]
                output_formatted.to_excel(writer, sheet_name=output, index=False)

    def export_output_dict_assumptions_to_excel(self, summarised_dict):
        filename = self.output_filepath + "summarised_input_assumptions.xlsx"

        output_df = pd.DataFrame(columns = ["fortnight_start_date", "central_assumptions", "mean", "sd", "percentile_95", "percentile_5"])


        for output in summarised_dict:
            output_formatted = self.format_time_matrix_to_df(summarised_dict.get(output), [output])
            output_df = output_df.append(output_formatted, ignore_index=True)

        with pd.ExcelWriter(filename, datetime_format= 'dd/mm/yyyy') as writer:
                output_df.to_excel(writer, sheet_name="all_assumptions", index=False)


