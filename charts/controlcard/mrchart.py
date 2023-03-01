# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statistics
from charts.basechart import BaseChart


class Mrchart(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        data = np.array(self.chart.data[0])

        # Create pandas series objects
        x = pd.Series(data)
        # MR = pd.Series(col2)
        MR = [np.nan]

        # Get and append moving ranges
        i = 1
        for data in range(1, len(x)):
            MR.append(abs(x[i] - x[i-1]))
            i += 1

        # Convert list to pandas Series objects
        MR = pd.Series(MR)

        # Concatenate mR Series with and rename columns
        data = pd.concat([x, MR], axis=1).rename(columns={0: "x", 1: "mR"})

        # Plot x and mR charts
        self.figure, axs = plt.subplots(2, figsize=(15, 11), sharex=True)

        # x chart
        axs[0].plot(data['x'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        X = statistics.mean(data['x'])
        UCL = statistics.mean(data['x'])+3*statistics.mean(data['mR'][1:len(data['mR'])])/1.128
        LCL = statistics.mean(data['x'])-3*statistics.mean(data['mR'][1:len(data['mR'])])/1.128

        axs[0].axhline(UCL, color='red', linestyle='dashed', label='UCL=' + str(round(UCL, 3)))
        axs[0].axhline(X, color='green', label='X=' + str(round(X, 1)))
        axs[0].axhline(LCL, color='red', linestyle='dashed', label='LCL=' + str(round(LCL, 3)))
        axs[0].set_title(title, fontsize=28, pad=20)
        axs[0].set(xlabel='Observation', ylabel='Individual Value')
        axs[0].legend(loc='upper right', framealpha=1)

        # mR chart
        axs[1].plot(data['mR'], linestyle='-', marker='o', color='blue')
        # Define variables for use in line and label
        MR = statistics.mean(data['mR'][1:len(data['mR'])])
        UCL2 = statistics.mean(data['mR'][1:len(data['mR'])])+3*statistics.mean(data['mR'][1:len(data['mR'])])*0.8525
        LCL2 = statistics.mean(data['mR'][1:len(data['mR'])])-3*statistics.mean(data['mR'][1:len(data['mR'])])*0.8525

        axs[1].axhline(MR, color='green', label='MR=' + str(round(MR, 3)))
        axs[1].axhline(UCL2, color='red', linestyle='dashed', label='UCL=' + str(round(UCL2, 3)))
        axs[1].axhline(LCL2, color='red', linestyle='dashed', label='LCL=' + str(round(LCL2, 3)))
        axs[1].set(xlabel='Observation', ylabel='Moving Range')
        axs[1].legend(loc='upper right', framealpha=1)

        # Validate points out of control limits for x chart
        i = 0
        control = True
        for unit in data['x']:
            if unit > statistics.mean(data['x'])+3*statistics.mean(data['mR'][1:len(data['mR'])])/1.128 or unit < statistics.mean(data['x'])-3*statistics.mean(data['mR'][1:len(data['mR'])])/1.128:
                self.message = 'Unit', i, 'out of cotrol limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        # Validate points out of control limits for mR chart
        i = 0
        control = True
        for unit in data['mR']:
            if unit > statistics.mean(data['mR'][1:len(data['mR'])])+3*statistics.mean(data['mR'][1:len(data['mR'])])*0.8525 or unit < statistics.mean(data['mR'][1:len(data['mR'])])-3*statistics.mean(data['mR'][1:len(data['mR'])])*0.8525:
                self.message = 'Unit', i, 'out of control limits!'
                control = False
            i += 1
        if control == True:
            self.message = 'All points within control limits.'

        return self.figure
