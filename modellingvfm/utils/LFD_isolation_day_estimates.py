import numpy as np

LFD_test_sensitivity = {1: 0.0, 2: 0.0, 3: 0.08, 4: 0.39, 5: 0.71, 6: 0.83, 7: 0.86, 8: 0.86, 9: 0.83, 10: 0.74, 11: 0.55, 12: 0.33, 13: 0.16, 14: 0.05}

class DayToIsolateLFD:

    def __init__(self):
        self.LFD_test_sensitivity = LFD_test_sensitivity

    def day_tests_positive_LFD_frequency(self, period):
        """

        :param period:
        :return:
        """
        days_of_possible_test = list(range(1, period + 1))

        output_dictionary = {}

        for n_tests_per_week in days_of_possible_test:

            average_day_detection_start_date = []

            for start_day in list(range(0, n_tests_per_week)):
                index_days_to_test = self.return_index_of_days_of_test(start_day, period + 1, n_tests_per_week)

                days_of_test = [0] * len(days_of_possible_test)

                for test_day in index_days_to_test:
                    days_of_test[test_day] = 1

                probability_not_detected_on_a_day = np.array(days_of_test) * np.array(
                    list(self.LFD_test_sensitivity.values()))
                probability_not_detected_on_a_day = [1 - x for x in probability_not_detected_on_a_day]

                probability_detect_on_day = []
                for i in days_of_possible_test:
                    probability_detect_on_day_value = 1 - np.prod(probability_not_detected_on_a_day[:i]) - (
                            1 - np.prod(probability_not_detected_on_a_day[:i - 1]))
                    probability_detect_on_day.append(probability_detect_on_day_value)

                if np.sum(probability_detect_on_day) == 0:
                    average_day_of_detection = period
                else:
                    average_day_of_detection = np.sum(np.array(probability_detect_on_day) * np.array(
                        list(self.LFD_test_sensitivity.keys()))) / np.sum(probability_detect_on_day)

                average_day_detection_start_date.append(average_day_of_detection)

            output_dictionary[n_tests_per_week] = np.mean(average_day_detection_start_date)

        return output_dictionary

    def multiples(self, start_day, end_day, delta):
        """
        This function generates a list of dates between a start and end date whereby the delta determines the intervals between each date.
        :param start_day: a datetime date
        :param end_day: a datetime date
        :param delta: an integer
        :return:
        """
        curr = start_day
        while curr < end_day:
            yield curr
            curr += delta

    def return_index_of_days_of_test(self, start_day, end_day, delta):
        """
        This function uses 'multiples' to create a list of integers indexing of the days of testing.
        :param start_day: a datetime date
        :param end_day: a datetime date
        :param delta: an integer
        :return: days_when_testing list
        """
        days_when_testing = []
        for days_test in self.multiples(start_day, end_day, delta):
            index_of_day_test = days_test - 1
            days_when_testing.append(index_of_day_test)

        return days_when_testing
