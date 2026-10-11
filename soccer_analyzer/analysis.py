def calculate_goal_contributions(goals, assists):
    return goals + assists


def calculate_goals_per_90(goals, minutes):
    if minutes <= 0:
        return 0.0

    return (goals / minutes) * 90


def calculate_assists_per_90(assists, minutes):
    if minutes <= 0:
        return 0.0

    return (assists / minutes) * 90


def calculate_contributions_per_90(
    goal_contributions,
    minutes
):
    if minutes <= 0:
        return 0.0

    return (
        goal_contributions /
        minutes
    ) * 90


def calculate_xg_difference(goals, xg):
    return goals - xg


def calculate_xag_difference(assists, xag):
    return assists - xag


def calculate_scoring_efficiency(goals, xg):
    if xg <= 0:
        return 0.0

    return goals / xg  