import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_DEFAULT, TITLE_FONT_SIZE, TITLE_PADDING


class Interval5Config(BaseModel):
    title: str


class Interval5Data(BaseModel):
    values: Dict[str, List[float]] = Field(..., min_length=1)
    additional_values: Optional[Dict[str, List[str]]] = None


class Interval5Request(BaseModel):
    project: str
    step: str
    config: Interval5Config
    data: Interval5Data


class Interval5:
    def __init__(self, data: dict):
        try:
            validated_data = Interval5Request(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data
            self.figure = None
        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )

    def process(self):
        title = self.config.title
        df = pd.DataFrame(self.data.values)

        # Set additional data if it exists
        ad = pd.DataFrame(self.data.additional_values) if self.data.additional_values else None

        if ad is not None and not ad.empty:
            # Create a new dataframe with the data and grouping
            df_grouped = pd.DataFrame(
                {'Values': df.values.flatten(),
                 'Group': np.repeat(ad.iloc[:, 0], len(df.columns))}
            )

            # Group the data by categorical variable
            grouped_data = df_grouped.groupby('Group')

            # Determine subplot layout
            n_cols = 2
            n_subplots = len(df.columns)
            n_rows = math.ceil(n_subplots / n_cols)

            # Create subplots
            self.figure, axes = plt.subplots(n_rows, n_cols, figsize=(15, n_rows * 5))
            axes = axes.reshape(-1)

            # Generate plots for each column
            for i, column in enumerate(df.columns):
                ax = axes[i]

                # Plot for each group
                for j, (group, group_df) in enumerate(grouped_data):
                    values = group_df.loc[group_df['Group'] == group, 'Values']
                    mean = np.mean(values)
                    stddev = np.std(values)
                    confidence_interval = 1.96 * stddev / np.sqrt(len(values))

                    ax.errorbar(
                        x=j,
                        y=mean,
                        yerr=confidence_interval,
                        fmt='o',
                        capsize=15,
                        label=group
                    )

                # Customize plot
                ax.set_xticks(range(len(grouped_data)))
                ax.set_xticklabels(grouped_data.groups.keys())
                ax.set_ylabel('Values')
                ax.set_title(column)
                ax.legend(loc='best')
                ax.grid(True)

            # Hide extra subplots
            for i in range(n_subplots, len(axes)):
                self.figure.delaxes(axes[i])

            # Adjust layout
            plt.subplots_adjust(hspace=0.4)

        else:
            # Create single figure without grouping
            self.figure = plt.figure(figsize=FIGURE_SIZE_DEFAULT)
            ax = self.figure.add_subplot(111)

            # Generate plots for each column
            for index, column in enumerate(df):
                mean = np.mean(df[column])
                stddev = np.std(df[column])
                confidence_interval = 1.96 * stddev / np.sqrt(len(df[column]))

                ax.errorbar(
                    x=index,
                    y=mean,
                    yerr=confidence_interval,
                    fmt='o',
                    capsize=15,
                    label=column
                )

                ax.set_ylabel('Values')
                ax.set_xticks([])
                ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=TITLE_PADDING)
                ax.legend(loc='best')
                ax.grid(True)

        plt.tight_layout()
        plt.close('all')
        return self.figure
