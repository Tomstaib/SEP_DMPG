class TallyStatistic:
    def __init__(self):
        self.num_times_processed_list = []

    def record(self, num_times_processed):
        self.num_times_processed_list.append(num_times_processed)

    def calculate_statistics(self):
        if not self.num_times_processed_list:
            return None, None, None
        else:
            min_value = min(self.num_times_processed_list)
            max_value = max(self.num_times_processed_list)
            avg_value = sum(self.num_times_processed_list) / len(self.num_times_processed_list)
            return min_value, max_value, avg_value
