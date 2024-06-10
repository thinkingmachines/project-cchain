import os

import pandas as pd

from src.settings import CLIMATE_VARIABLES_LIST, RAW_DIR

CLIMATE_FILES = os.listdir(RAW_DIR / "climate")

# Function for combining individual files
def combine_indiv_files(directory, list_of_filenames):
    """
    Concatenate individual extracted files into one dataframe.

    Args:
     directory: file directory containing individual files
     list_of_filenames
    """
    dfs = []
    for file in list_of_filenames:
        df = pd.read_csv(directory / file)
        dfs.append(df)

    result_df = pd.concat(dfs)
    result_df = result_df.sort_values(by=["date", "ADM4_PCODE"])
    return result_df


def merge_multi_dfs(df_list, merge_on_cols=["date", "ADM4_PCODE"]):
    merged_df = pd.DataFrame()

    # Merge dataframes one by one
    for df in df_list:
        if merged_df.empty:
            merged_df = df
        else:
            # Merge on 'date' and 'adm4_pcode' columns
            merged_df = pd.merge(merged_df, df, on=merge_on_cols, how="outer")

    return merged_df


# Insert "year" column for joining of annual datasets
def add_year(df):
    """
    Insert a year column from the date
    and drop the frequency column.
    """
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop(columns=["freq"])
    df.insert(2, "year", df["date"].dt.year)
    return df


def weighted_average(group, col_name):
    col_without_nan = group[
        col_name
    ].dropna()  # Replace 'your_column' with the column name you want to calculate the weighted average for
    weighted_sum = (
        col_without_nan * group["brgy_total_area"][col_without_nan.index]
    ).sum()
    total_area_sum = group["brgy_total_area"][col_without_nan.index].sum()
    return weighted_sum / total_area_sum


def prep_climate_var_df(climate_var, min_year=2013):
    """
    Adds start of week column from daily date.
    Filters dataframe by year.

    Args:
      climate_var: Climate variable.
      min_year: minimum year to filter the climate dataset to match health data to be used.
    """
    raw_df = [
        filename for filename in CLIMATE_FILES if filename.startswith(climate_var)
    ][0]
    var_df = pd.read_csv(RAW_DIR / "climate" / raw_df)
    var_df["DATE"] = pd.to_datetime(var_df["DATE"])
    # filter date
    var_df = var_df[var_df["DATE"].dt.year >= min_year]
    # add weekly timestamp
    var_df["start_of_week"] = var_df["DATE"] - pd.to_timedelta(
        var_df["DATE"].dt.dayofweek, unit="D"
    )

    # Check if the Monday is from the previous year (December)
    previous_year_mask = var_df["start_of_week"].dt.year < var_df["DATE"].dt.year
    # # Adjust the start of the week to the current year
    var_df.loc[previous_year_mask, "start_of_week"] = pd.to_datetime(
        var_df[previous_year_mask]["DATE"].dt.year, format="%Y"
    )

    return var_df


def align_climate_var(prepped_df, climate_var):
    """
    This function aggregates the climate variable datasets weekly
    and then returns one master dataframe for all the variables.

    Args:
      prepped_df: Climate var df that has start of week and filtered by year.
      climate_var: climate variable columns from raw dataset.
      min_year: minimum year to filter the climate dataset to match health data to be used.
    """

    agg_dict = {
        "AVG": ("mean", "AVG"),
        "MIN": ("min", "MIN"),
        "MAX": ("max", "MAX"),
        "STD": ("std", "STD"),
    }

    result_dict = {}

    for agg_function, column_name in agg_dict.values():
        new_column_name = f"{climate_var}_{column_name}"
        result = prepped_df.groupby(["start_of_week", "ADM4_PCODE"])[climate_var].agg(
            **{new_column_name: agg_function}
        )
        result_dict[new_column_name] = result

    # Combine the results into a single DataFrame
    var_weekly = pd.concat(result_dict.values(), axis=1).reset_index()
    var_weekly[f"{climate_var}_STD"] = var_weekly[f"{climate_var}_STD"].fillna(0)

    return var_weekly


def climate_weighted_avg(climate_var, prepped_df, admin_df, min_year=2013):

    # add brgy area to df
    merged_var_df = prepped_df.merge(
        admin_df[["ADM4_PCODE", "brgy_total_area"]], on="ADM4_PCODE", how="left"
    )
    merged_var_df = merged_var_df.drop_duplicates(subset=["DATE", "ADM4_PCODE"])

    # add weighted average
    merged_var_df = (
        merged_var_df.groupby(["start_of_week", "ADM4_PCODE"])
        .apply(weighted_average, climate_var)
        .rename(f"WEIGHTED_AVG_{climate_var}")
    )
    merged_var_df = merged_var_df.reset_index()

    return merged_var_df


def convert_to_city(
    df,  # to aggregate
    key_columns=["ADM3_PCODE", "ADM4_PCODE", "date", "year", "freq", "Year"],
    agg_list=[
        ("sum", "sum"),
        ("mean", "mean"),
        ("min", "min"),
        ("max", "max"),
        ("std", "std"),
    ],
):

    # Define aggregation functions for each column
    aggregation_functions = {}
    for column in df.columns:
        if column not in key_columns:
            aggregation_functions[
                column
            ] = agg_list  # Include multiple aggregation functions
    key_columns.remove("ADM4_PCODE")
    # Group by key columns and aggregate other columns
    aggregated_df = df.groupby(key_columns).agg(aggregation_functions).reset_index()

    # Flatten MultiIndex column names
    aggregated_df.columns = [
        f"{col[0]}_{col[1]}" if col[1] else col[0] for col in aggregated_df.columns
    ]

    return aggregated_df


def create_outbreak_summary(tagged_df, target_class):
    """
    Args:
     tagged_df: dataframe that contains the outbreak tag
     target_class: class to summarize
    """
    # Create a boolean mask for rows with outbreak_tag = 1
    # tagged_df.sort_values(by=["ADM4_PCODE", "start_of_week"], inplace=True)
    tagged_df.sort_values(by=["Date"], inplace=True)
    outbreak_mask = tagged_df[target_class] == 1

    # Calculate a group ID for each consecutive outbreak period within the same barangay
    outbreak_groups = (outbreak_mask != outbreak_mask.shift(fill_value=False)).cumsum()
    # Add the 'outbreak_groups' column to the DataFrame
    tagged_df["outbreak_group"] = outbreak_groups
    # Filter rows with outbreak_tag = 1
    outbreak_df = tagged_df[outbreak_mask]
    # Group by 'barangay' and 'outbreak_group' and calculate start date, end date, and length
    outbreak_summary = (
        outbreak_df.groupby(["outbreak_group"])  # adm4_pcode
        .agg(
            start_date=("Date", "min"),
            end_date=("Date", "max"),
            actual_length_weeks=(target_class, "count"),
        )
        .reset_index()
    )

    return outbreak_summary
