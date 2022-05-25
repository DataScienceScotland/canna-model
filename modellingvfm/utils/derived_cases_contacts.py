import numpy as np
from .support_functions import SupportFunctions

class DerivedCasesContacts:

    def __init__(self, ):
        self.case_contact_volumes_generated = ['cases_no_test_symp', 'contacts_app_reached','contacts_schools', "counterfactual_cases", "counterfactual_contacts", "counterfactual_symp_only_pop"]
        self.support_functions = SupportFunctions()

    def add_derived_column(self, derived_group, group_list, dictionary):

        new_dictionary = dictionary.copy()
        new_column = None

        if derived_group == "cases_no_test_symp":
            new_column = self.calc_cases_no_test_symp(group_list, dictionary)
        elif derived_group == "contacts_app_reached":
            new_column = dictionary.get("app_exposure_notifications_sent")
        elif derived_group == "contacts_schools":
            new_column = dictionary.get("contacts_schools")
        elif derived_group == "counterfactual_cases":
            new_column = self.calc_counterfactual_cases(dictionary)
        elif derived_group == "counterfactual_contacts":
            new_column = self.calc_counterfactual_contacts(dictionary)
        elif derived_group == "counterfactual_symp_only_pop":
            new_column = self.calc_counterfactual_symp_only_pop(dictionary)
        else:
            print("not included calculation for derived case/contact column")

        actuals_data_array = new_dictionary['actuals_data_PPV']
        actuals_data_array = np.append(actuals_data_array, new_column, axis=1)
        new_dictionary['actuals_data_PPV'] = actuals_data_array

        return new_dictionary

    def apply_PPV_to_actuals_data(self, dictionary, PCR_PPV, LFD_PPV):
        actuals_data_dictionary = dictionary['actuals_data_dictionary']
        actuals_data_dictionary_PPV = dict()

        actuals_data_dictionary_PPV['cases_PCR_test_symp'] = actuals_data_dictionary['cases_PCR_test_symp'] * PCR_PPV
        actuals_data_dictionary_PPV['cases_PCR_test_asymp'] = actuals_data_dictionary['cases_PCR_test_asymp'] * PCR_PPV
        actuals_data_dictionary_PPV['cases_LFD_test_asymp_assisted'] = actuals_data_dictionary['cases_LFD_test_asymp_assisted'] * LFD_PPV
        actuals_data_dictionary_PPV['cases_LFD_test_asymp_selftest'] = actuals_data_dictionary['cases_LFD_test_asymp_selftest'] * LFD_PPV

        ConfPCR_PPV = 1 - ((1-LFD_PPV) * (1-PCR_PPV))

        actuals_data_dictionary_PPV['cases_ConfPCR_test_symp'] = actuals_data_dictionary['cases_ConfPCR_test_symp'] * ConfPCR_PPV
        actuals_data_dictionary_PPV['cases_ConfPCR_test'] = actuals_data_dictionary['cases_ConfPCR_test'] * ConfPCR_PPV

        PPV_adjustment_for_contacts = self.calc_PPV_adjustment_for_contacts(actuals_data_dictionary, actuals_data_dictionary_PPV)
        actuals_data_dictionary_PPV['contacts_household_reached'] = actuals_data_dictionary['contacts_household_reached'] * PPV_adjustment_for_contacts
        actuals_data_dictionary_PPV['contacts_nonhousehold_reached'] = actuals_data_dictionary['contacts_nonhousehold_reached'] * PPV_adjustment_for_contacts

        adjusted_app_exposure_notifications_sent = dictionary['app_exposure_notifications_sent'] * PPV_adjustment_for_contacts
        contacts_schools = dictionary['contacts_schools'].astype('float') * PPV_adjustment_for_contacts

        return actuals_data_dictionary_PPV, adjusted_app_exposure_notifications_sent, contacts_schools

    def calc_PPV_adjustment_for_contacts(self, dictionary, dictionary_PPV):

        sum_cases_PPV = dictionary_PPV['cases_PCR_test_symp'] + dictionary_PPV['cases_PCR_test_asymp'] + dictionary_PPV['cases_LFD_test_asymp_assisted'] + dictionary_PPV['cases_ConfPCR_test']
        sum_cases = dictionary['cases_PCR_test_symp'] + dictionary['cases_PCR_test_asymp'] + dictionary['cases_LFD_test_asymp_assisted'] + dictionary_PPV['cases_ConfPCR_test']

        PPV_adjustment_for_contacts = sum_cases_PPV / sum_cases

        return PPV_adjustment_for_contacts

    def generate_base_PPV_array(self, dictionary, group_list, actuals_data_PPV_inputs):

        length_of_matrix = dictionary['actuals_data'].shape[0]
        actuals_data_PPV = np.empty([length_of_matrix,0], dtype = float)

        for group in group_list:
            if group in actuals_data_PPV_inputs:
                actuals_data_PPV = np.append(actuals_data_PPV, actuals_data_PPV_inputs.get(group), axis = 1)
            else:
                pass

        return actuals_data_PPV

    def calc_incidence(self, dictionary):
        proportion_population_testing_positive = dictionary['proportion_population_testing_positive']
        incidence_per_10000 = dictionary['incidence_per_10000']
        population_size = dictionary['population_size']

        population_multiplier = population_size / 10000

        updated_population_testing_positive = incidence_per_10000 * population_multiplier

        return updated_population_testing_positive

    def adjust_attack_rates(self, dictionary):

        attack_rate_household = dictionary['attack_rate_household']
        attack_rate_non_household = dictionary['attack_rate_non_household']
        attack_rate_nhh_2_16 = dictionary['attack_rate_nhh_2_16']

        prop_household_contacts_prev_cases = dictionary['actuals_data_dictionary']['prop_household_contacts_prev_cases']
        prop_nonhousehold_contacts_prev_cases = dictionary['actuals_data_dictionary']['prop_nonhousehold_contacts_prev_cases']

        attack_rate_household_adjusted = (attack_rate_household - prop_household_contacts_prev_cases) / (1 - prop_household_contacts_prev_cases)
        #attack_rate_household_adjusted = attack_rate_household 
        attack_rate_non_household_adjusted = (attack_rate_non_household - prop_nonhousehold_contacts_prev_cases) / (1 - prop_nonhousehold_contacts_prev_cases)
        #attack_rate_non_household_adjusted = attack_rate_non_household
        attack_rate_nhh_2_16_adjusted = attack_rate_nhh_2_16 * (attack_rate_non_household_adjusted / attack_rate_non_household)
        #attack_rate_nhh_2_16_adjusted = attack_rate_nhh_2_16
        
        #attack_rate_household_adjusted[attack_rate_household_adjusted<0] = 0
        #attack_rate_non_household_adjusted[attack_rate_non_household_adjusted<0]=0

        return attack_rate_household_adjusted, attack_rate_non_household_adjusted, attack_rate_nhh_2_16_adjusted


    def update_actuals_data(self, dictionary, group_list):

        PPV_PCR = self.support_functions.generate_PPV_for_tests(dictionary)
        PPV_LFD = dictionary.get('PPV_LFD') # replace PPV calc for LFD with external assumption

        attack_rate_household_adjusted, attack_rate_non_household_adjusted, attack_rate_nhh_2_16_adjusted = self.adjust_attack_rates(dictionary)

        actuals_data_PPV_dictionary, adjusted_app_exposure_notifications_sent, contacts_schools = self.apply_PPV_to_actuals_data(dictionary, PPV_PCR, PPV_LFD)

        actuals_data_PPV_array = self.generate_base_PPV_array(dictionary, group_list, actuals_data_PPV_dictionary)

        new_dictionary = dictionary.copy()
        new_dictionary['attack_rate_household'] = attack_rate_household_adjusted
        new_dictionary['attack_rate_non_household'] = attack_rate_non_household_adjusted
        new_dictionary['attack_rate_nhh_2_16'] = attack_rate_nhh_2_16_adjusted
        #new_dictionary['population_testing_positive'] = self.calc_incidence(new_dictionary)
        new_dictionary['app_exposure_notifications_sent'] = adjusted_app_exposure_notifications_sent
        new_dictionary['contacts_schools'] = contacts_schools
        new_dictionary['actuals_data_PPV'] = actuals_data_PPV_array
        new_dictionary['actuals_data_PPV_dictionary'] = actuals_data_PPV_dictionary
        new_dictionary['household_contacts_per_case_counterfactual'] = self.calc_contacts_per_case(new_dictionary)

        for derived_group in self.case_contact_volumes_generated:

            if derived_group not in group_list:
                pass
            else:
                new_dictionary = self.add_derived_column(derived_group, group_list, new_dictionary)

        return new_dictionary

    def calc_total_attacked_contacts_reached(self, list_groups, dictionary):

        attack_rate_non_household = dictionary['attack_rate_non_household']
        attack_rate_household = dictionary['attack_rate_household']
        attack_rate_nhh_2_16 = dictionary['attack_rate_nhh_2_16']
        actuals_data = dictionary['actuals_data_PPV_dictionary']
        contacts_household_reached = actuals_data['contacts_household_reached']
        contacts_nonhousehold_reached = actuals_data['contacts_nonhousehold_reached']
        app_exposure_notifications_sent = dictionary['app_exposure_notifications_sent']
        contacts_schools = dictionary['contacts_schools']


        total_contacts_reached = (contacts_household_reached * attack_rate_household) + (contacts_nonhousehold_reached * attack_rate_non_household)

        if "contacts_app_reached" in list_groups:
            total_contacts_reached = total_contacts_reached + (app_exposure_notifications_sent * attack_rate_non_household)

        if "contacts_schools" in list_groups:
            total_contacts_reached = total_contacts_reached + (contacts_schools * attack_rate_nhh_2_16)

        return total_contacts_reached

    def calc_symp_cases_testing(self, dictionary):
        proportion_cases_symptomatic = dictionary['proportion_cases_symptomatic']
        actuals_data = dictionary['actuals_data_PPV_dictionary']
        total_PCR_symp_cases_tested = actuals_data['cases_PCR_test_symp']
        total_LFD_cases_tested = actuals_data['cases_LFD_test_asymp_assisted'] + actuals_data['cases_LFD_test_asymp_selftest']
        total_LFD_symp_cases_tested = (total_LFD_cases_tested * proportion_cases_symptomatic) + actuals_data['cases_ConfPCR_test_symp']

        return total_PCR_symp_cases_tested, total_LFD_symp_cases_tested

    def calc_cases_no_test_symp(self, list_groups, dictionary):
        population_testing_positive = dictionary['population_testing_positive']
        proportion_cases_symptomatic = dictionary['proportion_cases_symptomatic']
        total_contacts_reached = self.calc_total_attacked_contacts_reached(list_groups, dictionary)
        symptomatic_contacts_reached = total_contacts_reached * proportion_cases_symptomatic
        total_PCR_symp_cases_tested, total_LFD_symp_cases_tested = self.calc_symp_cases_testing(dictionary)
        symptomatic_cases_tested = total_PCR_symp_cases_tested + total_LFD_symp_cases_tested
        symp_population_testing_positive = population_testing_positive * proportion_cases_symptomatic
        cases_no_test_symp = symp_population_testing_positive - symptomatic_cases_tested - symptomatic_contacts_reached

        # TODO: values are sometimes negative, set to zero?
        cases_no_test_symp[cases_no_test_symp < 0] = 0

        return cases_no_test_symp

    def calc_contacts_per_case(self, dictionary):
        dictionary_actuals = dictionary['actuals_data_PPV_dictionary']

        total_cases = dictionary_actuals.get('cases_PCR_test_symp') + \
                      dictionary_actuals.get('cases_PCR_test_asymp') + \
                      dictionary_actuals.get('cases_LFD_test_asymp_assisted') + \
                      dictionary_actuals.get('cases_ConfPCR_test')

        # excl. self serve LFDs t included in CTAS
        contacts_per_case = dictionary_actuals.get('contacts_household_reached') / total_cases

        return contacts_per_case


    def calc_counterfactual_cases(self, dictionary):
        total_PCR_symp_cases_tested, total_LFD_symp_cases_tested = self.calc_symp_cases_testing(dictionary)

        return total_PCR_symp_cases_tested

    def calc_counterfactual_contacts(self, dictionary):
        household_contacts_per_case_counterfactual = dictionary.get('household_contacts_per_case_counterfactual')
        counterfactual_cases = self.calc_counterfactual_cases(dictionary)
        counterfactual_contacts = counterfactual_cases * household_contacts_per_case_counterfactual

        return counterfactual_contacts

    def calc_counterfactual_symp_only_pop(self, dictionary):
        population_testing_positive = dictionary['population_testing_positive']
        proportion_cases_symptomatic = dictionary['proportion_cases_symptomatic']
        attack_rate_household = dictionary['attack_rate_household']
        counterfactual_cases = self.calc_counterfactual_cases(dictionary)
        counterfactual_contacts = self.calc_counterfactual_contacts(dictionary)

        symp_population_testing_positive = population_testing_positive * proportion_cases_symptomatic

        counterfactual_contacts_symptomatic = counterfactual_contacts * proportion_cases_symptomatic * attack_rate_household

        counterfactual_symp_only_pop = symp_population_testing_positive - counterfactual_cases - counterfactual_contacts_symptomatic

        # TODO: values are sometimes negative, set to zero?
        counterfactual_symp_only_pop[counterfactual_symp_only_pop < 0] = 0

        return counterfactual_symp_only_pop




