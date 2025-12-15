import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from api.schemas import BusinessLogicException
from api.charts.constants import FIGURE_SIZE_A4_PORTRAIT, TITLE_FONT_SIZE

class BaseBoxplot:
    """
    Base class with common logic for all boxplots.
    Subclasses override:
        - compute_statistics()
        - draw_boxplot()
        - postprocess()
    """

    request_model = None  # subclasses must set this

    def __init__(self, data: dict):
        try:
            validated = self.request_model(**data)
            self.project = validated.project
            self.step = validated.step
            self.config = validated.config
            self.data = validated.data
            self.figure = None
            self.statistics = None
        except Exception as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": str(e)}
            )

    # ------------------ HOOKS ------------------

    def compute_statistics(self, df):
        """Override if the plot needs descriptive stats."""
        return None

    def draw_boxplot(self, df, ax):
        """Default horizontal boxplot."""
        sns.boxplot(
            data=df,
            ax=ax,
            color="#a1d111",
            linecolor="black",
            showcaps=False,
            linewidth=1,
            flierprops={"marker": "x"},
            width=0.3
        )

    def postprocess(self, ax):
        """Override for extra decorations."""
        pass

    # -------------------------------------------

    def process(self):

        dataset_name = getattr(self.data, "dataset_name", "Dataset")
        df = pd.DataFrame(self.data.values)  # columns are Measurement1, Measurement2, etc.


        # compute statistics (optional)
        self.statistics = self.compute_statistics(df)

        # create figure
        self.figure = plt.figure(figsize=FIGURE_SIZE_A4_PORTRAIT)
        ax = self.figure.add_subplot(111)

        # draw boxplot
        self.draw_boxplot(df, ax)

        # styling
        ax.set_title(self.config.title, fontsize=TITLE_FONT_SIZE, pad=20)
        ax.grid(True, alpha=0.3)

        # hooks
        self.postprocess(ax)

        plt.close(self.figure)
        return self.figure

    def get_statistics(self):
        return self.statistics
