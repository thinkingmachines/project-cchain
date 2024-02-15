def create_outbreak_summary(tagged_df, target_class):
    """
    Args:
     tagged_df: dataframe that contains the outbreak tag
     target_class: class to summarize
    """
    # Create a boolean mask for rows with outbreak_tag = 1
    tagged_df.sort_values(by=["ADM4_PCODE", "start_of_week"], inplace=True)
    outbreak_mask = tagged_df[target_class] == 1

    # Calculate a group ID for each consecutive outbreak period within the same barangay
    outbreak_groups = (outbreak_mask != outbreak_mask.shift(fill_value=False)).cumsum()
    # Add the 'outbreak_groups' column to the DataFrame
    tagged_df["outbreak_group"] = outbreak_groups
    # Filter rows with outbreak_tag = 1
    outbreak_df = tagged_df[outbreak_mask]
    # Group by 'barangay' and 'outbreak_group' and calculate start date, end date, and length
    outbreak_summary = (
        outbreak_df.groupby(["ADM4_PCODE", "outbreak_group"])
        .agg(
            start_date=("start_of_week", "min"),
            end_date=("start_of_week", "max"),
            actual_length_weeks=(target_class, "count"),
        )
        .reset_index()
    )

    return outbreak_summary
