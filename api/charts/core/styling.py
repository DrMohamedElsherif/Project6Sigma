# api/charts/core/styling.py

import seaborn as sns

def draw_histogram(ax, data, bins=None, multiple=None, **kwargs):
    import seaborn as sns

    bins = bins or "auto"

    plot_kwargs = dict(
        data=data,
        bins=bins,
        ax=ax,
        **kwargs   # 🔥 THIS IS THE FIX
    )

    if multiple is not None:
        plot_kwargs["multiple"] = multiple

    sns.histplot(**plot_kwargs)