# This is a function file for server.py.

from pytrends.request import TrendReq, exceptions
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from collections import defaultdict
from flask import send_file
from datetime import date
import numpy as np
import pandas as pd
import sys
import hashlib
import constants
import smtplib
import string
import random
import os
import socket


# Start of CSV Reading Functions
def get_dataset_from_csv():
    """
    Return dataframe of dataset.
    """
    dataset = pd.read_csv("./assets/dataset.csv")
    dataset[["retrenchment"]] = dataset[["retrenchment"]]\
        .replace(to_replace='-', value=0)\
        .apply(pd.to_numeric)

    return dataset


def get_events_dataset_from_csv():
    """
    Return dataframe of dataset.
    """
    return pd.read_csv("./assets/events_dataset.csv")


def get_admins_dataset_from_csv():
    """
    Return dataframe of dataset.
    """
    return pd.read_csv("./assets/admins_dataset.csv")
# End of CSV Reading Functions


# Start of Events Functions
def write_events_to_csv(start_year, end_year, event, start_quarter=None, end_quarter=None):
    """
    Purpose: Get write new events to the datatable and save to csv
    Use Pandas to edit the status column to whichever status was selected by an admin
    Needs:
    - start_year, end_year
    - start_quarter, end_quarter (nullable)
    - event description (limited to 140 characters)
    Returns:
    True - if save was successful
    False - if save was unsuccessful
    """
    dataset = get_events_dataset_from_csv()
    # get new row id
    rowid = int(dataset.tail(1)['id']) + 1

    # create new row with data
    new_row = {'id': rowid, 'start_year': start_year, 'start_quarter': start_quarter, 'end_year': end_year,
               'end_quarter': end_quarter, 'events': event, 'status': 'pending'}

    try:
        # create a new row
        newdf = dataset.append(new_row, ignore_index=True)
        # save it as the original csv file without indexing
        newdf.to_csv('./assets/events_dataset.csv', index=False)
        return True

    except Exception as e:
        print(e)
        return False


def edit_events_status(rowid, name, status):
    """
    Purpose: Get edit the events status in the datatable
    Use Pandas to edit the status column to whichever status was selected by an admin
    Needs:
    - Unfiltered Events dataset
    - rowid of event being reviewed
    - name of admin who reviewed the event
    - status chosen by admin (approved, rejected)
    Returns:
    True - if change was done successfully
    False - if change was unsuccessful
    """
    dataset = get_events_dataset_from_csv()
    reviewedon = date.today().strftime('%d/%m/%Y')
    try:
        # get the location of the row in dataframe from the id
        # and replace the column values accordingly
        dataset.loc[dataset['id'] == int(rowid), ['status']] = status
        dataset.loc[dataset['id'] == int(rowid), ['reviewed on']] = reviewedon
        dataset.loc[dataset['id'] == int(rowid), ['reviewed by']] = name

        # save it as the original csv file without indexing
        dataset.to_csv('./assets/events_dataset.csv', index=False)
        return True

    except Exception as e:
        print(e)
        return False
# End of Events Functions


# Start of Export Data Functions
def export_data_to_file_path(dataset, file_path):
    """
    export dataset into filepath.
    """
    dataset.to_csv(file_path, index=False)


def generate_random_csv_filename():
    """
    generate a csv filename with 7 characters in uppercase.
    """
    return ''.join(random.choices(string.ascii_uppercase +
                                  string.digits, k=7)) + ".csv"


def send_email(receiver_email, dataset):
    """
    Send email with dataset as attachment to receiver_email.
    """
    # Generate random csv filename so that file will be unqiue.
    # Export dataset with filename to a static location.
    try:
        filename = generate_random_csv_filename()
        export_data_to_file_path(
            dataset, constants.EXPORT_DATA_FILE_PATH + filename)

        # Set email details.
        message = MIMEMultipart()
        message["From"] = constants.SENDER_EMAIL
        message["To"] = receiver_email
        message["Subject"] = constants.SUBJECT
        message.attach(MIMEText(constants.BODY, "plain"))

        with open(constants.EXPORT_DATA_FILE_PATH + filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header("Content-Disposition",
                        "attachment; filename=data.csv", )

        # Add attachment to message and convert message to string
        message.attach(part)
        text = message.as_string()

        # Create SMTP session for sending the mail using gmail.
        session = smtplib.SMTP("smtp.gmail.com", 587)
        # Enable security.
        session.starttls()
        # Login with mail_id and password.
        session.login(constants.SENDER_EMAIL, constants.SENDER_PASSWORD)
        # Send email.
        session.sendmail(constants.SENDER_EMAIL, receiver_email, text)
        session.quit()
        os.remove(constants.EXPORT_DATA_FILE_PATH + filename)
        return True
    except socket.gaierror:
        print("socket error")
        return False
    return False


def download_dataset(filename, dataset):
    """
    Export dataset to file_path.
    """
    file_path = constants.EXPORT_DATA_FILE_PATH + filename
    export_data_to_file_path(dataset, file_path)
    return send_file(file_path, attachment_filename="data.csv")
# End of Export Data Functions


# Start of Admin Verification Functions
def authenticate_admin(password):
    """
    Authethic password given with admin dataset. If admin password is
    correct, return the name of the admin.
    """
    hashed = salt_and_hash(password)
    admin_list = get_admins_dataset_from_csv()
    if hashed in list(admin_list["hash_password"]):
        identity = admin_list.loc[(admin_list.hash_password == hashed)]
        identity = list(identity["name"])[0]
    else:
        identity = None
    return identity


def salt_and_hash(password):
    """
    Salt the password in the front, middle and back, hash it with SHA224 and
    returns it.
    """
    split = int(len(password)/2)
    salted = "salted" + password[:split] + \
        "salted" + password[split:] + "salted"
    hashed = hashlib.sha224(str.encode(salted)).hexdigest()
    return hashed
# End of Admin Verification Functions


# Start of Google Trend Functions
def build_google_trend_payload(start_year, end_year, start_quarter,
                               end_quarter):
    """
    Build payload to google trend using start_year, end_year, start_quarter,
    end_quarter.
    """
    keywords = ["economic recession"]
    pytrend = TrendReq()

    if start_quarter == None:
        start_quarter == 1
    if end_quarter == None:
        end_quarter == 1

    start_month = get_corresponding_month_for_quarter(True, start_quarter)
    end_month = get_corresponding_month_for_quarter(True, end_quarter)
    timeframe = ("%s-%s-01 %s-%s-01" %
                 (start_year, start_month, end_year, end_month))

    pytrend.build_payload(
        kw_list=keywords,
        cat=0,
        timeframe=timeframe,
        geo="SG")

    return pytrend


def get_google_trend_related_topics(pytrend):
    """
    Returns a list of related topics of keyword from pytrend.
    """
    try:
        dataset_related_topics = []

        data_related_topics = pytrend.related_topics()
        data_related_topics = data_related_topics["economic recession"]["top"]

        if not data_related_topics.empty:
            data_related_topics = data_related_topics.drop(
                labels=["formattedValue", "hasData", "link", "topic_mid", "topic_type"], axis="columns")
            dataset_related_topics.append(data_related_topics)
            result_related_topics = pd.concat(dataset_related_topics, axis=1)
            return list(result_related_topics["topic_title"].values)
        return []
    except exceptions.ResponseError:
        return []


def get_google_trend_intrst_ovr_time(pytrend, by_quarter):
    """
    Returns dict of interest over time.
    Key - "quarter year"
    Value - number_of_searches
    """
    # Get data of interest over time from google trend.
    try:
        data = pytrend.interest_over_time()

        intrst_ovr_time_dict = {}
        for key in data["economic recession"].keys():
            key_str = str(key)

            year = key_str[0:4]
            quarter = get_corresponding_month_for_quarter(False, key_str[5:7])
            num_of_searches = data["economic recession"][key]

            # Get value by year quarter if by_quarter is True else get data by
            # year.
            if by_quarter:
                year_quarter = year + " " + quarter
                if year_quarter not in intrst_ovr_time_dict:
                    intrst_ovr_time_dict[year_quarter] = [
                        int(num_of_searches), 1]
                else:
                    intrst_ovr_time_dict[year_quarter][0] += int(
                        num_of_searches)
                    intrst_ovr_time_dict[year_quarter][1] += 1
            else:
                if year not in intrst_ovr_time_dict:
                    intrst_ovr_time_dict[year] = [int(num_of_searches), 1]
                else:
                    intrst_ovr_time_dict[year][0] += int(num_of_searches)
                    intrst_ovr_time_dict[year][1] += 1

        # Averaging the number of searches per quarter by dividing
        # total number of searches [0] with total count [1].
        for key in intrst_ovr_time_dict.keys():
            avg_intrst = round(intrst_ovr_time_dict[key][0]
                               / intrst_ovr_time_dict[key][1], 1)
            intrst_ovr_time_dict[key] = avg_intrst

        return intrst_ovr_time_dict
    except exceptions.ResponseError:
        return {}
# End of Google Trend Functions


# Start of TimeFrame Functions
def get_year(start_year, end_year):
    """
    Return list of years in between start_year and end_year.
    """
    start = int(start_year)
    end = int(end_year)
    years = []
    while start <= end:
        years.append(start)
        start += 1
    return years


def get_start_quarters(start_quarter):
    """
    return list of quarters after start_quarter.
    """
    if(start_quarter == "Q1"):
        return ["Q1", "Q2", "Q3", "Q4"]
    elif(start_quarter == "Q2"):
        return ["Q2", "Q3", "Q4"]
    elif(start_quarter == "Q3"):
        return ["Q3", "Q4"]
    elif(start_quarter == "Q4"):
        return ["Q4"]
    else:
        return ["Q1", "Q2", "Q3", "Q4"]


def get_end_quarters(end_quarter):
    """
    return list of quarters before end_quarter.
    """
    if(end_quarter == "Q1"):
        return ["Q1"]
    elif(end_quarter == "Q2"):
        return ["Q1", "Q2"]
    elif(end_quarter == "Q3"):
        return ["Q1", "Q2", "Q3"]
    elif(end_quarter == "Q4"):
        return ["Q1", "Q2", "Q3", "Q4"]
    else:
        return ["Q1", "Q2", "Q3", "Q4"]


def get_corresponding_month_for_quarter(to_month, val):
    """
    Returns the translation between month and quarter.
    """
    if to_month:
        if val == "Q1":
            return "1"
        elif val == "Q2":
            return "4"
        elif val == "Q3":
            return "7"
        else:
            return "10"
    else:
        if int(val) <= 3:
            return "Q1"
        elif int(val) <= 6:
            return "Q2"
        elif int(val) <= 9:
            return "Q3"
        else:
            return "Q4"
# End of TimeFrame Functions


# Start of Chart Data Functions
def plot_average_by_year_or_quarter(filtered_dataset, by_quarter):
    """
    Parameters:
    filtered_dataset - Pandas Dataframe is filtered by inputs.
    by_quarter - Group dataset by year and quarter or year only.
    Returns:
    Pandas Dataframe with columns:
        Year, Industry, Recruitment Rate(%), Resignation Rate(%)
        or
        Year, Quarter, Industry, Recruitment Rate(%), Resignation Rate(%)
    """
    # If group by year and quarter, else group by year only.
    if by_quarter:
        group_list = [filtered_dataset.year, filtered_dataset.quarter]
    else:
        group_list = [filtered_dataset.year]

    grouped_df = filtered_dataset.groupby(group_list, as_index=False).mean()
    return grouped_df.round(1)


def plot_comparison_data(filtered_dataset):
    """
    Purpose: Get data for plotting Comparison Chart
    Parameters:
    filtered_dataset - Pandas Dataframe is filtered by inputs.
    by_quarter - Group dataset by year and quarter or year only.
    Returns:
    Pandas Dataframe with columns:
        Year, Industry, Recruitment Rate(%), Resignation Rate(%)
        or
        Year, Quarter, Indusutry, Recruitment Rate(%), Resignation Rate(%)
    """
    grouped_df = filtered_dataset.groupby(
        [filtered_dataset.industry], as_index=False).mean()
    return grouped_df.round(1).drop(columns=["year"])


def get_comp_plot_values(data):
    """
    Return the lists of data needed to plot comparison bar graph.
    """
    industry_list = data["industry"].tolist()
    recruitment_list = data["recruitment_rate"].tolist()
    resignation_list = data["resignation_rate"].tolist()
    retrenchment_list = data["retrenchment"].tolist()

    return industry_list, recruitment_list, resignation_list, retrenchment_list


def get_average_plot_values(data):
    """
    Return the lists of data needed to plot an average chart.
    """
    year_list = data["year"].tolist()
    recruitment_list = data["recruitment_rate"].tolist()
    resignation_list = data["resignation_rate"].tolist()
    retrenchment_list = data["retrenchment"].tolist()

    # if data is aggregated by quarter, return year, quarter and csv data
    # to template engine.
    if "quarter" in data.columns:
        quarter = "true"
    else:
        quarter = "false"

    return year_list, recruitment_list, resignation_list, retrenchment_list, quarter
# End of Chart Data Functions


# Start of Highest/Lowest Functions
def get_highest_lowest_term(term, high_low, by_quarter, dataset):
    """
    Get the highest or lowest retrenchment, retirement or resignation from
    the dataset.
    Parameters:
    term - retrenchment, retirement or resignation.
    high_low - high or low.
    by_quarter - Group dataset by year and quarter or year only.
    dataset - Dataset to search in.
    Returns:
    Tuple with 2 values:
        Str Value of highest or lowest.
        List of year / year quarter that is with the search.
    """
    data = dataset.replace('-', 0)

    # Create a dictionary based on timeframe term (Year or Year with Quarters)
    data_list_years = list(data["year"])
    data_list_years = [str(x) for x in data_list_years]

    if by_quarter:
        # Create a list containing Year and Quarter combined
        data_list_quarter = list(data["quarter"])
        data_list_time = []
        for i in range(0, len(data_list_years)):
            string = data_list_years[i] + " " + data_list_quarter[i]
            data_list_time.append(string)
        # Create a dictionary with Year+Quarter as key and rates as value
        data_list_search = list(data[term])
        data_list_search = [float(x) for x in data_list_search]
        data_dict = defaultdict(list)
        for a, b in zip(data_list_time, data_list_search):
            data_dict[a].append(b)

    else:
        # Create a dictionary with Year as key and rates as value
        data_list_search = list(data[term])
        data_list_search = [float(x) for x in data_list_search]
        data_dict = defaultdict(list)
        for a, b in zip(data_list_years, data_list_search):
            data_dict[a].append(b)

    # Call search functions, passing relevant data dictionary with timeframe
    if high_low == constants.HIGHEST:
        result = get_highest_term_rate(data_dict, term, by_quarter)
    elif high_low == constants.LOWEST:
        result = get_lowest_term_rate(data_dict, term, by_quarter)
    return result


def get_highest_term_rate(data_dict, term, by_quarter):
    """
    Returns tuple of highest value and list of the keys that have highest value
    from data_dict.
    """
    identified_years_list = []
    # Get the keys and value of the highest average rate.
    if term != constants.RETRENCHMENT:
        average_rates_list = []
        for i in data_dict:
            average_rates_list.append(
                round(sum(data_dict[i]) / len(data_dict[i]), 1))
        identified_years_tuple = [max(average_rates_list)]
        for i in data_dict:
            if round(sum(data_dict[i])/len(data_dict[i]), 1) == max(average_rates_list):
                identified_years_list.append(i)

    # Get the keys and value of the highest average number.
    else:
        total_retrench_list = []
        for i in data_dict:
            total_retrench_list.append(round(sum(data_dict[i]), 1))
        if by_quarter:
            identified_years_tuple = [
                round((max(total_retrench_list)/len(data_dict[i])), 1)]
        else:
            identified_years_tuple = [
                round((max(total_retrench_list)/len(data_dict[i])), 1)]
        for i in data_dict:
            if round(sum(data_dict[i]), 1) == max(total_retrench_list):
                identified_years_list.append(i)
    identified_years_tuple.append(identified_years_list)
    return tuple(identified_years_tuple)


def get_lowest_term_rate(data_dict, term, by_quarter):
    """
    Returns tuple of lowest value and list of the keys that have highest value
    from data_dict.
    """
    identified_years_list = []
    # Obtains lowest average rate in timeframe period (Recruit & Resign)
    if term != constants.RETRENCHMENT:
        average_rates_list = []
        for i in data_dict:
            average_rates_list.append(
                round(sum(data_dict[i])/len(data_dict[i]), 1))
        identified_years_tuple = [min(average_rates_list)]
        for i in data_dict:
            if round(sum(data_dict[i])/len(data_dict[i]), 1) == min(average_rates_list):
                identified_years_list.append(i)
    # Obtains lowest total retrenchments
    else:
        total_retrench_list = []
        for i in data_dict:
            total_retrench_list.append(round(sum(data_dict[i]), 1))
        if by_quarter:
            identified_years_tuple = [
                round((min(total_retrench_list)/len(data_dict[i])), 1)]
        else:
            identified_years_tuple = [
                round((min(total_retrench_list)/len(data_dict[i])), 1)]
        for i in data_dict:
            if round(sum(data_dict[i]), 1) == min(total_retrench_list):
                identified_years_list.append(i)
    identified_years_tuple.append(identified_years_list)
    return tuple(identified_years_tuple)
# End of Highest/Lowest Functions


# Start of Input Sanitization Function
def sanitize_user_input(request_form):
    """
    Take in request form of HTML and bring all the data into a proper dict
    with proper datatype.
    """
    # Convert form to dict
    request_form_dict = request_form.to_dict(flat=False)

    # Take the first item of list as the value of key.
    request_form_dict["start_year"] = request_form_dict["start_year"][0]
    request_form_dict["end_year"] = request_form_dict["end_year"][0]
    request_form_dict["start_quarter"] = request_form_dict["start_quarter"][0]
    request_form_dict["end_quarter"] = request_form_dict["end_quarter"][0]

    if "is_range" in request_form_dict.keys():
        request_form_dict["is_range"] = "N"
    else:
        request_form_dict["is_range"] = "Y"

    # If data is missing, add a empty list or None to the value.
    if "industries" not in request_form_dict:
        request_form_dict["industries"] = []
    if request_form_dict["start_quarter"] == "none":
        request_form_dict["start_quarter"] = None
    if request_form_dict["end_quarter"] == "none":
        request_form_dict["end_quarter"] = None
    return request_form_dict
# End of Input Sanitization Function


# Start of Filtering Functions
def filter_dataset(dataset, start_year, end_year, industries,
                   start_quarter=None, end_quarter=None, is_range="Y"):
    """
    Use pandas to plot the average recruitment by year or quarter and return
    dataframe average ? with year or year/quarter.
    """
    # If start or end year is out of range of dataset, return empty dataframe
    # If start_quarter and end_quarter are both None, filter the dataset
    # by year and industries only.
    # If start_quarter and end_quarter are both None, filter the dataset
    # by year and industries only.
    if int(start_year) < int(dataset.head(1)['year']) or int(end_year) > int(dataset.tail(1)['year']):
        return pd.DataFrame()

    if is_range == "Y":
        if (start_quarter is None and end_quarter is None):
            dataset_out = dataset[
                dataset.year.isin(get_year(start_year, end_year)) &
                dataset.industry.isin(industries)]

        # Else get the remaining quarters filtered by start_quarter
        # and end_quarter.
        else:
            if start_year == end_year:
                dataset_out = dataset[
                    dataset.year.isin([start_year]) &
                    dataset.quarter.isin(list(set(get_start_quarters(start_quarter)) &
                                              set(get_end_quarters(end_quarter)))) &
                    dataset.industry.isin(industries)]
            else:
                # Get dataframe of first year with filtered quarters.
                start_df = dataset[
                    dataset.year.isin([start_year]) &
                    dataset.quarter.isin(get_start_quarters(str(start_quarter))) &
                    dataset.industry.isin(industries)]

                # Get dataframe of last year with filtered quarters.
                end_df = dataset[dataset.year.isin([end_year]) & dataset.quarter.isin(
                    get_end_quarters(str(end_quarter))) &
                    dataset.industry.isin(industries)]

                # Get dataframe of all years from start_year + 1 to end_year - 1.
                mid_df = dataset[
                    dataset.year.isin(get_year(int(start_year) + 1, int(end_year) - 1)) &
                    dataset.industry.isin(industries)]

                # concat all 3 dataframes previously into 1.
                dataset_out = pd.concat([start_df, mid_df, end_df])
    else:
        if (start_quarter is None and end_quarter is None):
            dataset_out = dataset[
                dataset.year.isin([start_year, end_year]) &
                dataset.industry.isin(industries)]

        else:
            # if only one quarter supplied, make both quarters same
            if start_quarter is None:
                start_quarter = end_quarter
            elif end_quarter is None:
                end_quarter = start_quarter

            # making dataframe of first comparison
            start_df = dataset[
                dataset.year.isin([start_year]) &
                dataset.quarter.isin([start_quarter]) &
                dataset.industry.isin(industries)]

            # making dataframe of second comparison
            end_df = dataset[dataset.year.isin([end_year]) & dataset.quarter.isin(
                [end_quarter]) &
                dataset.industry.isin(industries)]

            # combine both dataframes
            dataset_out = pd.concat([start_df, end_df])
    return dataset_out


def filter_events_dataset(dataset):
    """
    Purpose: Get data for events datatable
    Use Pandas to filter out unwanted data based on status colmun
    Rows to display: Status = pending, approved
    Returns:
    Pandas Dataframe with columns:
        start_year, start_quarter, end_year, end_quarter, events, status reviewed on, reviewed by
    """
    search_values = ['approved', 'pending']
    dataset = dataset[
        dataset['status'].str.match('|'.join(search_values))]
    return dataset
# End of Filtering Functions


# Functions for Testing
# def main(start_year, end_year, industries, start_quarter="", end_quarter=""):
#     """
#     This is the main program.
#     """
#     full_dataframe = get_dataset_from_csv()
#     filtered_dataset = filter_dataset(full_dataframe, start_year, end_year, industries,
#                                       start_quarter=None, end_quarter=None)
#     print(plot_comparison_data(filtered_dataset))
#
#
# if __name__ == "__main__":
#     """
#     sys.argv[1]: start_year
#     sys.argv[2]: end_year
#     sys.argv[3]: industries - eg. manufacturing,construction,services
#     sys.argv[4]: start_quarter - leave empty for none(if this is empty, end_quarter must be empty)
#     sys.argv[5]: end_quarter - leave empty for none(if this is empty, start_quarter must be empty)
#
#
#     EXAMPLE CMD LINE RUN:
#     python3 g_function.py 2002 2004 construction,services Q1 Q4
#     """
#     # edit_events_status(4, "Jas", "approved")
#     # start_year = sys.argv[1]
#     # end_year = sys.argv[2]
#     # industries = sys.argv[3].split(",")
#     # try:
#     #     start_quarter = sys.argv[4]
#     #     end_quarter = sys.argv[5]
#     # except:
#     #     start_quarter = ""
#     #     end_quarter = ""
#
#     # main(start_year, end_year, industries, start_quarter, end_quarter)
