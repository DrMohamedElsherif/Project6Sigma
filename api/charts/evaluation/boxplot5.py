import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest
from api.charts.constants import TITLE_FONT_SIZE


class Boxplot5(BaseBoxplot):
    request_model = BoxplotRequest

    def process(self):
        df = pd.DataFrame(self.data.values)
        categories = self.data.categories

        if categories:
            categories_df = pd.DataFrame(categories)
            unique_categories = categories_df.iloc[:, 0].unique()
            count = len(unique_categories)

            self.figure, axes = plt.subplots(
                1, count, figsize=(11.7, 8.3), sharex=True, sharey=True
            )

            for i, (category, data) in enumerate(
                df.join(categories_df).groupby(categories_df.columns[0])
            ):
                sns.boxplot(
                    data=data,
                    ax=axes[i],
                    color="#a1d111",
                    linewidth=1,
                    showcaps=False,
                    flierprops={"marker": "x"}
                )
                axes[i].set_xlabel(unique_categories[i])

            self.figure.suptitle(self.config.title, fontsize=TITLE_FONT_SIZE)
            plt.tight_layout()
            plt.close(self.figure)
            return self.figure

        # fallback to default behavior
        return super().process()




# import pandas as pd
# import matplotlib.pyplot as plt
# from pydantic import BaseModel, Field
# from typing import List, Dict, Optional
# from api.schemas import BusinessLogicException
# from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE, COLOR_BLACK, COLOR_BLUE
# import seaborn as sns


# class Boxplot5Config(BaseModel):
#     title: str


# class Boxplot5Data(BaseModel):
#     values: Dict[str, List[float]] = Field(..., min_length=1)
#     categories: Optional[Dict[str, List[str]]] = None


# class Boxplot5Request(BaseModel):
#     project: str
#     step: str
#     config: Boxplot5Config
#     data: Boxplot5Data


# class Boxplot5:
#     def __init__(self, data: dict):
#         try:
#             validated_data = Boxplot5Request(**data)
#             self.project = validated_data.project
#             self.step = validated_data.step
#             self.config = validated_data.config
#             self.data = validated_data.data
#             self.figure = None

#         except ValueError as e:
#             raise BusinessLogicException(
#                 error_code="error_validation",
#                 field=str(e),
#                 details={"message": f"Invalid or missing field: {str(e)}"}
#             )

#     def process(self):
#         title = self.config.title
#         df = pd.DataFrame(self.data.values)
#         categories_data = self.data.categories

#         if categories_data is not None:
#             categories_df = pd.DataFrame(categories_data)
#             unique_categories = categories_df.iloc[:, 0].unique()
#             count = len(unique_categories)

#             self.figure, axes = plt.subplots(
#                 1, count, figsize=FIGURE_SIZE_A4_PORTRAIT, sharex=True, sharey=True)

#             for i, (category, data) in enumerate(df.join(categories_df).groupby(categories_df.columns[0])):
#                 ax = axes[i]
#                 sns.boxplot(
#                     data=data,
#                     ax=ax,
#                     color="#a1d111",
#                     linewidth=1,
#                     width=0.3,
#                     flierprops={"marker": "x"},
#                     showcaps=False,
#                     boxprops={"edgecolor": "black"},
#                     whiskerprops={"color": "black"},
#                     capprops={"color": "black"}
#                 )
#                 ax.set_xlabel(unique_categories[i])

#             self.figure.suptitle(title, fontsize=TITLE_FONT_SIZE, y=0.99)
#             plt.tight_layout()

#         else:
#             self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
#             ax = self.figure.add_subplot(111)

#             sns.boxplot(
#                 data=df,
#                 ax=ax,
#                 color="#a1d111",
#                 linewidth=1,
#                 showcaps=False,
#                 flierprops={"marker": "x"},
#                 width=0.3,
#                 boxprops=dict(edgecolor='black')
#             )

#             ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)

#         plt.grid(True, alpha=0.3)
#         plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)
#         plt.close('all')
#         return self.figure
