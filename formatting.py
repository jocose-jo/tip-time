import datetime as dt
from datetime import datetime
from table2ascii import table2ascii as t2a, PresetStyle


def format_users(users):
    if len(users) == 0:
        return ""
    if len(users) == 1:
        return users[0]['name']

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


def format_duration(timedelta_obj):
    total_seconds = int(timedelta_obj.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} hr{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return f"{parts[0]} {parts[1]} and {parts[2]}"


def calculate_rdw_reward(total_time):
    hours = total_time.total_seconds() / 3600
    if hours < 3:
        return 250
    elif hours < 4:
        return 200
    else:
        return 100


def format_team_mentions(initiator_mention, selected_users_mentions):
    team_size = len(selected_users_mentions) + 1
    if team_size == 1:
        return initiator_mention
    elif team_size == 2:
        return f"{initiator_mention} and {selected_users_mentions[0]}"
    else:  # team_size == 3
        return f"{initiator_mention}, {selected_users_mentions[0]}, and {selected_users_mentions[1]}"


def format_team_summary(selected_users, initiator_name):
    team_size = len(selected_users) + 1
    if team_size == 1:
        run_type = "👤 Solo Run"
        team_display = f"Team: {initiator_name}"
    elif team_size == 2:
        teammate = selected_users[0].name
        run_type = "👥 Duo Run"
        team_display = f"Team: {initiator_name} + {teammate}"
    else:  # team_size == 3
        teammates = ", ".join([u.name for u in selected_users])
        run_type = "👨‍👩‍👧 Trio Run"
        team_display = f"Team: {initiator_name} + {teammates}"
    return run_type, team_display


def format_bet_summary(bet):
    outcomes_summary = []
    for outcome in bet["outcomes"]:
        wagers = [w for w in bet["bets"] if w["outcome"] == outcome]
        total = sum(w["amount"] for w in wagers)
        bettor_names = ", ".join([w["username"] for w in wagers]) if wagers else "No bets"
        outcomes_summary.append(f"{outcome}: {total} coins ({bettor_names})")
    return "\n".join(outcomes_summary)


def format_run_team(users):
    if len(users) == 0:
        return "👤"
    if len(users) == 1:
        return f"👤 {users[0]['name']}"
    elif len(users) == 2:
        return f"👥 {users[0]['name']} & {users[1]['name']}"
    else:  # 3+ users
        names = ", ".join([u['name'] for u in users[:-1]]) + f", & {users[-1]['name']}"
        return f"👨‍👩‍👧 {names}"
