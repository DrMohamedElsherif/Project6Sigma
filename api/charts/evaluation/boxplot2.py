from .base_boxplot import BaseBoxplot
from .boxplot_schemas import BoxplotRequest


class Boxplot2(BaseBoxplot):
    request_model = BoxplotRequest





# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# from pydantic import BaseModel, Field
# from typing import List, Dict
# from api.schemas import BusinessLogicException
# from api.charts.constants import COLOR_BLUE, FIGURE_SIZE_A4_PORTRAIT, COLOR_BLACK, TITLE_FONT_SIZE
# from api.charts.statistics import calculate_descriptive_stats, add_stats_table

    

# class Boxplot2Config(BaseModel):
#     title: str


# class Boxplot2Data(BaseModel):
#     values: Dict[str, List[float]] = Field(..., min_length=1)


# class Boxplot2Request(BaseModel):
#     project: str
#     step: str
#     config: Boxplot2Config
#     data: Boxplot2Data


# class Boxplot2:
#     def __init__(self, data: dict):
#         try:
#             validated_data = Boxplot2Request(**data)
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

#         self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)

#         plt.subplots_adjust(top=0.85, bottom=0.4, left=0.15, right=0.85)

#         sns.set_style("whitegrid")

#         ax = self.figure.add_subplot(111)

#         sns.boxplot(
#             data=df,
#             color='#a1d111',
#             linecolor='black',
#             linewidth=1,
#             flierprops={'marker': 'x'},
#             width=0.3,
#         )
        
#         ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=20)
#         ax.grid(True, alpha=0.3)
#         plt.close('all')
#         return self.figure
    

    
    