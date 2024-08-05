# File: data_analytics.py

import matplotlib.pyplot as plt

class DataAnalytics:
    def __init__(self, firestore_service):
        self.firestore_service = firestore_service

    def generate_program_distribution_chart(self):
        companies = self.firestore_service.get_all_companies()
        program_counts = {}
        for company in companies:
            program = company.get('ProgramName', 'Unknown')
            program_counts[program] = program_counts.get(program, 0) + 1

        plt.figure(figsize=(10, 6))
        plt.bar(program_counts.keys(), program_counts.values())
        plt.title('Distribution of Companies by Program')
        plt.xlabel('Program')
        plt.ylabel('Number of Companies')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('program_distribution.png')
        plt.close()

    def generate_quantity_summary(self):
        companies = self.firestore_service.get_all_companies()
        quantities = [company.get('quantity', 0) for company in companies if company.get('quantity') is not None]

        summary = {
            'Total Companies': len(companies),
            'Total Quantity': sum(quantities),
            'Average Quantity': sum(quantities) / len(quantities) if quantities else 0,
            'Max Quantity': max(quantities) if quantities else 0,
            'Min Quantity': min(quantities) if quantities else 0
        }

        return summary