
# api/charts/core/chart_styling.py

import seaborn as sns


sns.set_theme(style="whitegrid")

def draw_histogram(ax, data, bins=None, multiple=None, **kwargs):

    bins = bins or "auto"

    plot_kwargs = dict(
        data=data,
        bins=bins,
        ax=ax,
        **kwargs   
    )

    if multiple is not None:
        plot_kwargs["multiple"] = multiple

    sns.histplot(**plot_kwargs)
    
    
def draw_boxplot(ax, data, **kwargs):
    sns.boxplot(data=data, ax=ax, **kwargs)