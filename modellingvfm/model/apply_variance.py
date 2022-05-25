import numpy as np
import math

class ApplyVariance:

    def __init__(self, standard_deviation_assumptions):
        self.standard_deviation_assumptions = standard_deviation_assumptions
        self.assumptions_to_vary = [*self.standard_deviation_assumptions]

        self.list_assumptions_not_rates = ['population_testing_positive', 'days_to_isolate_CTAS', 'additional_contacts_per_case_app', 'household_contacts_per_case_counterfactual', 'r_rate', 'isolate_on_PCR_positive_test', 'isolate_on_LFD_positive_test', 'isolate_on_symptom_onset']

    def generate_dictionary_of_means(self, dictionary):
        variance_correlations = dictionary['variance_correlations']
        correlated_assumptions = [*variance_correlations]
        individual_assumptions = [x for x in self.assumptions_to_vary if x not in correlated_assumptions]

        dictionary_of_means = dict()
	
        for individual_assumption in individual_assumptions:
            array_to_mean = dictionary.get(individual_assumption)
            array_to_mean = array_to_mean.astype(float)
            array_to_mean[array_to_mean == 0.0] = np.nan
            if np.isnan(array_to_mean).all():
            	mean_value = 1
            else:
            	mean_value = np.nanmean(array_to_mean)
            temp_dictionary = {'mean': mean_value}
            dictionary_of_means[individual_assumption] = temp_dictionary

        for correlated_assumption in correlated_assumptions:
            temp_list_arrays = []
            assumptions_to_correlate = variance_correlations.get(correlated_assumption)
            for assumption in assumptions_to_correlate:
                temp_list_arrays.append(dictionary.get(assumption))

            array_to_mean = np.array(temp_list_arrays)
            array_to_mean = array_to_mean.astype(float)
            array_to_mean[array_to_mean == 0.0] = np.nan
            mean_value = np.nanmean(array_to_mean)
            temp_dictionary = {'mean': mean_value}
            dictionary_of_means[correlated_assumption] = temp_dictionary

        return dictionary_of_means

    def merge_input_dictionaries(self, dictionary_of_means):
        input_values = dict()

        for key in self.standard_deviation_assumptions:
            mean_dict = dictionary_of_means[key]
            sd_dict = self.standard_deviation_assumptions[key]
            sd_dict.update(mean_dict)
            input_values[key] = sd_dict.copy()

        return input_values

    def calc_gamma_inputs(self, mean, sd):
        shape = mean**2 / sd
        scale = sd / mean
        return shape, scale


    def generate_dictionary_of_sensitivities(self, dictionary_of_means):

        input_values = self.merge_input_dictionaries(dictionary_of_means)

        dict_of_sensitivities = dict()

        for assumption_key in input_values:
            assumption = input_values.get(assumption_key)
            sd = assumption['SD']
            mean = assumption['mean']

            if assumption['SD_type'] == "Absolute":
                pass
            else:
                sd = sd * mean

            sensitivity = sd / mean

            dict_of_sensitivities[assumption_key] = sensitivity



        return dict_of_sensitivities

    def generate_dictionary_of_variance(self, dictionary_of_means):

        input_values = self.merge_input_dictionaries(dictionary_of_means)

        dict_of_variance = dict()

        for assumption_key in input_values:
            assumption = input_values.get(assumption_key)
            sd = assumption['SD']
            mean = assumption['mean']
            dist = assumption['dist']

            if assumption['SD_type'] == "Absolute":
                pass
            else:
                sd = sd * mean

            sensitivity = sd / mean

            if dist == "Normal":
                sample = np.random.normal(1, sensitivity)
                dict_of_variance[assumption_key] = sample / 1

            elif dist == "Gamma":
                shape, scale = self.calc_gamma_inputs(1, sensitivity)
                sample = np.random.gamma(shape, scale)
                dict_of_variance[assumption_key] = sample / 1

            else:
                print("error: unrecognised distribution type for " + assumption_key)

            if dict_of_variance[assumption_key] < 0:
                dict_of_variance[assumption_key] = 0
            #elif (assumption_key not in self.list_assumptions_not_rates) & (dict_of_variance[assumption_key] > 1):
            #    dict_of_variance[assumption_key] = 1
           # else:
            #    pass
        return dict_of_variance

    def generate_dictionary_of_variance_sd_sensitivities(self, input_values, assumption_name, variance_dict, sd_variance):

        dict_of_variance = variance_dict.copy()

        assumption = input_values.get(assumption_name)
        sd = assumption['SD']
        mean = assumption['mean']

        if assumption['SD_type'] == "Absolute":
            pass
        else:
            sd = sd * mean

        sd_varied = sd_variance * sd
        mean_sd_varied = mean + sd_varied

        variance_for_assumption = mean_sd_varied / mean

        if variance_for_assumption < 0:
            variance_for_assumption = 0.0

        dict_of_variance[assumption_name] = variance_for_assumption



        return dict_of_variance

    def update_dictionary_with_variance(self, dictionary, dict_of_variance):
        variance_correlations = dictionary['variance_correlations']
        correlated_assumptions = [*variance_correlations]
        individual_assumptions = [x for x in self.assumptions_to_vary if x not in correlated_assumptions]

        dictionary_updated = dictionary.copy()

        for individual_assumption in individual_assumptions:
            array_input = dictionary.get(individual_assumption)
            variance_input = dict_of_variance.get(individual_assumption)
            dictionary_updated[individual_assumption] = array_input * variance_input

        for correlated_assumption in correlated_assumptions:
            assumptions_to_correlate = variance_correlations.get(correlated_assumption)
            variance_input = dict_of_variance.get(correlated_assumption)

            for assumption in assumptions_to_correlate:
                array_input = dictionary.get(assumption)
                dictionary_updated[assumption] = array_input * variance_input

        return dictionary_updated
