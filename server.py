# Server.py
# This is where the frontend interact with the backend.

from flask import Flask, request, render_template, session, redirect
import numpy as np
import pandas as pd
import functions
import constants

app = Flask(__name__)

current_dataset = None


@app.route("/", methods=("POST", "GET"))
def index():
    """
    "/" is the main page of the app. Filtering and displaying of data is done
    here.
    """
    global current_dataset
    if request.method == "POST":
        # Get all data from asset dataset.
        dataset = functions.get_dataset_from_csv()

        # Put user inputs in proper datatypes and in a dict.
        sanitize_inputs = functions.sanitize_user_input(request.form)

        # Filtered the dataset with user_inputs.
        filtered_dataset = functions.filter_dataset(
            dataset, sanitize_inputs["start_year"],
            sanitize_inputs["end_year"], sanitize_inputs["industries"],
            sanitize_inputs["start_quarter"], sanitize_inputs["end_quarter"],
            sanitize_inputs["is_range"])

        current_dataset = filtered_dataset
        # Error checking and handling
        if len(sanitize_inputs["industries"]) == 0:
            warning_msg = "Please enter at least one industry"
            return render_template("index.html",
                                   warning=[warning_msg],
                                   export_data="disabled",
                                   data={"start_year": "", "end_year": "",
                                         "start_quarter": "", "end_quarter": "",
                                         "industries": []}
                                   )
        elif current_dataset.empty:
            error_msg = "Year range should be between {0} and {1}!"\
                .format(str(dataset.head(1)["year"].iloc[0]),
                        str(dataset.tail(1)["year"].iloc[0]))
            error_msg1 = "End Quarter should be later than Start Quarter for the same year!"
            return render_template("index.html",
                                   error=[error_msg, error_msg1],
                                   export_data="disabled",
                                   data={"start_year": "", "end_year": "",
                                         "start_quarter": "", "end_quarter": "",
                                         "industries": []}
                                   )
        else:
            # If either start_quarter or end_quarter have value, sort by quarter.
            by_quarter = (sanitize_inputs["start_quarter"] != None or
                          sanitize_inputs["end_quarter"] != None)

            # Get the dataframe of average data for plotting chart.
            avg_data = functions.plot_average_by_year_or_quarter(
                filtered_dataset, by_quarter)

            # Get the dataframe of comparison data for plotting chart.
            comp_data = functions.plot_comparison_data(filtered_dataset)

            # Get list of values needed to plot the average chart from dataframe.
            avg_year, avg_recruitment, avg_resignation, avg_retrenchment, avg_quarter = \
                functions.get_average_plot_values(avg_data)

            # Get list of values needed to plot the average chart from dataframe.
            comp_industry, comp_recruitment, comp_resignation, comp_retrenchment = \
                functions.get_comp_plot_values(comp_data)

            if len(filtered_dataset) != 0:
                highest_recruitment_info = \
                    functions.get_highest_lowest_term(
                        constants.RECRUITMENT, constants.HIGHEST,
                        by_quarter, filtered_dataset)

                highest_retrenchment_info = \
                    functions.get_highest_lowest_term(
                        constants.RETRENCHMENT, constants.HIGHEST,
                        by_quarter, filtered_dataset)

                highest_resignation_info = \
                    functions.get_highest_lowest_term(
                        constants.RESIGNATION, constants.HIGHEST,
                        by_quarter, filtered_dataset)

                lowest_recruitment_info = \
                    functions.get_highest_lowest_term(
                        constants.RECRUITMENT, constants.LOWEST,
                        by_quarter, filtered_dataset)

                lowest_retrenchment_info = \
                    functions.get_highest_lowest_term(
                        constants.RETRENCHMENT, constants.LOWEST,
                        by_quarter, filtered_dataset)

                lowest_resignation_info = \
                    functions.get_highest_lowest_term(
                        constants.RESIGNATION, constants.LOWEST,
                        by_quarter, filtered_dataset)
            else:
                highest_recruitment_info = 0
                highest_retrenchment_info = 0
                highest_resignation_info = 0
                lowest_recruitment_info = 0
                lowest_retrenchment_info = 0
                lowest_resignation_info = 0

            # Google trend.
            payload = functions.build_google_trend_payload(
                sanitize_inputs["start_year"], sanitize_inputs["end_year"],
                sanitize_inputs["start_quarter"], sanitize_inputs["end_quarter"])
            related_topics = functions.get_google_trend_related_topics(payload)
            intrst_ovr_time = functions.get_google_trend_intrst_ovr_time(
                payload, by_quarter)
            intrst_ovr_time_list = list(intrst_ovr_time.values())

            # As data from google trend start from 2004, data before 2004 will be
            # 0.
            while len(intrst_ovr_time_list) < len(avg_retrenchment):
                intrst_ovr_time_list.insert(0, 0)

            # In order for export file to work, a random file name need to
            # be generated for the file.
            # Flask bug with path, path must be passed from html and must be
            # dynamic.
            random_filename = functions.generate_random_csv_filename()

            # Render template with all the data for display.
            return render_template("index.html",
                                   export_data="",
                                   data=request.form.to_dict(flat=False),
                                   column_names=filtered_dataset.columns.values,
                                   row_data=list(
                                       filtered_dataset.values.tolist()),
                                   year=avg_year, quarter=avg_quarter,
                                   avgrecruitment=avg_recruitment,
                                   avgresignation=avg_resignation,
                                   avgretrenchment=avg_retrenchment,
                                   compindustry=comp_industry,
                                   comprecruitment=comp_recruitment,
                                   compresignation=comp_resignation,
                                   compretrenchment=comp_retrenchment,
                                   intrst_ovr_time=intrst_ovr_time_list,
                                   related_topics=", ".join(related_topics),
                                   highest_recruitment_info=highest_recruitment_info,
                                   highest_retrenchment_info=highest_retrenchment_info,
                                   highest_resignation_info=highest_resignation_info,
                                   lowest_recruitment_info=lowest_recruitment_info,
                                   lowest_retrenchment_info=lowest_retrenchment_info,
                                   lowest_resignation_info=lowest_resignation_info,
                                   random_filename=random_filename)
    else:
        return render_template("index.html",
                               export_data="disabled",
                               data={"start_year": "", "end_year": "",
                                     "start_quarter": "", "end_quarter": "",
                                     "industries": []})


@app.route("/events", methods=("POST", "GET"))
def events_index():
    """
    "/events" is the events page of the app. CRUD of events take place here.
    """
    dataset = functions.get_events_dataset_from_csv()
    filtered_dataset = functions.filter_events_dataset(dataset)
    # All data to string.
    stringed_dataset = []
    for row in filtered_dataset.values:
        row = [str(i) for i in row]
        row = ["" if i == "nan" else i for i in row]
        stringed_dataset.append(row)

    return render_template("events/index.html",
                           row_data=stringed_dataset)


@app.route("/submit-email", methods=["POST"])
def submit_email():
    """
    "/submit-email" receive an email address from the form and send it.
    """
    if request.method == "POST":
        receiver_email = request.form["email"]
        try:
            # Try to send the email with the current_dataset.
            email_status = functions.send_email(
                receiver_email, current_dataset)
        except ValueError:
            return "False"

        # If successful, return True, else False.
        if email_status:
            return "True"
        return "False"


@app.route("/download-dataset/<path:filename>", methods=["GET"])
def download_dataset(filename):
    """
    "/download-dataset" download the current_dataset into user computer using
    path as filename.
    """
    # Flask bug with path, path and sendfile must be passed from html and
    # must be dynamic.
    data = functions.download_dataset(filename, current_dataset)
    return data


@app.route("/add-event", methods=["POST"])
def add_event():
    """
     "/add-event" receive events details from the form and write it into
     events csv.
    """
    if request.method == "POST":
        start_year = request.form["startYear"]
        start_quarter = request.form["startQuarter"]
        end_year = request.form["endYear"]
        end_quarter = request.form["endQuarter"]
        event = request.form["event"]
        status = functions.write_events_to_csv(
            start_year, end_year, event, start_quarter, end_quarter)
        return str(status)
    return "False"


@app.route("/review-status", methods=["POST"])
def review_status():
    """
    "/review-status" receive event detail and admin password from the form
    and edit the event if admin password is correct.
    """
    if request.method == "POST":
        action = request.form["action"]
        row_id = request.form["rowId"]
        admin_password = request.form["adminPassword"]
        auth_admin_name = functions.authenticate_admin(admin_password)

        if auth_admin_name == None:
            return "False"
        else:
            status = functions.edit_events_status(
                row_id, auth_admin_name, action)
            return str(status)

    return "False"


if __name__ == "__main__":
    app.run(host="127.0.0.1")
