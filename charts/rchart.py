# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from .basechart import BaseChart

class Rchart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data1 = self.chart.data[0]
        group_size = self.chart.group_size if bool(self.chart.group_size) else False

        # Check if `group_size` is provided
        if group_size is not False:
            # use group_size to split data into pieces with a possible leftover when its not divisible
            splits = np.split(data1, np.arange(group_size, len(data1), group_size))
            x_temp = []

            for item in splits:
                x_temp.append(item)
            x = np.array(x_temp, dtype=object)

        else:
            x = np.asarray(data1, dtype=object)

        # Define list variable for groups means
        x_bar = []

        # Define list variable for groups ranges
        r = []

        # Get and append groups means and ranges
        for group in x:
            if len(group) > 1:
                x_bar.append(group.mean(dtype=np.float64))
                r.append(group.max() - group.min())
            else:
                x_bar.append(float(group[0]))

        # Plot x-bar and R charts
        self.figure, axs = plt.subplots(2, figsize=(15, 7.5))

        # x-bar chart
        axs[0].plot(x_bar, linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        X = (statistics.mean(x_bar))
        OEG = (statistics.mean(x_bar)+0.577*statistics.mean(r))
        UEG = (statistics.mean(x_bar)-0.577*statistics.mean(r))

        axs[0].axhline(OEG, color='red', linestyle='dashed', label='OEG=' + str(round(OEG, 3)))
        axs[0].axhline(X, color='green', label='X=' + str(round(X, 1)))
        axs[0].axhline(UEG, color='red', linestyle='dashed', label='UEG=' + str(round(UEG, 3)))
        axs[0].set_title(title, fontsize=28, pad=20)
        axs[0].set(xlabel='Sample', ylabel='Sample Mean')
        axs[0].legend(loc='upper right', framealpha=1)

        # R chart
        axs[1].plot(r, linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        R = (statistics.mean(r))
        OEG2 = (2.574*statistics.mean(r))
        UEG2 = (0*statistics.mean(r))

        axs[1].axhline(OEG2, color='red', linestyle='dashed', label='OEG=' + str(round(OEG2, 3)))
        axs[1].axhline(R, color='green', label='R=' + str(round(R, 1)))
        axs[1].axhline(UEG2, color='red', linestyle='dashed', label='UEG=' + str(round(UEG2, 3)))
        axs[1].set(xlabel='Sample', ylabel='Sample Range')
        axs[1].legend(loc='upper right', framealpha=1)

        # Validate points out of control limits for x-bar chart
        i = 0
        control = True
        for group in x_bar:
            if group > statistics.mean(x_bar)+0.577*statistics.mean(r) or group < statistics.mean(x_bar)-0.577*statistics.mean(r):
                self.message = 'Group', i, 'out of mean control limits!'
                control = False
            i += 1
        if control == True:
            print('All points within control limits.')

        # Validate points out of control limits for R chart
        i = 0
        control = True
        for group in r:
            if group > 2.574*statistics.mean(r):
                self.message = 'Group', i, 'out of range cotrol limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        return self.figure
