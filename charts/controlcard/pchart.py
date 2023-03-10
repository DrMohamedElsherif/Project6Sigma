# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from charts.basechart import BaseChart

class pchart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data1 = self.chart.data[0]
        data2 = []
        group_size = self.chart.group_size if bool(self.chart.group_size) else False
        data_length = len(data1)

        # Check if `group_size` is provided
        if group_size is not False:
            for x in range(data_length):
                data2.append(group_size)

        else:
            data2 = self.chart.data[1]

        p = {
            'defects': list(np.array(data1)),
            'group_size': list(np.array(data2))
        }

        # Convert data to data frame
        p = pd.DataFrame(p)

        # Add 'p' column to data frame
        p['p'] = p['defects']/p['group_size']

        # Plot c-chart
        self.figure = plt.figure(figsize=(15, 11))

        plt.plot(p['p'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        PC = statistics.mean(p['p'])
        OEG = statistics.mean(p['p'])+3*(np.sqrt((statistics.mean(p['p'])*(1-statistics.mean(p['p'])))/(p['group_size'])))
        UEG = statistics.mean(p['p'])-3*(np.sqrt((statistics.mean(p['p'])*(1-statistics.mean(p['p'])))/(p['group_size'])))

        plt.step(x=range(0, len(p['p'])), y=OEG, color='red', linestyle='dashed', label='OEG=' + str(round(OEG[0], 2)))
        plt.axhline(PC, color='green', label='p=' + str(round(PC, 1)))
        plt.step(x=range(0, len(p['p'])), y=UEG, color='red', linestyle='dashed', label='UEG=' + str(round(UEG[0], 2)))
        plt.title(title, fontsize=28, pad=20)
        plt.xlabel('Sample')
        plt.ylabel('Proportion')
        plt.legend(loc='upper right', framealpha=1)

        # Validate points out of control limits
        i = 0
        control = True
        for group in p['p']:
            if group > (statistics.mean(p['p'])+3*(np.sqrt((statistics.mean(p['p'])*(1-statistics.mean(p['p'])))/statistics.mean(p['group_size'])))) or group < (statistics.mean(p['p'])-3*(np.sqrt((statistics.mean(p['p'])*(1-statistics.mean(p['p'])))/statistics.mean(p['group_size'])))):
                print('Group', i, 'out of fraction defective cotrol limits!')
                control = False
            i += 1
        if control == True:
            print('All points within control limits.')

        return self.figure