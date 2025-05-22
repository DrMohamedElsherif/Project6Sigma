import io
from io import BytesIO

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd  # type: ignore
import seaborn as sns  # type: ignore
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import numpy as np  # Added for statistical calculations

from api.schemas import BusinessLogicException
from ...utils.pdf_utils import add_header_or_footer_to_a4_portrait
from ..constants import COLOR_PALETTE

header_image_path = 'assets/img/Header.png'
footer_image_path = 'assets/img/Footer.png'

class MultiVariConfig(BaseModel):
    title: str
    settings: Optional[Dict[str, Any]] = None

class MultiVariData(BaseModel):
    values: Dict[str, List[Any]] = Field(..., min_length=1)

class MultiVariRequest(BaseModel):
    project: str
    step: str
    config: MultiVariConfig
    data: MultiVariData

class MultiVariChart:
    def __init__(self, data:dict):
        try:
            validated_data = MultiVariRequest(**data)
            self.project = validated_data.project
            self.step = validated_data.step
            self.config = validated_data.config
            self.data = validated_data.data

            if validated_data.data.values:
                iter_values = iter(validated_data.data.values.values())
                try:
                    first_list = next(iter_values)
                    first_len = len(first_list)
                    if first_len == 0:
                        raise BusinessLogicException(
                            error_code="error_no_data",
                            field="data.values",
                            details={"message": "No data provided in the values."}
                        )
                    if not all(len(lst) == first_len for lst in iter_values):
                        raise BusinessLogicException(
                            error_code="error_data_length",
                            field="data.values",
                            details={"message": "All columns must have the same number of data points."}
                        )

                except StopIteration:
                    raise BusinessLogicException(
                        error_code="error_no_data",
                        field="data.values",
                        details={"message": "No data provided in the values."}
                    )

        except ValueError as e:
            raise BusinessLogicException(
                error_code="error_validation",
                field=str(e),
                details={"message": f"Invalid or missing field: {str(e)}"}
            )
        
    def process(self):
        title = self.config.title
        settings = self.config.settings
        keys = list(self.data.values.keys())[:-1]
        keys_string = "|".join(keys)
        df = pd.DataFrame(self.data.values)

        pdf_io = io.BytesIO()

        # Define A4 size in inches for clarity
        a4_width_inches = 8.27
        a4_height_inches = 11.69

        with PdfPages(pdf_io) as pdf:
            # Initial figure setup, this one will be A4
            fig, axes = plt.subplot_mosaic([
                ['MultiVari']
            ], figsize=(a4_width_inches, a4_height_inches), dpi=300)
            # fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1) # Suptitle will be applied to final_plot_fig
            # Headers/footers will be applied to final_plot_fig

            # Determine x_cols and y_col from data
            columns = list(df.columns)
            if len(columns) < 2:
                raise BusinessLogicException(
                    error_code="error_data",
                    field="data.values",
                    details={"message": "At least two columns required: input(s) and output."}
                )
            x_cols = columns[:-1]
            y_col = columns[-1]

            # Map settings to function arguments with sensible defaults
            settings = settings or {}
            final_plot_fig = multi_vari_plot(
                df,
                x_cols=x_cols,
                y_col=y_col,
                connect_lines=settings.get('connect_lines', False),
                show_points=settings.get('show_points', False),
                show_min_max=settings.get('show_min_max', False),
                separate_factor_1=settings.get('separate_factor_1', False), # Pass the boolean
                separate_factor_2=settings.get('separate_factor_2', False), # Pass the boolean
                show_medians=settings.get('show_medians', False),
                connect_medians=settings.get('connect_medians', False),
                show_percentiles=settings.get('show_percentiles', False),
                show_mean=settings.get('show_mean', False), # This is for the separate mean markers/line
                connect_means=settings.get('connect_means', False),
                ci_95=settings.get('ci_95', False), # This is for pointplot's CI
                ax=axes['MultiVari'], # Pass the ax from subplot_mosaic
                keys_string=keys_string,
            )

            # If multi_vari_plot returned a new figure (due to faceting), 
            # the original `fig` is not the one with the plot.
            if final_plot_fig is not fig:
                plt.close(fig) # Close the unused initial figure
                # Explicitly set the FacetGrid figure size to A4
                final_plot_fig.set_size_inches(a4_width_inches, a4_height_inches)

            # Apply overall title and header/footer to the actual figure that was plotted on
            final_plot_fig.suptitle(title, fontsize=14, y=0.92, ha='left', x=0.1)
            add_header_or_footer_to_a4_portrait(final_plot_fig, header_image_path, position='header')
            add_header_or_footer_to_a4_portrait(final_plot_fig, footer_image_path, position='footer', page_number=1, total_pages=1)
            
            # Adjust layout carefully AFTER adding suptitle, footers, and setting figure size
            # Increase bottom margin to make space for the legend which is now at the bottom
            final_plot_fig.tight_layout(rect=[0.05, 0.22, 0.95, 0.88]) # rect=[left, bottom, right, top]

            # Save figure with a large bottom padding to make room for the legend
            pdf.savefig(final_plot_fig, bbox_inches='tight', pad_inches=0.5)
            plt.close(final_plot_fig)

        pdf_io.seek(0)
        plt.close('all')
        return pdf_io

def multi_vari_plot(
    df: pd.DataFrame,
    x_cols: List[str],
    y_col: str,
    connect_lines: bool = False,
    show_points: bool = False,
    show_min_max: bool = False,
    separate_factor_1: bool = False, # Boolean flag for faceting
    separate_factor_2: bool = False, # Boolean flag for faceting
    show_medians: bool = False,
    connect_medians: bool = False,
    show_percentiles: bool = False,
    show_mean: bool = False,
    connect_means: bool = False,
    ci_95: bool = False, 
    ax=None, # Matplotlib Axes for non-faceted plot
    keys_string: Optional[str] = None
):
    """
    Create a multi-vari plot for 1-4 input columns (x_cols) and one output column (y_col).
    Optional settings for lines, points, statistics, and faceting.
    Returns the matplotlib Figure object.
    """
    n_factors = len(x_cols)
    if n_factors < 1 or n_factors > 4:
        raise ValueError("x_cols must have between 1 and 4 elements.")
    
    plot_df = df.copy()

    # Determine faceting column names based on boolean flags
    facet_col_var = x_cols[1] if separate_factor_1 and n_factors >= 2 else None
    facet_row_var = x_cols[2] if separate_factor_2 and n_factors >= 3 else None

    fig_to_return = None

    if facet_col_var or facet_row_var:
        # Faceting is active. FacetGrid creates its own figure. `ax` argument is ignored.
        x_in_facet = x_cols[0]
        hue_in_facet = None
        
        # Determine hue for plots within facets
        # This logic assigns the next available x_col (not used for x or faceting) as hue.
        temp_remaining_cols = [col for col in x_cols if col not in [x_in_facet, facet_col_var, facet_row_var]]
        if temp_remaining_cols:
            hue_in_facet = temp_remaining_cols[0]

        # Check if we have enough data points per facet to create a meaningful plot
        facet_combinations = plot_df.groupby([col for col in [facet_col_var, facet_row_var] if col is not None]).size()
        if (facet_combinations == 0).any():
            raise ValueError("Some facet combinations have no data points. Consider using fewer faceting variables.")

        g = sns.FacetGrid(plot_df, col=facet_col_var, row=facet_row_var, margin_titles=True, sharey=True, height=4, aspect=1.2) # Adjust height/aspect as needed
        
        order_for_x_in_facet = sorted(list(plot_df[x_in_facet].unique()))

        current_errorbar_arg = 'ci' if ci_95 else None
        current_err_kws = {'linewidth': 0.5} if current_errorbar_arg else None

        plot_palette_facet = COLOR_PALETTE
        if hue_in_facet:
            num_hue_levels_facet = plot_df[hue_in_facet].nunique()
            plot_palette_facet = COLOR_PALETTE[:num_hue_levels_facet]

        g.map_dataframe(
            safe_pointplot_wrapper, # Use the wrapper to catch errors
            x=x_in_facet,
            y=y_col,
            hue=hue_in_facet,
            order=order_for_x_in_facet,
            dodge=True if hue_in_facet else False,
            capsize=0.0, # Set capsize to 0
            linestyles="-" if connect_lines else "None",
            estimator=np.mean,
            errorbar=current_errorbar_arg,
            err_kws=current_err_kws,
            palette=plot_palette_facet
        )

        if show_points:

            strip_palette_arg_facet = None
            strip_color_arg_facet = COLOR_PALETTE[0] if COLOR_PALETTE else "dimgray"
            if hue_in_facet:
                strip_palette_arg_facet = plot_palette_facet
                strip_color_arg_facet = None

            g.map_dataframe(
                sns.stripplot,
                x=x_in_facet,
                y=y_col,
                hue=hue_in_facet,
                order=order_for_x_in_facet,
                dodge=True if hue_in_facet else False,
                palette=strip_palette_arg_facet,
                color=strip_color_arg_facet,
                alpha=0.7,
                jitter=True
            )
        
        if show_min_max:
            g.map_dataframe(
                show_min_max_facet,
                x=x_in_facet,
                y=y_col,
                hue=hue_in_facet,
                order=order_for_x_in_facet
            )

        if show_percentiles:
            g.map_dataframe(
                show_percentiles_facet,
                x=x_in_facet,
                y=y_col,
                hue=hue_in_facet,
                order=order_for_x_in_facet
            )

        if show_medians:
            g.map_dataframe(
                show_medians_facet,
                x=x_in_facet,
                y=y_col,
                hue=hue_in_facet,
                order=order_for_x_in_facet,
                connect_medians=connect_medians
            )

        if show_mean:
            g.map_dataframe(
                show_means_facet,
                x=x_in_facet,
                y=y_col,
                hue=hue_in_facet,
                order=order_for_x_in_facet,
                connect_means=connect_means
            )

        # Move the legend to be centered underneath the plot
        if hue_in_facet:
            # Remove any existing legend
            for ax_facet in g.axes.flat:
                if ax_facet.get_legend() is not None:
                    ax_facet.get_legend().remove()
            
            # Add a new legend at the figure level, centered below the plot
            # Position higher (0.1 instead of 0.05) to make it more visible
            handles, labels = g.axes.flat[0].get_legend_handles_labels()
            if handles:  # Only add legend if there are items to show
                g.figure.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.15), 
                                ncol=min(4, len(handles)), frameon=True, fontsize=10,
                                title=hue_in_facet if hue_in_facet else "")
        else:
            # Get handles and labels from the first subplot if available
            handles, labels = [], []
            if len(g.axes.flat) > 0:
                handles, labels = g.axes.flat[0].get_legend_handles_labels()
            
            # Add a simple legend even when no hue is used (for other plot elements)
            g.figure.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.15), 
                            ncol=min(4, len(handles)) if handles else 1, frameon=True, fontsize=10)
            
        g.set_axis_labels(x_var=x_in_facet, y_var=y_col) # Use actual column names for labels
        g.set_titles(col_template="{col_var}={col_name}", row_template="{row_var}={row_name}")

        # Don't apply grid when using facets
        for ax_facet in g.axes.flat:
            # Rotate tick labels
            for label in ax_facet.get_xticklabels():
                label.set_rotation(90)
        
        g.tight_layout()

        fig_to_return = g.figure

    else: # No faceting, plot on the provided `ax`.
        if ax is None: # Should not happen if called from MultiVariChart.process
            # Fallback for standalone use: create a figure and axis
            fig_obj, ax = plt.subplots(figsize=(6 + 2 * n_factors, 6))
            fig_to_return = fig_obj
        else:
            fig_to_return = ax.figure

        # Define x_axis, hue, and order for non-faceted plots
        x_axis_name_nf = x_cols[0]
        hue_name_nf = None
        # Create a combined category for x-axis if multiple factors are not used for hue
        
        if n_factors == 1:
            order_nf = sorted(list(plot_df[x_axis_name_nf].unique()))
            base_color = COLOR_PALETTE[0] if COLOR_PALETTE else "blue"
            sns.pointplot(data=plot_df, x=x_axis_name_nf, y=y_col, order=order_nf, color=base_color, ax=ax,
                          capsize=.1, linestyles="-" if connect_lines else "None", estimator=np.mean,
                          errorbar='ci' if ci_95 else None, err_kws={'linewidth': 0.5})
            if show_points:
                sns.stripplot(data=plot_df, x=x_axis_name_nf, y=y_col, order=order_nf, color=base_color, alpha=0.7, ax=ax)
        
        elif n_factors >= 2:
            # Default: x_cols[0] is x, x_cols[1] is hue.
            # If more factors (x_cols[2], x_cols[3]), they are combined into the x-axis with x_cols[0].
            hue_name_nf = x_cols[1] # Tentatively x_cols[1] is hue
            
            cols_for_x_axis_nf = [x_cols[0]]
            if n_factors > 2: # If x_cols[2] exists, add it to x-axis combination
                cols_for_x_axis_nf.append(x_cols[2])
            if n_factors > 3: # If x_cols[3] exists, add it to x-axis combination
                cols_for_x_axis_nf.append(x_cols[3])

            if len(cols_for_x_axis_nf) > 1:
                plot_df["_combined_x_nf"] = plot_df[cols_for_x_axis_nf].apply(lambda row: " | ".join(row.astype(str)), axis=1)
                x_axis_name_nf = "_combined_x_nf"
            # else x_axis_name_nf remains x_cols[0]
            
            order_nf = sorted(list(plot_df[x_axis_name_nf].unique()))

            plot_palette_nf = COLOR_PALETTE
            if hue_name_nf:
                num_hue_levels_nf = plot_df[hue_name_nf].nunique()
                plot_palette_nf = COLOR_PALETTE[:num_hue_levels_nf]

            sns.pointplot(data=plot_df, x=x_axis_name_nf, y=y_col, hue=hue_name_nf, order=order_nf, ax=ax,
                          dodge=True, capsize=.1, linestyles="-" if connect_lines else "None",
                          estimator=np.mean, errorbar='ci' if ci_95 else None, err_kws={'linewidth': 0.5},
                          palette=plot_palette_nf)
            if show_points:

                strip_palette_arg_nf = None
                strip_color_arg_nf = COLOR_PALETTE[0] if COLOR_PALETTE else "dimgray"
                if hue_name_nf:
                    strip_palette_arg_nf = plot_palette_nf
                    strip_color_arg_nf = None

                sns.stripplot(data=plot_df, x=x_axis_name_nf, y=y_col, hue=hue_name_nf, order=order_nf, ax=ax,
                              dodge=True, palette=strip_palette_arg_nf,
                              color=strip_color_arg_nf,
                              alpha=0.7, jitter=True)
        
        ax.set_xlabel(keys_string if x_axis_name_nf == x_cols[0] and len(x_cols) == 1 else x_axis_name_nf.replace("_combined_x_nf", "Combined Factors"))
        ax.set_ylabel(y_col)
        # Title is set by the caller using suptitle on the figure

        # Ensure x-ticks are set correctly for non-faceted plots
        ax.set_xticks(range(len(order_nf)))
        ax.set_xticklabels([str(lbl).replace(" | ", "\n") for lbl in order_nf], rotation=90)
        ax.grid(True, alpha=0.3)

        # --- Manual Stats Plotting (show_min_max, etc.) for non-faceted plots ---
        # This section uses: ax, x_axis_name_nf, hue_name_nf, order_nf (as plot_categories_on_xaxis)
        plot_categories_on_xaxis = order_nf

        if show_min_max:
            group_cols_stats = [x_axis_name_nf]
            if hue_name_nf:
                 group_cols_stats.append(hue_name_nf)
            
            # ... (rest of show_min_max logic as in your existing code, using these variables)
            # Make sure to use category_to_pos = {cat: i for i, cat in enumerate(plot_categories_on_xaxis)}
            # And when plotting error bars with hue, use hue_name_nf and COLOR_PALETTE
            # For example, in the loop for hue_name_nf:
            #   color_idx = hue_map[hue_cat_val] % len(COLOR_PALETTE)
            #   bar_color = COLOR_PALETTE[color_idx]
            #   ax.errorbar(..., ecolor=bar_color, ...)
            # If no hue_name_nf:
            #   ax.errorbar(..., ecolor=COLOR_PALETTE[1] if len(COLOR_PALETTE) > 1 else "black", ...)

            # Simplified example for show_min_max (needs full logic from your original)
            grouped_stats = plot_df.groupby(group_cols_stats)[y_col]
            min_vals_stats = grouped_stats.min()
            max_vals_stats = grouped_stats.max()
            center_vals_stats = grouped_stats.mean() # Or median if preferred
            
            category_to_pos_stats = {cat: i for i, cat in enumerate(plot_categories_on_xaxis)}

            if hue_name_nf:
                hue_categories_stats = sorted(list(plot_df[hue_name_nf].unique()))
                n_hues_stats = len(hue_categories_stats)
                hue_map_stats = {hue_val: j for j, hue_val in enumerate(hue_categories_stats)}
                dodge_width_stats = 0.8 
                
                plotted_min_max_labels = set() # To avoid duplicate legend entries

                for idx_stats, center_val_stat in center_vals_stats.items():
                    primary_cat_stat, hue_cat_stat = idx_stats # Assuming MultiIndex
                    base_pos_stat = category_to_pos_stats[primary_cat_stat]
                    hue_idx_stat = hue_map_stats[hue_cat_stat]
                    offset_stat = (hue_idx_stat - (n_hues_stats - 1) / 2.0) * (dodge_width_stats / n_hues_stats)
                    x_pos_stat = base_pos_stat + offset_stat
                    
                    y_err_min_stat = center_val_stat - min_vals_stats[idx_stats]
                    y_err_max_stat = max_vals_stats[idx_stats] - center_val_stat
                    
                    color_idx_stat = hue_idx_stat % len(COLOR_PALETTE)
                    bar_color_stat = COLOR_PALETTE[color_idx_stat]
                    
                    label_mm = None
                    if hue_cat_stat not in plotted_min_max_labels:
                        label_mm = f'Min/Max ({hue_cat_stat})'
                        plotted_min_max_labels.add(hue_cat_stat)

                    ax.errorbar(x=[x_pos_stat], y=[center_val_stat], yerr=[[y_err_min_stat], [y_err_max_stat]],
                                fmt='none', ecolor=bar_color_stat, elinewidth=1.5, capsize=5, label=label_mm, zorder=5)
            else: # No hue
                x_positions_stats = [category_to_pos_stats[cat] for cat in center_vals_stats.index]
                ax.errorbar(x=x_positions_stats, y=center_vals_stats, 
                            yerr=[center_vals_stats - min_vals_stats, max_vals_stats - center_vals_stats],
                            fmt='none', ecolor=COLOR_PALETTE[1] if len(COLOR_PALETTE) > 1 else "darkgray", 
                            elinewidth=1.5, capsize=5, label='Min/Max', zorder=5)


        if show_medians or connect_medians:
            # Groups by the main x-axis only for the overall median line/points
            medians_series = plot_df.groupby(x_axis_name_nf)[y_col].median().reindex(plot_categories_on_xaxis).dropna()
            if not medians_series.empty:
                y_values = medians_series.values
                x_positions = [plot_categories_on_xaxis.index(cat) for cat in medians_series.index]
                median_color = "#FF5733"
                # median_color = COLOR_PALETTE[3] if len(COLOR_PALETTE) > 3 else "orange"
                ax.scatter(x_positions, y_values, color=median_color, marker='D', label='Median', zorder=9)
                if connect_medians: # Connect overall medians
                    ax.plot(x_positions, y_values, color=median_color, linestyle='--', label='_nolegend_', zorder=9)

        if show_mean or connect_means: # For overall mean line/points by main x-axis
            means_series = plot_df.groupby(x_axis_name_nf)[y_col].mean().reindex(plot_categories_on_xaxis).dropna()
            if not means_series.empty:
                y_values = means_series.values
                x_positions = [plot_categories_on_xaxis.index(cat) for cat in means_series.index]
                mean_color = "#143f66"
                # mean_color = COLOR_PALETTE[4] if len(COLOR_PALETTE) > 4 else "green"
                ax.scatter(x_positions, y_values, color=mean_color, marker='X', label='Mean', zorder=10)
                if connect_means: # Connect overall means
                    ax.plot(x_positions, y_values, color=mean_color, linestyle='-.', label='_nolegend_', zorder=10)
        
        # Consolidate legend for non-faceted plot
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles)) # Remove duplicates
        
        # Remove any existing legend
        if ax.get_legend() is not None:
            ax.get_legend().remove()
        
        # Add a new legend centered below the plot with improved visibility
        if by_label:  # Only add legend if there are items to show
            fig_to_return.legend(
                by_label.values(), 
                by_label.keys(), 
                loc='upper center', 
                bbox_to_anchor=(0.5, 0.15),  # Adjusted position to be more visible
                ncol=min(4, len(by_label)),
                frameon=True,  # Add a frame around the legend
                fontsize=10
            )

    return fig_to_return

def safe_pointplot_wrapper(data, **kwargs_for_plot):
    """
    Wrapper for sns.pointplot to catch and handle errors gracefully for a single facet.
    `data`and `color`(and `label`) are passed by FacetGrid.map_dataframe.
    Other arguments (x, y, hue, order, etc.) are passed from the map_dataframe call.
    """
    try: 
        sns.pointplot(data=data, **kwargs_for_plot)
    except ZeroDivisionError as e:
        x_var = kwargs_for_plot.get('x')
        y_var = kwargs_for_plot.get('y')
        hue_var = kwargs_for_plot.get('hue')
        # Construct a meaningful error message
        print(f"Warning: ZeroDivisionError in sns.pointplot for a facet.\n"
                f"  Plotting with: x='{x_var}', y='{y_var}', hue='{hue_var}'. Error: {e}.\n"
                f"  The pointplot for this specific facet might be missing or incomplete.\n"
                f"  This can occur if a group within the facet has too few data points (e.g., <2) for error bar calculation (if active), "
                f"or if all y-values in a group are identical leading to zero variance, or other internal calculation issues.")
    except Exception as e: # Catch other potential plotting errors
        x_var = kwargs_for_plot.get('x')
        y_var = kwargs_for_plot.get('y')
        hue_var = kwargs_for_plot.get('hue')
        print(f"Warning: An unexpected error ('{type(e).__name__}') occurred in sns.pointplot for a facet.\n"
                f"  Plotting with: x='{x_var}', y='{y_var}', hue='{hue_var}'. Error: {e}.\n"
                f"  The pointplot for this specific facet might be missing or incomplete.")

def show_min_max_facet(data, x, y, hue=None, order=None, **kwargs):
    """
    Custom function to add min/max error bars to facet plots.
    This is designed to be used with FacetGrid's map_dataframe.
    """
    ax = plt.gca()  # Get the current axes (facet subplot)
    
    # Create a category to position mapping for x-axis placement
    plot_categories = order if order is not None else sorted(list(data[x].unique()))
    category_to_pos = {cat: i for i, cat in enumerate(plot_categories)}
    
    # Group by x and hue if applicable
    group_cols = [x]
    if hue is not None:
        group_cols.append(hue)
    
    # Calculate statistics
    grouped = data.groupby(group_cols)[y]
    min_vals = grouped.min()
    max_vals = grouped.max()
    center_vals = grouped.mean()  # Use mean as the center for error bars
    
    if hue is not None:
        # Handle case with hue (multiple groups per x-category)
        hue_categories = sorted(list(data[hue].unique()))
        n_hues = len(hue_categories)
        hue_map = {hue_val: j for j, hue_val in enumerate(hue_categories)}
        dodge_width = 0.8  # Width available for dodging within a category
        
        # Keep track of plotted labels to avoid duplicates in legend
        plotted_labels = set()
        
        for idx, center_val in center_vals.items():
            try:
                primary_cat, hue_cat = idx  # Assuming MultiIndex from groupby with x and hue
                base_pos = category_to_pos[primary_cat]
                hue_idx = hue_map[hue_cat]
                offset = (hue_idx - (n_hues - 1) / 2.0) * (dodge_width / n_hues)
                x_pos = base_pos + offset
                
                y_err_min = center_val - min_vals[idx]
                y_err_max = max_vals[idx] - center_val
                
                # Use color from palette based on hue index
                color_idx = hue_idx % len(COLOR_PALETTE)
                bar_color = COLOR_PALETTE[color_idx]
                
                # Only add label to legend once per hue category
                label = None
                if hue_cat not in plotted_labels:
                    label = f'Min/Max ({hue_cat})'
                    plotted_labels.add(hue_cat)
                
                ax.errorbar(x=[x_pos], y=[center_val], yerr=[[y_err_min], [y_err_max]],
                            fmt='none', ecolor=bar_color, elinewidth=1.5, capsize=5, label=label, zorder=5)
            except Exception as e:
                print(f"Warning: Error plotting min/max for {idx}: {e}")
    else:
        # Handle case without hue (one group per x-category)
        try:
            x_positions = [category_to_pos[cat] for cat in center_vals.index]
            ax.errorbar(x=x_positions, y=center_vals,
                        yerr=[center_vals - min_vals, max_vals - center_vals],
                        fmt='none', ecolor=COLOR_PALETTE[1] if len(COLOR_PALETTE) > 1 else "darkgray",
                        elinewidth=1.5, capsize=5, label='Min/Max', zorder=5)
        except Exception as e:
            print(f"Warning: Error plotting simple min/max: {e}")

def show_percentiles_facet(data, x, y, hue=None, order=None, **kwargs):
    """
    Custom function to add 25th/75th percentile error bars to facet plots.
    This is designed to be used with FacetGrid's map_dataframe.
    """
    ax = plt.gca()  # Get the current axes (facet subplot)
    
    # Create a category to position mapping for x-axis placement
    plot_categories = order if order is not None else sorted(list(data[x].unique()))
    category_to_pos = {cat: i for i, cat in enumerate(plot_categories)}
    
    # Group by x and hue if applicable
    group_cols = [x]
    if hue is not None:
        group_cols.append(hue)
    
    # Calculate statistics
    grouped = data.groupby(group_cols)[y]
    q25 = grouped.quantile(0.25)
    q75 = grouped.quantile(0.75)
    median_vals = grouped.median()  # Use median as the center for percentile bars
    
    if hue is not None:
        # Handle case with hue (multiple groups per x-category)
        hue_categories = sorted(list(data[hue].unique()))
        n_hues = len(hue_categories)
        hue_map = {hue_val: j for j, hue_val in enumerate(hue_categories)}
        dodge_width = 0.8  # Width available for dodging within a category
        
        # Keep track of plotted labels to avoid duplicates in legend
        plotted_labels = set()
        
        for idx, median_val in median_vals.items():
            try:
                primary_cat, hue_cat = idx  # Assuming MultiIndex from groupby with x and hue
                base_pos = category_to_pos[primary_cat]
                hue_idx = hue_map[hue_cat]
                offset = (hue_idx - (n_hues - 1) / 2.0) * (dodge_width / n_hues)
                x_pos = base_pos + offset
                
                y_err_25 = median_val - q25[idx]
                y_err_75 = q75[idx] - median_val
                
                # Use color from palette based on hue index
                color_idx = hue_idx % len(COLOR_PALETTE)
                bar_color = COLOR_PALETTE[color_idx]
                
                # Only add label to legend once per hue category
                label = None
                if hue_cat not in plotted_labels:
                    label = f'25th-75th ({hue_cat})'
                    plotted_labels.add(hue_cat)
                
                ax.errorbar(x=[x_pos], y=[median_val], yerr=[[y_err_25], [y_err_75]],
                            fmt='none', ecolor=bar_color, elinewidth=1.0, capsize=3, alpha=0.7, label=label, zorder=4)
            except Exception as e:
                print(f"Warning: Error plotting percentiles for {idx}: {e}")
    else:
        # Handle case without hue (one group per x-category)
        try:
            x_positions = [category_to_pos[cat] for cat in median_vals.index]
            ax.errorbar(x=x_positions, y=median_vals,
                        yerr=[median_vals - q25, q75 - median_vals],
                        fmt='none', ecolor=COLOR_PALETTE[2] if len(COLOR_PALETTE) > 2 else "lightblue",
                        elinewidth=1.0, capsize=3, alpha=0.7, label='25th-75th Percentile', zorder=4)
        except Exception as e:
            print(f"Warning: Error plotting simple percentiles: {e}")

def show_medians_facet(data, x, y, hue=None, order=None, connect_medians=False, **kwargs):
    """
    Custom function to add median points and optionally connect them with lines.
    This is designed to be used with FacetGrid's map_dataframe.
    """
    ax = plt.gca()  # Get the current axes (facet subplot)
    
    # Create a category to position mapping for x-axis placement
    plot_categories = order if order is not None else sorted(list(data[x].unique()))
    category_to_pos = {cat: i for i, cat in enumerate(plot_categories)}
    
    # Calculate medians by x category
    medians_series = data.groupby(x)[y].median().reindex(plot_categories).dropna()
    if medians_series.empty:
        return
    
    # Get positions and values for plotting
    y_values = medians_series.values
    x_positions = [category_to_pos[cat] for cat in medians_series.index]
    
    # Use a distinct color for median
    median_color = "#FF5733"
    # median_color = COLOR_PALETTE[3] if len(COLOR_PALETTE) > 3 else "orange"
    
    # Plot median points
    ax.scatter(x_positions, y_values, color=median_color, marker='D', s=50, 
              label='Median', zorder=9, alpha=0.8)
    
    # Optionally connect with lines
    if connect_medians and len(x_positions) > 1:
        ax.plot(x_positions, y_values, color=median_color, linestyle='--', 
               label='_nolegend_', zorder=9, alpha=0.7)

def show_means_facet(data, x, y, hue=None, order=None, connect_means=False, **kwargs):
    """
    Custom function to add mean points and optionally connect them with lines.
    This is designed to be used with FacetGrid's map_dataframe.
    """
    ax = plt.gca()  # Get the current axes (facet subplot)
    
    # Create a category to position mapping for x-axis placement
    plot_categories = order if order is not None else sorted(list(data[x].unique()))
    category_to_pos = {cat: i for i, cat in enumerate(plot_categories)}
    
    # Calculate means by x category
    means_series = data.groupby(x)[y].mean().reindex(plot_categories).dropna()
    if means_series.empty:
        return
    
    # Get positions and values for plotting
    y_values = means_series.values
    x_positions = [category_to_pos[cat] for cat in means_series.index]
    
    # Use a distinct color for mean
    mean_color = "#143f66"
    # mean_color = COLOR_PALETTE[4] if len(COLOR_PALETTE) > 4 else "green"
    
    # Plot mean points
    ax.scatter(x_positions, y_values, color=mean_color, marker='X', s=50,
              label='Mean', zorder=10, alpha=0.8)
    
    # Optionally connect with lines
    if connect_means and len(x_positions) > 1:
        ax.plot(x_positions, y_values, color=mean_color, linestyle='-.',
               label='_nolegend_', zorder=10, alpha=0.7)
