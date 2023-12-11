import datetime as dt
from datetime import datetime
from table2ascii import table2ascii as t2a, PresetStyle


def format_users(users):
    output_str = ""
    for idx, user in enumerate(users):
        if idx == len(users) - 1:
            output_str += ", and"
        output_str += f" {user['name']}"
    return output_str


def format_date(date):
    return date.strftime('%m-%d-%Y @%I:%M %p')


def format_time_delta(time):
    new_dt = datetime.strptime(str(time), "%H:%M:%S.%f")
    return new_dt.strftime("%H:%M:%S.%f")


# this function while nearly identical to format_time_delta returns a string truncated of ms
def format_date_time(date):
    new_dt = datetime.strptime(date, "%H:%M:%S.%f")
    return new_dt.strftime("%H:%M:%S")


def calculate_in_game_time(game_data):
    document_running_total = dt.timedelta(0)
    for game in game_data:
        document_running_total += (game["end"] - game["start"])
    return document_running_total


def convert_to_table(header, data):
    return t2a(
        header=header,
        body=data,
        style=PresetStyle.thin_compact
    )
