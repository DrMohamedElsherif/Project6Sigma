import warnings
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

from charts.basechart import BaseChart
from charts.constants import FIGURE_SIZE_DEFAULT

class Msa2n3gagerrchart(BaseChart):
    def process(self):
        # Read Excel file
        try:
            # Extracting data directly from the API response
            title = self.chart.config.title
            values = self.chart.data["values"]  # Values (measurements)
            parts = self.chart.data["parts"]  # Part IDs

            # Check if the chart has operators else use devices else throw an error
            if "operators" in self.chart.data:
                operators = self.chart.data["operators"]
            elif "devices" in self.chart.data:
                operators = self.chart.data["devices"]
            else:
                raise ValueError("The chart data must have either 'operators' or 'devices'")

            label = self.chart.config.labelx  # Label (Operator or Device)
            print(f"Title: {label}")
        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return None

        # Create a DataFrame
        data = pd.DataFrame({
            "Part": parts,
            "Operator": operators,
            "Value": values
        })

        # Sort and reset index
        data = data.sort_values(["Part", "Operator"])
        data.reset_index(inplace=True, drop=True)

        # Assign "Measurement" column
        num_measurements = data["Part"].value_counts().iloc[0]
        data["Measurement"] = list(np.arange(1, num_measurements + 1)) * (len(data) // num_measurements)

        # Plot Gage Run Chart
        try:
            g = sns.relplot(
                data=data,
                x="Measurement",
                y="Value",
                hue="Operator",
                style="Operator",
                col="Part",
                col_wrap=5,
                aspect=0.7
            )
            g.fig.suptitle(title, fontsize=16)
            g.map(plt.axhline, y=data["Value"].mean(), color=".7", dashes=(2, 1), zorder=0)
            g.set_axis_labels("Measurement", "Value")

            g.legend.set_title(f"{label}")
            legend = g._legend
            plt.setp(legend.get_texts(), fontsize=12)  # Set the font size for legend texts
            plt.setp(legend.get_title(), fontsize=14)  # Set the font size for the legend title

            # Attach the seaborn figure to the matplotlib figure
            plt.tight_layout()

        except Exception as e:
            print(f"Error generating the Gage Run Chart: {e}")
            return None

        return g
