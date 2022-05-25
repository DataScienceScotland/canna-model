from .model.generate_central_assumptions import CentralAssumptions
from .model.transmission_reduction import TransmissionReduction
from .model.output_excel import OutputExcel
from modellingvfm.model.monte_carlo_simulation import MonteCarlo
from modellingvfm.model.sensitivity_output import SensitivityAnalysis

if __name__ == '__main__':
    groups = [# Impact of T&T
              "contacts_household_reached",
              "contacts_nonhousehold_reached",
              "contacts_app_reached",
              'contacts_schools',
              "cases_PCR_test_symp",
              "cases_PCR_test_asymp",
              "cases_ConfPCR_test",
              "cases_LFD_test_asymp_assisted",
              "cases_LFD_test_asymp_selftest",

              # further effective isolation
              "cases_no_test_symp",

              # counterfactual
              "counterfactual_cases",
              "counterfactual_contacts",
              "counterfactual_symp_only_pop"
              ]

    #### preps central assumptions, runs calculation and outputs an excel

    dict_example, fortnightly_periods = CentralAssumptions(groups).dictionary_central_assumptions()
    df = TransmissionReduction(dict_example, groups, fortnightly_periods).create_dictionary_storing_outputs()
    df_excel = OutputExcel(dict_example, groups, fortnightly_periods).output_df()

    #### preps data and runs simulation n times using random variance each time

    output_dict, dict_of_assumption_outputs, n_of_sims = MonteCarlo(groups).monte_carlo_simulation(1000)
    output_dict_summarised = MonteCarlo(groups).average_output_from_monte_carlo(output_dict, n_of_sims)
    dict_of_assumption_outputs_summarised = MonteCarlo(groups).average_output_from_monte_carlo_assumptions(dict_of_assumption_outputs)

    MonteCarlo(groups).output_multiple_charts(dict_of_assumption_outputs, "assumptions")
    MonteCarlo(groups).output_multiple_charts(output_dict, "outputs")
    MonteCarlo(groups).high_level_outputs(output_dict)
    MonteCarlo(groups).export_output_dict_assumptions_to_excel(dict_of_assumption_outputs_summarised)
    MonteCarlo(groups).export_output_dict_to_excel(output_dict_summarised)

    #### generates table of sensitivities
    SensitivityAnalysis(groups).output_excel_sensitivites(['r_red_from_NHSTT', 'r_red_from_TTI', 'pta_NHSTT_total'])








