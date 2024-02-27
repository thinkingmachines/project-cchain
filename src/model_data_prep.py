import os

import pandas as pd

from src.settings import CLIMATE_VARIABLES_LIST, RAW_DIR

CLIMATE_FILES = os.listdir(RAW_DIR / "climate")


def align_climate_var(climate_var, min_year=2013):
    """
    This function aggregates the climate variable datasets weekly
    and then returns one master dataframe for all the variables.

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

    agg_dict = {
        "AVG": ("mean", "AVG"),
        "MIN": ("min", "MIN"),
        "MAX": ("max", "MAX"),
        "STD": ("std", "STD"),
    }

    result_dict = {}

    for agg_function, column_name in agg_dict.values():
        new_column_name = f"{climate_var}_{column_name}"
        result = var_df.groupby(["start_of_week", "ADM4_PCODE"])[climate_var].agg(
            **{new_column_name: agg_function}
        )
        result_dict[new_column_name] = result

    # Combine the results into a single DataFrame
    var_weekly = pd.concat(result_dict.values(), axis=1).reset_index()
    var_weekly[f"{climate_var}_STD"] = var_weekly[f"{climate_var}_STD"].fillna(0)

    return var_weekly


def create_outbreak_summary(tagged_df, target_class):
    """
    Args:
     tagged_df: dataframe that contains the outbreak tag
     target_class: class to summarize
    """
    # Create a boolean mask for rows with outbreak_tag = 1
    # tagged_df.sort_values(by=["ADM4_PCODE", "start_of_week"], inplace=True)
    tagged_df.sort_values(by=["start_of_week"], inplace=True)
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
            start_date=("start_of_week", "min"),
            end_date=("start_of_week", "max"),
            actual_length_weeks=(target_class, "count"),
        )
        .reset_index()
    )

    return outbreak_summary
