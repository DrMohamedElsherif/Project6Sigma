# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT


class Uchart(BaseChart):
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

        u = {
            'defects': list(np.array(data1)),
            'group_size': list(np.array(data2))
        }

        # Convert data to data frame
        u = pd.DataFrame(u)

        # Add 'u' column to data frame
        u['u'] = u['defects']/u['group_size']

        # Plot u-chart
        self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)

        plt.plot(u['u'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        U = statistics.mean(u['u'])
        OEG = u['u'].mean()+3*np.sqrt(u['u'].mean() / u['group_size'])
        UEG = u['u'].mean()-3*np.sqrt(u['u'].mean() / u['group_size'])

        plt.step(x=range(0, len(u['u'])), y=OEG, color='red',
                 linestyle='dashed', label='OEG=' + str(round(OEG[0], 2)))
        plt.axhline(U, color='green', label='U=' + str(round(U, 1)))
        plt.step(x=range(0, len(u['u'])), y=UEG, color='red',
                 linestyle='dashed', label='UEG=' + str(round(UEG[0], 2)))
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Sample Count Per Unit')
        plt.legend(loc='upper right', framealpha=1)

        # Validate points out of control limits
        i = 0
        control = True
        for group in u['u']:
            if group > u['u'].mean()+3*np.sqrt(u['u'].mean()/u['group_size'][i]) or group < u['u'].mean()-3*np.sqrt(u['u'].mean()/u['group_size'][i]):
                self.message = 'Group', i, 'out of fraction defective cotrol limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        return self.figure
