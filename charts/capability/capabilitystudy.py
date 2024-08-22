import pandas as pd
from scipy.stats import normaltest, shapiro

from charts.basechart import BaseChart
from charts.capability.continuous.normal import I_MR_chart
from charts.capability.continuous.notnormal import I_MR_chart_transformed
from charts.capability.discrete.pchart import P_chart
from charts.capability.discrete.uchart import U_chart


class Capabilitystudy(BaseChart):
    def process(self):
        # Define data and parameters
        title = self.chart.config.title
        target = self.chart.config.target
        acceptable_percent = self.chart.config.acceptable_percent
        acceptable_DPU = self.chart.config.acceptable_DPU
        subgroup_size = self.chart.config.subgroup_size
        values = self.chart.data["values"]
        lsl = self.chart.config.lower_bound
        usl = self.chart.config.upper_bound
        type = self.chart.config.type

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
                return I_MR_chart(data, title, target=target, subgroup_size=subgroup_size, USL=usl, LSL=lsl)
            # If data is not normally distributed
            else:
                return I_MR_chart_transformed(data, title, target=target, subgroup_size=subgroup_size, LSL=lsl, USL=usl)

        # Discrete data:
        else:
            if type == "pchart":
                return P_chart(data, title, acceptable_percent=acceptable_percent, subgroup_size=subgroup_size)
            elif type == "uchart":
                return U_chart(data, title, acceptable_DPU=acceptable_DPU, subgroup_size=subgroup_size)
            else:
                return print("Error. The type of chart is not supported.")


