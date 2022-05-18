# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from .basechart import BaseChart

class Cchart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data = self.chart.data[0]
        group_size = []
        data_length = len(data)

        for x in range(data_length):
            group_size.append(data_length)

        c = {
            'defects': list(np.array(data)),
            'group_size': list(np.array(group_size))
        }

        # Convert data to data frame
        c = pd.DataFrame(c)

        # Plot c-chart
        self.figure = plt.figure(figsize=(15,7.5))

        plt.plot(c['defects'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        C = statistics.mean(c['defects'])
        OEG = statistics.mean(c['defects'])+3*np.sqrt(statistics.mean(c['defects']))
        UEG = statistics.mean(c['defects'])-3*np.sqrt(statistics.mean(c['defects']))

        plt.axhline(OEG, color='red', linestyle='dashed', label='OEG=' + str(round(OEG, 2)))
        plt.axhline(C, color='green', label='C=' + str(round(C, 1)))
        plt.axhline(UEG, color='red', linestyle='dashed', label='UEG=' + str(round(UEG, 2)))
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Defect Count')
        plt.legend(loc='upper right', framealpha=1)

        # Validate points out of control limits
        i = 0
        control = True
        for group in c['defects']:
            if group > statistics.mean(c['defects'])+3*np.sqrt(statistics.mean(c['defects'])) or group < statistics.mean(c['defects'])-3*np.sqrt(statistics.mean(c['defects'])):
                self.message = 'Group', i, 'out of defects cotrol limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        return self.figure