# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT


class Npchart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data1 = self.chart.data[0]
        data2 = []
        group_size = self.chart.group_size if bool(
            self.chart.group_size) else False
        data_length = len(data1)

        # Check if `group_size` is provided
        if group_size is not False:
            for x in range(data_length):
                data2.append(group_size)

        else:
            data2 = self.chart.data[1]

        data = {
            'defects': list(np.array(data1)),
            'group_size': list(np.array(data2))
        }

        # Convert data to data frame
        data = pd.DataFrame(data)

        # Add 'np' column to data frame
        data['np'] = data['defects']/data['group_size']

        # Plot np-chart
        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        plt.plot(data['np'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        NP = statistics.mean(data['np'])
        OEG = statistics.mean(data['np'])+3*(np.sqrt((statistics.mean(data['np'])*(
            1-statistics.mean(data['np'])))/statistics.mean(data['group_size'])))
        UEG = statistics.mean(data['np'])-3*(np.sqrt((statistics.mean(data['np'])*(
            1-statistics.mean(data['np'])))/statistics.mean(data['group_size'])))

        plt.axhline(OEG, color='red', linestyle='dashed',
                    label='OEG=' + str(round(OEG, 2)))
        plt.axhline(NP, color='green', label='np=' + str(round(NP, 1)))
        plt.axhline(UEG, color='red', linestyle='dashed',
                    label='UEG=' + str(round(UEG, 2)))
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Sample Count')
        plt.legend(loc='upper right', framealpha=1)

        # Validate points out of control limits
        i = 0
        control = True
        for group in data['np']:
            if group > (statistics.mean(data['np'])+3*(np.sqrt((statistics.mean(data['np'])*(1-statistics.mean(data['np'])))/statistics.mean(data['group_size'])))) or group < (statistics.mean(data['np'])-3*(np.sqrt((statistics.mean(data['np'])*(1-statistics.mean(data['np'])))/statistics.mean(data['group_size'])))):
                self.message = 'Group', i, 'out of fraction defective cotrol limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        return self.figure
