import pandas as pd
from scipy.stats import normaltest, shapiro

from charts.basechart import BaseChart
from charts.capability.continuous.normal import I_MR_chart


class Capabilitystudy(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        values = self.chart.data["values"]
        lsl = self.chart.config.lower_bound
        usl = self.chart.config.upper_bound

        data = pd.DataFrame({
            "value": values
        })

        # Continuous data
        if data.dtypes.iloc[0] == "float64":

            # Normality tests
            _, p_value_shapiro = shapiro(data.iloc[:, 0])
            _, p_value_normaltest = normaltest(data.iloc[:, 0])

            # If data is normally distributed
            if p_value_shapiro > 0.05 and p_value_normaltest > 0.05:
                print("Data is normally distributed")
                return I_MR_chart(data, title, target=100, subgroup_size=1, USL=usl, LSL=lsl)
            # If data is not normally distributed
            else:
                print("Data is not normally distributed")
                # I_MR_transformed_chart(data, target=100, subgroup_size=1, LSL=5, USL=10)

        # Discrete data:
        else:
            print("Discrete data")
            # U_chart(data, acceptable_DPU=3, subgroup_size=20)
            # P_chart(data, target=10, subgroup_size=20)