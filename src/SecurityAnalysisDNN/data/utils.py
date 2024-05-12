from datetime import timedelta


def find_first_close_date(df1, df2, n_days=10):
    '''Find the first index where the difference is less than n days'''
    # Iterate over each date in the first DataFrame
    for date1 in df1.index:
        # Check against each date in the second DataFrame
        for date2 in df2.index:
            # If the difference is less than n days
            if abs(date1 - date2) < timedelta(days=n_days):
                # Return the later date to ensure we cover the n-day range
                return min(date1, date2)
    return None  # In case no close date is found


def find_last_close_date(df1, df2, n_days=10):
    '''Find the last index where the difference is less than n days'''
    # Iterate over each date in the first DataFrame in reverse
    for date1 in reversed(df1.index):
        # Check against each date in the second DataFrame
        for date2 in reversed(df2.index):
            # If the difference is less than n days
            if abs(date1 - date2) < timedelta(days=n_days):
                # Return the later date to ensure we cover the n-day range
                return max(date1, date2)
    return None  # In case no close date is found


def find_closest_date(target_date, dates):
    '''Find the closest date in the index'''
    # Initialize the minimum difference to a large value and the closest date to None
    min_diff = timedelta(days=10**6)
    closest_date = None

    # Iterate over each date in the index
    for date in dates:
        diff = date - target_date
        if diff < min_diff and diff > timedelta(days=0):
            min_diff = diff
            closest_date = date
    return closest_date
