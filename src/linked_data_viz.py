import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib.cm import ScalarMappable, get_cmap
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize
from matplotlib.dates import DateFormatter, YearLocator
from matplotlib.patches import Rectangle
from statsmodels.tsa.seasonal import seasonal_decompose

from src.settings import DATA_DIR


def plot_diseases_bar(df, cols_list, category="CD", city=""):
    count_df = df[cols_list].sum().sort_values(ascending=True)
    count_df.plot(kind="barh")

    if city == "":
        # Set the title and labels
        plt.title(f"Total historical sum of {category}s")
        plt.xlabel("Diseases")
        plt.ylabel("Sum of Cases")

        plt.show()
    else:
        # Set the title and labels
        plt.title(f"Total historical sum of {category}s - {city}")
        plt.xlabel("Diseases")
        plt.ylabel("Sum of Cases")

        plt.show()


def plot_health_access(iso_gdf, city, pct_cols, save_df=False):
    fig, axs = plt.subplots(1, 3, figsize=(14, 6))
    # Define the number of rows and columns for subplots

    city_data = iso_gdf[iso_gdf["adm3_en"] == city]

    if save_df:
        keep_only = [
            "adm3_en",
            "adm4_pcode",
            "brgy_healthcenter_pop_reached_pct_5min",
            "hospital_pop_reached_pct_5min",
            "geometry",
        ]
        df_to_save = city_data[keep_only]
        df_to_save.to_csv(DATA_DIR / f"linked_data/processed/{city}_choropleths.csv")

    # Define colormap and normalization
    cmap = get_cmap("viridis")
    norm = Normalize(
        vmin=city_data[pct_cols].min().min(), vmax=city_data[pct_cols].max().max()
    )

    # Iterate over the columns and plot each one
    for ax, column in zip(axs, pct_cols):
        city_data.plot(
            column=column,
            ax=ax,
            legend=True,
            cmap=cmap,
            norm=norm,
            legend_kwds={
                "label": f"% population reached in 5 mins \n in {city}",
                "orientation": "horizontal",
                "shrink": 0.8,
                "anchor": (0.5, 1),
            },
        )
        ax.set_title(f"{column}")
        ax.axis("off")  # Turn off the axis

    plt.tight_layout(
        rect=[0, 0.15, 1, 1]
    )  # Adjust the rect to leave space for the color bar
    plt.show()


def plot_diseases_bar(df, cols_list, category="CD", city=""):
    count_df = df[cols_list].sum().sort_values(ascending=True)
    count_df.plot(kind="barh")

    if city == "":
        # Set the title and labels
        plt.title(f"Total historical sum of {category}s")
        plt.xlabel("Diseases")
        plt.ylabel("Sum of Cases")

        plt.show()
    else:
        # Set the title and labels
        plt.title(f"Total historical sum of {category}s - {city}")
        plt.xlabel("Diseases")
        plt.ylabel("Sum of Cases")

        plt.show()


def plot_choropleth_all_cities(
    feat_df, feat_col, vmin, vmax, cmap="Reds", label="Population Density"
):
    # Ensure the data is grouped by the 'city' column
    # max_val = pop_df[pop_col].max()
    grouped = feat_df.groupby("adm3_en")

    # Number of cities
    num_cities = len(grouped)

    # Create subplots - adjust the number of rows and columns as needed
    fig, axs = plt.subplots(
        nrows=int(num_cities**0.5) + 1,
        ncols=int(num_cities**0.5) + 1,
        figsize=(18, 21),
    )
    axs = axs.flatten()  # Flatten the array of axes

    # Define colormap and normalization
    cmap = get_cmap(cmap)
    # norm = Normalize(vmin=pop_df[pop_col].min().min(), vmax=pop_df[pop_col].max())

    # Loop through each city and plot it
    for i, (city_name, data) in enumerate(grouped):
        ax = axs[i]
        data.plot(
            ax=ax,
            legend=True,
            column=feat_col,
            cmap=cmap,
            legend_kwds={
                "label": label,
                "orientation": "horizontal",
                "shrink": 0.8,
                "anchor": (0.5, 1),
            },
            vmin=vmin,
            vmax=vmax
            # vmax=pop_df[pop_col].describe(percentiles=[0.75, 0.9, 0.95])['95%']
        )  # Plot the data
        ax.set_title(f"{city_name}")
        ax.axis("off")  # Turn off axis

    # Hide any unused axes if there are any
    for j in range(i + 1, len(axs)):
        axs[j].set_visible(False)

    plt.tight_layout()  # Adjust the rect to leave space for the color bar
    # Show the plot
    # plt.show()
    # plt.savefig(DATA_DIR/"choropleth_hospital_access_5min.png", dpi=300)


def plot_pacsii_batch_data(
    batch_df,
    var_to_plot="water_supply_type_1",
    plot_title="Primary Water Supply Type",
    legend_title="Water Supply Type",
    color_scheme="viridis",
    bbox_anchor=(0.75, -0.1),
):

    # group by
    grouped_data = (
        batch_df.groupby(["adm3_en", var_to_plot]).size().unstack(fill_value=0)
    )

    # calculate percentages
    percentages = grouped_data.div(grouped_data.sum(axis=1), axis=0) * 100

    # plot
    ax = percentages.plot(kind="bar", stacked=True, figsize=(6, 6), cmap=color_scheme)

    # x-axis labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha="center")

    # add legend
    plt.legend(
        title=legend_title,
        bbox_to_anchor=bbox_anchor,
        loc="upper right",
        fontsize=8,
        title_fontsize=10,
    )

    # add title and labels
    plt.title(plot_title)
    plt.xlabel("")
    plt.ylabel("Percentage")

    # show labels
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        if height > 0.99:
            ax.annotate(
                f"{height:.1f}%",
                (x + width / 2, y + height / 2),
                ha="center",
                va="center",
                color="white",
                size=8,
            )
            text = ax.annotate(
                f"{height:.1f}%",
                (x + width / 2, y + height / 2),
                ha="center",
                va="center",
                color="black",
                size=7,
            )
            text.set_path_effects(
                [
                    path_effects.Stroke(linewidth=3, foreground="white"),
                    path_effects.Normal(),
                ]
            )
    # show plot
    plt.show()


def plot_pacsii_stacked_area_comparison(
    df,
    variable_of_interest,
    barangays_of_interest,
    title_label,
    legend_label,
):
    # fix values
    df[variable_of_interest] = (
        df[variable_of_interest].fillna("Unknown").replace({0: "No", 1: "Yes"})
    )

    # filter
    df["date"] = pd.to_datetime(df["date"])
    df = df[
        (df["adm4_pcode"].isin(barangays_of_interest)) & (df["date"].dt.year < 2021)
    ]

    # extract year
    df["year"] = df["date"].dt.year
    df["year"] = pd.to_datetime(df["year"], format="%Y")

    # group by
    grouped_data = (
        df.groupby(["year", variable_of_interest]).size().unstack(fill_value=0)
    )

    # percentages
    percentages = grouped_data.div(grouped_data.sum(axis=1), axis=0) * 100

    # plot
    ax = percentages.plot(kind="area", stacked=False, figsize=(12, 6), cmap="viridis")

    # legend
    plt.legend(
        title=legend_label,
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        fontsize=8,
        title_fontsize=10,
    )

    # title and labels
    plt.title(title_label)
    plt.xlabel("Year")
    plt.ylabel("Percentage")

    for column in percentages.columns:
        for index, value in percentages[column].items():
            text = ax.text(
                index,
                value,
                f"{value:.1f}%",
                color="black",
                ha="left",
                va="center",
                fontsize=8,
            )
            text.set_path_effects(
                [
                    path_effects.Stroke(linewidth=3, foreground="white"),
                    path_effects.Normal(),
                ]
            )

    # plot
    plt.show()


def plot_all_pacsii_sites(
    batch_df_edit,
    variable_of_interest,
    title_label,
    legend_label,
    bbox_anchor=(0.75, -0.1),
    fig_text_x=0.93,
    fig_text_y=0.64,
):
    # group by
    grouped_data = (
        batch_df_edit.groupby(["adm3_en", variable_of_interest], observed=False)
        .size()
        .unstack(fill_value=0)
    )

    # calculate percentages
    percentages = grouped_data.div(grouped_data.sum(axis=1), axis=0) * 100

    # plot
    ax = percentages.plot(kind="bar", stacked=True, figsize=(8, 6), cmap="viridis")

    # x-axis labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha="center")

    # legend
    plt.legend(
        title=legend_label,
        bbox_to_anchor=bbox_anchor,
        loc="upper right",
        fontsize=8,
        title_fontsize=10,
    )

    # title and labels
    plt.title(title_label)
    plt.xlabel("")
    plt.ylabel("Percentage")

    # labels
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        if height > 0.99:
            text = ax.annotate(
                f"{height:.1f}%",
                (x + width / 2, y + height / 2),
                ha="center",
                va="center",
                color="black",
                size=7,
            )
            text.set_path_effects(
                [
                    path_effects.Stroke(linewidth=3, foreground="white"),
                    path_effects.Normal(),
                ]
            )

    # note
    total_households = batch_df_edit.groupby("adm3_en").size()
    legend_text = [
        f"{year}: {total_households[year]} entries" for year in total_households.index
    ]
    plt.figtext(
        fig_text_x, fig_text_y, "\n".join(legend_text), fontsize=8, ha="left", va="top"
    )

    plt.show()


def plot_employment_treemap(df, variable_of_interest):
    # group by
    grouped_data = df.pivot_table(
        index=variable_of_interest, aggfunc="size", fill_value=0
    )
    unstacked_sum = grouped_data.reset_index()
    unstacked_sum.rename(columns={0: "sum"}, inplace=True)

    # treemap
    categories = [
        "armed forces occupations",
        "managers",
        "professionals",
        "technicians and associate professionals",
        "clerical support workers",
        "service and sales workers",
        "skilled agricultural, forestry and fishery workers",
        "craft and related trades workers",
        "plant and machine operators and assemblers",
        "elementary occupations",
    ]

    cmap = cm.get_cmap("viridis")
    colors = [cmap(i / len(categories)) for i in range(len(categories))]
    plotly_colors = [
        "rgb({}, {}, {})".format(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
        for c in colors
    ]
    color_map = dict(zip(categories, plotly_colors))
    color_map["(?)"] = "black"

    fig = px.treemap(
        unstacked_sum,
        path=[variable_of_interest],
        values="sum",
        color=variable_of_interest,
        hover_data=["sum"],
        color_discrete_map=color_map,
    )

    fig.update_traces(
        textinfo="label+percent parent",
        insidetextfont=dict(color="black"),
        textfont=dict(color="black", size=30),
    )

    fig.update_layout(margin=dict(t=5, l=5, r=5, b=5))
    fig.show()


# functions
def plot_avg_males_females(df, color_scheme):
    avg_males_females = df.groupby("adm3_en")[
        ["n_family_members_male", "n_family_members_female"]
    ].mean()
    avg_males_females.plot(kind="bar", stacked=True, cmap=color_scheme)
    plt.xlabel("")
    plt.ylabel("# of members")
    plt.legend(["Males", "Females"])
    for i, val in enumerate(avg_males_females.values):
        plt.text(
            i, val[0] / 2, f"{val[0]:.2f}", ha="center", va="center", color="white"
        )
        plt.text(
            i,
            val[0] + val[1] / 2,
            f"{val[1]:.2f}",
            ha="center",
            va="center",
            color="black",
        )
    plt.xticks(rotation=0)
    plt.show()


def calculate_and_plot_percentage(df, column, label):
    grouped = df.groupby("adm3_en").agg(
        total_label=pd.NamedAgg(
            column=column, aggfunc=lambda x: (x >= 1).sum()
        ),  # Count only if >= 1
        total_rows=pd.NamedAgg(column="adm4_pcode", aggfunc="count"),
    )

    grouped["percentage"] = (grouped["total_label"] / grouped["total_rows"]) * 100
    return grouped["percentage"]


def get_colorscheme(n, cmap="viridis"):
    return [plt.cm.get_cmap(cmap, n)(i) for i in range(n)]


## for outbreaks
# tag prolonged outbreaks
def detect_outbreak_periods(tagged_df, target_class):
    tagged_df.sort_values(by=["date"], inplace=True)
    outbreak_mask = tagged_df[target_class] == 1

    outbreak_groups = (outbreak_mask != outbreak_mask.shift(fill_value=False)).cumsum()
    tagged_df["outbreak_group"] = outbreak_groups
    outbreak_df = tagged_df[outbreak_mask]
    outbreak_summary = (
        outbreak_df.groupby(["outbreak_group"])
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            actual_length_weeks=(target_class, "count"),
        )
        .reset_index()
    )
    return outbreak_summary


# plot outbreaks and climate var
def plot_outbreaks_precip(
    dataframe,
    casetype,
    axis1_color,
    axis1_label,
    variable_of_interest,
    axis2_color,
    axis2_label,
    outbreak_color,
    outbreak_markers,
    title,
    major_outbreak_color,
):
    dataframe["date"] = pd.to_datetime(dataframe["date"])

    # plot
    fig, ax1 = plt.subplots(figsize=(18, 6))

    # cases
    ax1.plot(
        dataframe["date"], dataframe[casetype], color=axis1_color, label=axis1_label
    )
    ax1.set_xlabel("Time")
    ax1.set_ylabel(axis1_label, color=axis1_color)
    ax1.tick_params("y", colors=axis1_color)

    # variable of interest
    ax2 = ax1.twinx()
    ax2.plot(
        dataframe["date"],
        dataframe[variable_of_interest],
        color=axis2_color,
        label=axis2_label,
    )
    ax2.set_ylabel(axis2_label, color=axis2_color)
    ax2.tick_params("y", colors=axis2_color)

    # outbreak
    outbreak_dates = dataframe[dataframe["outbreak"] == 1]["date"]
    outbreak_legend_added = False
    for i in range(0, len(outbreak_dates), 2):
        if i + 1 < len(outbreak_dates):
            ax1.fill_between(
                [outbreak_dates.iloc[i], outbreak_dates.iloc[i + 1]],
                0,
                max(dataframe[casetype]),
                color=outbreak_color,
                alpha=0.5,
            )
            if not outbreak_legend_added:
                ax1.fill_between(
                    [], [], color=outbreak_color, alpha=0.3, label="Outbreak"
                )
                outbreak_legend_added = True

    # annotations
    outbreak_periods = outbreak_markers[["start_date", "end_date"]].to_dict("records")

    for period in outbreak_periods:
        period["start_date"] = pd.to_datetime(period["start_date"])
        period["end_date"] = pd.to_datetime(period["end_date"])

    for i, period in enumerate(outbreak_periods):
        start_date = period["start_date"]
        end_date = period["end_date"]
        num_weeks = ((end_date - start_date).days // 7) + 1
        ax1.add_patch(
            Rectangle(
                (start_date, 0),
                end_date - start_date,
                max(dataframe[casetype]),
                linewidth=1,
                edgecolor="none",
                facecolor=major_outbreak_color,
                alpha=0.5,
            )
        )
        mid_date = start_date + (end_date - start_date) / 2
        text = ax1.annotate(
            f"Outbreak {i+1}\n{num_weeks} weeks",
            xy=(mid_date, max(dataframe[casetype]) * 0.9),
            xytext=(mid_date, max(dataframe[casetype]) * 0.95),
            fontsize=10,
            ha="center",
            va="center",
        )
        text.set_path_effects(
            [
                path_effects.Stroke(linewidth=3, foreground="white"),
                path_effects.Normal(),
            ]
        )

    # time
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # title
    plt.title(title)

    # Legend
    fig.tight_layout()
    fig.legend(loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)

    # note
    note_text = "Outbreaks are numbered according to length of weeks"
    ax1.text(0.9, 0.83, note_text, transform=ax1.transAxes, fontsize=6, ha="center")

    plt.show()


def plot_all_climate_var_cases(
    dataframe,
    fig_size,
    disease,
    case_color,
    casetype,
    location,
    outbreak_markers,
    major_outbreak_color,
):
    # Loop over each variable of interest
    for variable_of_interest, variable_label, variable_color in [
        ("pr", "Precipitation", "cadetblue"),
        ("rh", "Relative Humidity", "green"),
        ("solar_rad", "Solar Radiation", "red"),
        ("tave", "Average Temperature", "orange"),
        ("tmax", "Maximum Temperature", "purple"),
        ("tmin", "Minimum Temperature", "brown"),
        ("uv_rad", "UV Radiation", "pink"),
        ("wind_speed", "Wind Speed", "gray"),
    ]:
        # time series decomposition
        decomposition_cases = seasonal_decompose(
            dataframe.set_index("date")[casetype], model="additive", period=12
        )
        decomposition_variable = seasonal_decompose(
            dataframe.set_index("date")[variable_of_interest],
            model="additive",
            period=12,
        )

        fig, ax1 = plt.subplots(figsize=fig_size)
        ax2 = ax1.twinx()

        ax1.plot(
            decomposition_cases.trend.index,
            decomposition_cases.trend,
            label=disease + " Trend",
            color=case_color,
        )
        ax2.plot(
            decomposition_variable.trend.index,
            decomposition_variable.trend,
            label=variable_label + " Trend",
            color=variable_color,
        )

        ax1.set_xlabel("Time")
        ax1.set_ylabel("Trend (" + disease + ")", color=case_color)
        ax2.set_ylabel("Trend (" + variable_label + ")", color=variable_color)

        ax1.tick_params(axis="y", labelcolor=case_color)
        ax2.tick_params(axis="y", labelcolor=variable_color)

        plt.title(location)
        fig.tight_layout()
        plt.grid(True)

        # Add major outbreak periods
        outbreak_periods = outbreak_markers[["start_date", "end_date"]].to_dict(
            "records"
        )
        for period in outbreak_periods:
            period["start_date"] = pd.to_datetime(period["start_date"])
            period["end_date"] = pd.to_datetime(period["end_date"])

        for i, period in enumerate(outbreak_periods):
            start_date = period["start_date"]
            end_date = period["end_date"]
            num_weeks = ((end_date - start_date).days // 7) + 1
            ax1.axvspan(start_date, end_date, facecolor=major_outbreak_color, alpha=0.5)

        plt.show()


def plot_all_clim_subplots(
    dataframe,
    disease,
    case_color,
    casetype,
    location,
    outbreak_markers,
    major_outbreak_color,
):
    # Create a big plot with subplots
    num_rows = 4
    num_cols = 2
    fig, axs = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    # Loop over each variable of interest
    for i, (variable_of_interest, variable_label, variable_color) in enumerate(
        [
            ("pr", "Precipitation", "cadetblue"),
            ("rh", "Relative Humidity", "green"),
            ("solar_rad", "Solar Radiation", "red"),
            ("tave", "Average Temperature", "orange"),
            ("tmax", "Maximum Temperature", "purple"),
            ("tmin", "Minimum Temperature", "brown"),
            ("uv_rad", "UV Radiation", "pink"),
            ("wind_speed", "Wind Speed", "gray"),
        ]
    ):

        # Time series decomposition
        decomposition_cases = seasonal_decompose(
            dataframe.set_index("date")[casetype], model="additive", period=12
        )
        decomposition_variable = seasonal_decompose(
            dataframe.set_index("date")[variable_of_interest],
            model="additive",
            period=12,
        )

        # Get subplot indices
        row_index = i // num_cols
        col_index = i % num_cols

        # Plot trend on separate axes
        ax1 = axs[row_index, col_index]
        ax2 = ax1.twinx()

        ax1.plot(
            decomposition_cases.trend.index,
            decomposition_cases.trend,
            label=disease + " Trend",
            color=case_color,
        )
        ax2.plot(
            decomposition_variable.trend.index,
            decomposition_variable.trend,
            label=variable_label + " Trend",
            color=variable_color,
        )

        ax1.set_xlabel("Time")
        ax1.set_ylabel("Trend (" + disease + ")", color=case_color)
        ax2.set_ylabel("Trend (" + variable_label + ")", color=variable_color)

        ax1.tick_params(axis="y", labelcolor=case_color)
        ax2.tick_params(axis="y", labelcolor=variable_color)

        plt.title(location)
        fig.tight_layout()
        ax1.grid(True)

        # Add major outbreak periods
        outbreak_periods = outbreak_markers[["start_date", "end_date"]].to_dict(
            "records"
        )
        for period in outbreak_periods:
            period["start_date"] = pd.to_datetime(period["start_date"])
            period["end_date"] = pd.to_datetime(period["end_date"])

        for period in outbreak_periods:
            start_date = period["start_date"]
            end_date = period["end_date"]
            ax1.axvspan(start_date, end_date, facecolor=major_outbreak_color, alpha=0.5)

    plt.show()


def agg_munti_socioecon(batch_df):
    # filter pacsii data to muntinlupa
    muntinlupa_pacsii = batch_df[batch_df["adm3_en"] == "City of Muntinlupa"]

    # family members
    variable = "n_family_members"
    muntinlupa_process = muntinlupa_pacsii.reset_index()[["adm4_pcode", variable]]
    muntinlupa_family_members = (
        muntinlupa_process.groupby(["adm4_pcode"]).mean().reset_index()
    )

    # housing materia
    variable = "structure_type"
    muntinlupa_process = muntinlupa_pacsii.reset_index()[["adm4_pcode", variable]]
    muntinlupa_structure = (
        muntinlupa_process.groupby(["adm4_pcode", variable])
        .size()
        .reset_index(name="size")
    )
    muntinlupa_structure[variable] = muntinlupa_structure[variable].replace(
        {
            "Concrete": "material_concrete",
            "Light Materials": "material_light",
            "Semi-concrete/Mixed": "material_mixed",
        }
    )
    muntinlupa_sum = muntinlupa_structure.groupby("adm4_pcode")["size"].transform("sum")
    muntinlupa_structure["percentage"] = (
        muntinlupa_structure["size"] / muntinlupa_sum
    ) * 100
    muntinlupa_structure = muntinlupa_structure.pivot(
        index="adm4_pcode", columns=variable, values="percentage"
    )
    muntinlupa_structure.columns = [
        f"{col}_percentage" for col in muntinlupa_structure.columns
    ]
    muntinlupa_structure.reset_index(inplace=True)

    # water supply type
    variable = "water_supply_type_1"
    muntinlupa_process = muntinlupa_pacsii.reset_index()[["adm4_pcode", variable]]
    muntinlupa_water = (
        muntinlupa_process.groupby(["adm4_pcode", variable])
        .size()
        .reset_index(name="size")
    )
    muntinlupa_water[variable] = muntinlupa_water[variable].replace(
        {
            "Buying out": "water_buyout",
            "Deep Well": "water_deepwell",
            "Maynilad/Nawasa/Formal Connection": "water_formal",
            "Nakiki-igib": "water_igib",
            "Tapping/Informal": "water_informal",
            "Walang Tubig": "water_none",
        }
    )
    muntinlupa_sum = muntinlupa_water.groupby("adm4_pcode")["size"].transform("sum")
    muntinlupa_water["percentage"] = (muntinlupa_water["size"] / muntinlupa_sum) * 100
    muntinlupa_water = muntinlupa_water.pivot(
        index="adm4_pcode", columns=variable, values="percentage"
    )
    muntinlupa_water.columns = [f"{col}_percentage" for col in muntinlupa_water.columns]
    muntinlupa_water.reset_index(inplace=True)

    # merge
    dfs = [muntinlupa_family_members, muntinlupa_structure, muntinlupa_water]
    muntinlupa_socioecon = dfs[0]
    for df in dfs[1:]:
        muntinlupa_socioecon = pd.merge(
            muntinlupa_socioecon, df, on="adm4_pcode", how="left"
        )
    return muntinlupa_socioecon
