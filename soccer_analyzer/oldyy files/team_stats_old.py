def calculate_team_goals(df, team):
    team_players = df[df["team"] == team]
    return team_players["goals"].sum()