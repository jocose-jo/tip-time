import datetime


def format_users(users):
    output_str = ""
    for idx, user in enumerate(users):
        if idx == len(users) - 1:
            output_str += ", and"
        output_str += f" <@{user['id']}>"
    return output_str


def format_date(date):
    return date.strftime('%m-%d-%Y @%I:%M %p')


def format_time_delta(time):
    return datetime.datetime.strptime(str(time), "%H:%M:%S.%f")
