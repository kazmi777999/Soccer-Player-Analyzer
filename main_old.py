import pandas as pd
import matplotlib.pyplot as plt
import unicodedata

from soccer_analyzer.visualizations import (
    plot_top_scorers,
    plot_top_assists,
    plot_top_contributors,
    plot_top_goals_per_90,
    plot_top_assists_per_90,
    plot_top_contributions_per_90
)

from soccer_analyzer.api import (
    api_get,
    get_live_matches,
    get_player_stats,
    get_team_squad,
    get_player_teams,
    get_player_career_stats
)

from soccer_analyzer.database import (
    create_tables,
    save_player,
    save_player_competition,
    get_saved_player,
    get_player_competitions,
    get_saved_seasons,
    get_players_by_season,
    get_player_history
)


CSV_PATH = "data/players_data_light-2025_2026.csv"
API_SEASON = 2024


def normalize_text(text):
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )


def load_data():
    df = pd.read_csv(
        CSV_PATH,
        usecols=[
            "Player",
            "Nation",
            "Pos",
            "Squad",
            "Comp",
            "Age",
            "MP",
            "Starts",
            "Min",
            "Gls",
            "Ast",
            "G+A",
            "xG",
            "xAG"
        ]
    )

    players = df.rename(
        columns={
            "Player": "name",
            "Nation": "nation",
            "Pos": "position",
            "Squad": "team",
            "Comp": "league",
            "Age": "age",
            "MP": "matches",
            "Starts": "starts",
            "Min": "minutes",
            "Gls": "goals",
            "Ast": "assists",
            "G+A": "goal_contributions",
            "xG": "xg",
            "xAG": "xag"
        }
    ).copy()

    players["minutes"] = players["minutes"].fillna(0)

    players["age"] = (
        players["age"]
        .astype(str)
        .str.split("-")
        .str[0]
    )

    players["age"] = pd.to_numeric(
        players["age"],
        errors="coerce"
    )

    for column in [
        "matches",
        "starts",
        "minutes",
        "goals",
        "assists",
        "goal_contributions",
        "xg",
        "xag"
    ]:
        players[column] = pd.to_numeric(
            players[column],
            errors="coerce"
        ).fillna(0)

    players["goals_per_90"] = 0.0
    players["assists_per_90"] = 0.0
    players["contributions_per_90"] = 0.0

    has_minutes = players["minutes"] > 0

    players.loc[has_minutes, "goals_per_90"] = (
        players.loc[has_minutes, "goals"]
        / players.loc[has_minutes, "minutes"]
        * 90
    )

    players.loc[has_minutes, "assists_per_90"] = (
        players.loc[has_minutes, "assists"]
        / players.loc[has_minutes, "minutes"]
        * 90
    )

    players.loc[has_minutes, "contributions_per_90"] = (
        players.loc[has_minutes, "goal_contributions"]
        / players.loc[has_minutes, "minutes"]
        * 90
    )

    players["xg_difference"] = (
        players["goals"] - players["xg"]
    )

    players["xag_difference"] = (
        players["assists"] - players["xag"]
    )

    return players


def get_csv_data(df):
    if df is None:
        print("\nLoading CSV data...")
        df = load_data()

    return df


def search_player(df, name):
    search_name = normalize_text(name)

    return df[
        df["name"].apply(
            lambda value:
            search_name in normalize_text(value)
        )
    ]


def get_team(df, name):
    search_name = normalize_text(name)

    return df[
        df["team"].apply(
            lambda value:
            search_name in normalize_text(value)
        )
    ]


def get_league(df, name):
    search_name = normalize_text(name)

    return df[
        df["league"].apply(
            lambda value:
            search_name in normalize_text(value)
        )
    ]


def get_position(df, position):
    position = normalize_text(position)

    return df[
        df["position"].apply(
            lambda value:
            position in normalize_text(value)
        )
    ]


def totals_from_api_player(player):
    statistics = player.get("statistics", [])

    appearances = sum(
        item.get("appearances", 0)
        for item in statistics
    )

    starts = sum(
        item.get("starts", 0)
        for item in statistics
    )

    minutes = sum(
        item.get("minutes", 0)
        for item in statistics
    )

    goals = sum(
        item.get("goals", 0)
        for item in statistics
    )

    assists = sum(
        item.get("assists", 0)
        for item in statistics
    )

    goal_contributions = goals + assists

    goals_per_90 = (
        goals / minutes * 90
        if minutes > 0 else 0
    )

    assists_per_90 = (
        assists / minutes * 90
        if minutes > 0 else 0
    )

    contributions_per_90 = (
        goal_contributions / minutes * 90
        if minutes > 0 else 0
    )

    return {
        "appearances": appearances,
        "starts": starts,
        "minutes": minutes,
        "goals": goals,
        "assists": assists,
        "goal_contributions": goal_contributions,
        "goals_per_90": goals_per_90,
        "assists_per_90": assists_per_90,
        "contributions_per_90": contributions_per_90
    }


def save_api_player(player, requested_team):
    totals = totals_from_api_player(player)

    try:
        save_player(
            player["id"],
            player["name"],
            player.get("age"),
            requested_team,
            API_SEASON,
            totals["appearances"],
            totals["starts"],
            totals["minutes"],
            totals["goals"],
            totals["assists"]
        )

        for item in player.get("statistics", []):
            try:
                save_player_competition(
                    player["id"],
                    player["name"],
                    requested_team,
                    API_SEASON,
                    item.get("competition"),
                    item.get("appearances", 0),
                    item.get("starts", 0),
                    item.get("minutes", 0),
                    item.get("goals", 0),
                    item.get("assists", 0)
                )
            except TypeError:
                pass

    except Exception:
        pass


def stored_player_to_api_format(saved, team_name):
    if saved is None:
        return None

    if isinstance(saved, dict):
        name = saved.get("name")
        player_id = saved.get("id")
        age = saved.get("age")
        appearances = saved.get(
            "appearances",
            saved.get("matches", 0)
        )
        starts = saved.get("starts", 0)
        minutes = saved.get("minutes", 0)
        goals = saved.get("goals", 0)
        assists = saved.get("assists", 0)

    else:
        values = list(saved)

        if len(values) < 10:
            return None

        player_id = values[0]
        name = values[1]
        age = values[2]
        appearances = values[-5]
        starts = values[-4]
        minutes = values[-3]
        goals = values[-2]
        assists = values[-1]

    return {
        "id": player_id,
        "name": name,
        "age": age,
        "statistics": [
            {
                "competition": "Saved total",
                "team": team_name,
                "appearances": appearances or 0,
                "starts": starts or 0,
                "minutes": minutes or 0,
                "goals": goals or 0,
                "assists": assists or 0
            }
        ]
    }


def get_player_for_comparison(name, team):
    try:
        saved = get_saved_player(
            name,
            team,
            API_SEASON
        )
    except TypeError:
        try:
            saved = get_saved_player(
                name,
                API_SEASON
            )
        except Exception:
            saved = None
    except Exception:
        saved = None

    if saved is not None:
        player = stored_player_to_api_format(
            saved,
            team
        )

        if player is not None:
            print(
                f"{player['name']} found in database."
            )
            return player

    print(
        f"{name} not found in database."
    )
    print(
        "Getting player data from API..."
    )

    try:
        player = get_player_stats(
            name,
            team
        )

    except Exception as error:
        print(
            f"API error: {error}"
        )
        return None

    if player is None:
        print("Player not found.")
        return None

    save_api_player(
        player,
        team
    )

    print(
        "Player data saved to database."
    )

    return player


def print_api_player(player, team_name):
    totals = totals_from_api_player(
        player
    )

    print(
        f"\n{player.get('name', 'Unknown')}"
    )
    print(
        f"Team: {team_name}"
    )
    print(
        f"Age: {player.get('age', 'Unknown')}"
    )
    print(
        f"Appearances: {totals['appearances']}"
    )
    print(
        f"Starts: {totals['starts']}"
    )
    print(
        f"Minutes: {totals['minutes']}"
    )
    print(
        f"Goals: {totals['goals']}"
    )
    print(
        f"Assists: {totals['assists']}"
    )
    print(
        "Goal Contributions: "
        f"{totals['goal_contributions']}"
    )
    print(
        "Goals per 90: "
        f"{totals['goals_per_90']:.2f}"
    )
    print(
        "Assists per 90: "
        f"{totals['assists_per_90']:.2f}"
    )
    print(
        "Goal Contributions per 90: "
        f"{totals['contributions_per_90']:.2f}"
    )

    if player.get("statistics"):
        print("\nCOMPETITIONS")

        for item in player["statistics"]:
            print(
                f"\n{item.get('competition', 'Unknown')}"
            )
            print(
                "Appearances: "
                f"{item.get('appearances', 0)}"
            )
            print(
                "Starts: "
                f"{item.get('starts', 0)}"
            )
            print(
                "Minutes: "
                f"{item.get('minutes', 0)}"
            )
            print(
                "Goals: "
                f"{item.get('goals', 0)}"
            )
            print(
                "Assists: "
                f"{item.get('assists', 0)}"
            )


def player_analysis(df):
    name = input(
        "\nEnter player name: "
    ).strip()

    result = search_player(
        df,
        name
    )

    if result.empty:
        print(
            "\nPlayer not found in the current dataset."
        )
        return

    print("\nPLAYER STATS\n")

    columns = [
        "name",
        "team",
        "league",
        "position",
        "age",
        "matches",
        "starts",
        "minutes",
        "goals",
        "assists",
        "goal_contributions",
        "goals_per_90",
        "assists_per_90",
        "contributions_per_90",
        "xg",
        "xag"
    ]

    print(
        result[
            columns
        ].round(2).to_string(
            index=False
        )
    )


def compare_players():
    print("\nCOMPARE PLAYERS")

    first_name = input(
        "Enter first player name: "
    ).strip()

    first_team = input(
        "Enter first player's team: "
    ).strip()

    second_name = input(
        "Enter second player name: "
    ).strip()

    second_team = input(
        "Enter second player's team: "
    ).strip()

    player1 = get_player_for_comparison(
        first_name,
        first_team
    )

    if player1 is None:
        return

    player2 = get_player_for_comparison(
        second_name,
        second_team
    )

    if player2 is None:
        return

    print("\nPLAYER COMPARISON")

    print_api_player(
        player1,
        first_team
    )

    print("\n" + "-" * 40)

    print_api_player(
        player2,
        second_team
    )

    totals1 = totals_from_api_player(
        player1
    )

    totals2 = totals_from_api_player(
        player2
    )

    print("\nCOMPARISON SUMMARY")

    if totals1["goals"] > totals2["goals"]:
        print(
            f"More goals: {player1['name']}"
        )
    elif totals2["goals"] > totals1["goals"]:
        print(
            f"More goals: {player2['name']}"
        )
    else:
        print("Goals: Tie")

    if totals1["assists"] > totals2["assists"]:
        print(
            f"More assists: {player1['name']}"
        )
    elif totals2["assists"] > totals1["assists"]:
        print(
            f"More assists: {player2['name']}"
        )
    else:
        print("Assists: Tie")

    if (
        totals1["goal_contributions"]
        >
        totals2["goal_contributions"]
    ):
        print(
            "More goal contributions: "
            f"{player1['name']}"
        )
    elif (
        totals2["goal_contributions"]
        >
        totals1["goal_contributions"]
    ):
        print(
            "More goal contributions: "
            f"{player2['name']}"
        )
    else:
        print(
            "Goal contributions: Tie"
        )

    if (
        totals1["contributions_per_90"]
        >
        totals2["contributions_per_90"]
    ):
        print(
            "Better contributions per 90: "
            f"{player1['name']}"
        )
    elif (
        totals2["contributions_per_90"]
        >
        totals1["contributions_per_90"]
    ):
        print(
            "Better contributions per 90: "
            f"{player2['name']}"
        )
    else:
        print(
            "Contributions per 90: Tie"
        )


def team_analysis_api():
    print("\nTEAM ANALYSIS")

    team_name = input(
        "Enter team name: "
    ).strip()

    try:
        squad = get_team_squad(
            team_name
        )

    except Exception as error:
        print(
            f"API error: {error}"
        )
        return

    if squad is None:
        print("Team not found.")
        return

    players = squad.get(
        "players",
        []
    )

    while True:
        print(
            f"\n{squad.get('team', team_name)}"
        )
        print("1. Full Squad")
        print("2. Goalkeepers")
        print("3. Defenders")
        print("4. Midfielders")
        print("5. Attackers")
        print("6. Return")

        choice = input(
            "\nChoose an option: "
        ).strip()

        if choice == "6":
            break

        position_map = {
            "2": "Goalkeeper",
            "3": "Defender",
            "4": "Midfielder",
            "5": "Attacker"
        }

        if choice == "1":
            selected = players

        elif choice in position_map:
            wanted = position_map[
                choice
            ]

            selected = [
                player
                for player in players
                if normalize_text(
                    player.get(
                        "position",
                        ""
                    )
                )
                ==
                normalize_text(wanted)
            ]

        else:
            print("Invalid option.")
            continue

        if not selected:
            print(
                "No players found."
            )
            continue

        for player in selected:
            print(
                f"{player.get('name', 'Unknown')} "
                f"- {player.get('position', 'Unknown')}"
            )


def compare_teams(df):
    team1_name = input(
        "\nEnter first team: "
    ).strip()

    team2_name = input(
        "Enter second team: "
    ).strip()

    team1 = get_team(
        df,
        team1_name
    )

    team2 = get_team(
        df,
        team2_name
    )

    if team1.empty:
        print(
            "\nFirst team not found."
        )
        return

    if team2.empty:
        print(
            "\nSecond team not found."
        )
        return

    comparison = pd.DataFrame(
        {
            "team": [
                team1["team"].iloc[0],
                team2["team"].iloc[0]
            ],
            "goals": [
                team1["goals"].sum(),
                team2["goals"].sum()
            ],
            "assists": [
                team1["assists"].sum(),
                team2["assists"].sum()
            ],
            "xg": [
                team1["xg"].sum(),
                team2["xg"].sum()
            ],
            "xag": [
                team1["xag"].sum(),
                team2["xag"].sum()
            ]
        }
    )

    print(
        "\nTEAM COMPARISON\n"
    )

    print(
        comparison.round(2).to_string(
            index=False
        )
    )


def league_analysis(df):
    print("\nLEAGUE ANALYSIS")

    league_name = input(
        "Enter league name: "
    ).strip()

    league = get_league(
        df,
        league_name
    )

    if league.empty:
        print("League not found.")
        return

    print("1. Top Scorers")
    print("2. Top Assisters")
    print("3. Top Goal Contributions")
    print("4. Best Goals Per 90")
    print("5. Best Assists Per 90")

    choice = input(
        "\nChoose an option: "
    ).strip()

    if choice == "1":
        result = league.sort_values(
            "goals",
            ascending=False
        ).head(10)

        columns = [
            "name",
            "team",
            "goals"
        ]

    elif choice == "2":
        result = league.sort_values(
            "assists",
            ascending=False
        ).head(10)

        columns = [
            "name",
            "team",
            "assists"
        ]

    elif choice == "3":
        result = league.sort_values(
            "goal_contributions",
            ascending=False
        ).head(10)

        columns = [
            "name",
            "team",
            "goal_contributions"
        ]

    elif choice == "4":
        result = league[
            league["minutes"] >= 450
        ].sort_values(
            "goals_per_90",
            ascending=False
        ).head(10)

        columns = [
            "name",
            "team",
            "goals_per_90"
        ]

    elif choice == "5":
        result = league[
            league["minutes"] >= 450
        ].sort_values(
            "assists_per_90",
            ascending=False
        ).head(10)

        columns = [
            "name",
            "team",
            "assists_per_90"
        ]

    else:
        print("Invalid option.")
        return

    print(
        result[
            columns
        ].round(2).to_string(
            index=False
        )
    )


def compare_leagues(df):
    league1_name = input(
        "\nEnter first league: "
    ).strip()

    league2_name = input(
        "Enter second league: "
    ).strip()

    league1 = get_league(
        df,
        league1_name
    )

    league2 = get_league(
        df,
        league2_name
    )

    if league1.empty or league2.empty:
        print(
            "One or both leagues were not found."
        )
        return

    comparison = pd.DataFrame(
        {
            "league": [
                league1["league"].iloc[0],
                league2["league"].iloc[0]
            ],
            "players": [
                len(league1),
                len(league2)
            ],
            "goals": [
                league1["goals"].sum(),
                league2["goals"].sum()
            ],
            "assists": [
                league1["assists"].sum(),
                league2["assists"].sum()
            ],
            "average_xg": [
                league1["xg"].mean(),
                league2["xg"].mean()
            ],
            "average_xag": [
                league1["xag"].mean(),
                league2["xag"].mean()
            ]
        }
    )

    print(
        "\nLEAGUE COMPARISON\n"
    )

    print(
        comparison.round(2).to_string(
            index=False
        )
    )


def position_analysis(df):
    position = input(
        "\nEnter position "
        "(GK, DF, MF, FW): "
    ).strip()

    result = get_position(
        df,
        position
    )

    if result.empty:
        print(
            "No players found."
        )
        return

    result = result.sort_values(
        "goal_contributions",
        ascending=False
    ).head(20)

    print(
        result[
            [
                "name",
                "team",
                "position",
                "goals",
                "assists",
                "goal_contributions"
            ]
        ].to_string(
            index=False
        )
    )


def player_rankings(df):
    qualified = df[
        df["minutes"] >= 450
    ].copy()

    print("\nPLAYER RANKINGS")
    print("1. Goals")
    print("2. Assists")
    print("3. Goal Contributions")
    print("4. Goals Per 90")
    print("5. Assists Per 90")
    print("6. Contributions Per 90")
    print("7. xG")
    print("8. xAG")
    print("9. Minutes")

    choice = input(
        "\nChoose an option: "
    ).strip()

    ranking_options = {
        "1": ("goals", ["name", "team", "goals"]),
        "2": ("assists", ["name", "team", "assists"]),
        "3": (
            "goal_contributions",
            [
                "name",
                "team",
                "goal_contributions"
            ]
        ),
        "4": (
            "goals_per_90",
            [
                "name",
                "team",
                "goals_per_90"
            ]
        ),
        "5": (
            "assists_per_90",
            [
                "name",
                "team",
                "assists_per_90"
            ]
        ),
        "6": (
            "contributions_per_90",
            [
                "name",
                "team",
                "contributions_per_90"
            ]
        ),
        "7": ("xg", ["name", "team", "xg"]),
        "8": ("xag", ["name", "team", "xag"]),
        "9": (
            "minutes",
            ["name", "team", "minutes"]
        )
    }

    if choice not in ranking_options:
        print("Invalid option.")
        return

    column, display_columns = (
        ranking_options[
            choice
        ]
    )

    source = (
        qualified
        if choice in {
            "4",
            "5",
            "6"
        }
        else df
    )

    result = source.sort_values(
        column,
        ascending=False
    ).head(10)

    print(
        result[
            display_columns
        ].round(2).to_string(
            index=False
        )
    )


def team_rankings(df):
    result = (
        df.groupby("team")
        .agg(
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            xg=("xg", "sum"),
            xag=("xag", "sum")
        )
        .sort_values(
            "goals",
            ascending=False
        )
        .head(20)
    )

    print(
        "\nTEAM RANKINGS\n"
    )

    print(
        result.round(2)
    )


def xg_analysis(df):
    qualified = df[
        df["minutes"] >= 450
    ].copy()

    print("\nXG / XAG ANALYSIS")
    print("1. Biggest xG Overperformers")
    print("2. Biggest xG Underperformers")
    print("3. Biggest xAG Overperformers")
    print("4. Biggest xAG Underperformers")

    choice = input(
        "\nChoose an option: "
    ).strip()

    if choice == "1":
        column = "xg_difference"
        ascending = False
        display = [
            "name",
            "team",
            "goals",
            "xg",
            "xg_difference"
        ]

    elif choice == "2":
        column = "xg_difference"
        ascending = True
        display = [
            "name",
            "team",
            "goals",
            "xg",
            "xg_difference"
        ]

    elif choice == "3":
        column = "xag_difference"
        ascending = False
        display = [
            "name",
            "team",
            "assists",
            "xag",
            "xag_difference"
        ]

    elif choice == "4":
        column = "xag_difference"
        ascending = True
        display = [
            "name",
            "team",
            "assists",
            "xag",
            "xag_difference"
        ]

    else:
        print("Invalid option.")
        return

    result = qualified.sort_values(
        column,
        ascending=ascending
    ).head(10)

    print(
        result[
            display
        ].round(2).to_string(
            index=False
        )
    )


def scoring_efficiency(df):
    qualified = df[
        (
            df["minutes"] >= 450
        )
        &
        (
            df["xg"] > 0
        )
    ].copy()

    qualified["goals_per_xg"] = (
        qualified["goals"]
        /
        qualified["xg"]
    )

    result = qualified.sort_values(
        "goals_per_xg",
        ascending=False
    ).head(10)

    print(
        "\nMOST EFFICIENT SCORERS\n"
    )

    print(
        result[
            [
                "name",
                "team",
                "goals",
                "xg",
                "goals_per_xg"
            ]
        ].round(2).to_string(
            index=False
        )
    )


def young_player_analysis(df):
    max_age = input(
        "\nEnter maximum age: "
    ).strip()

    if not max_age.isdigit():
        print(
            "Please enter a number."
        )
        return

    max_age = int(max_age)

    result = df[
        (
            df["age"] <= max_age
        )
        &
        (
            df["minutes"] >= 450
        )
    ].sort_values(
        "goal_contributions",
        ascending=False
    ).head(20)

    print(
        result[
            [
                "name",
                "age",
                "team",
                "position",
                "goals",
                "assists",
                "goal_contributions"
            ]
        ].to_string(
            index=False
        )
    )


def playing_time_analysis(df):
    print("\nPLAYING TIME")
    print("1. Most Minutes")
    print("2. Most Starts")
    print("3. Most Matches")

    choice = input(
        "\nChoose an option: "
    ).strip()

    options = {
        "1": "minutes",
        "2": "starts",
        "3": "matches"
    }

    if choice not in options:
        print("Invalid option.")
        return

    column = options[
        choice
    ]

    result = df.sort_values(
        column,
        ascending=False
    ).head(20)

    print(
        result[
            [
                "name",
                "team",
                column
            ]
        ].to_string(
            index=False
        )
    )


def advanced_analysis(df):
    print(
        "\nADVANCED ANALYSIS"
    )
    print(
        "1. Goals vs xG Correlation"
    )
    print(
        "2. Assists vs xAG Correlation"
    )
    print(
        "3. Minutes vs Goals Correlation"
    )
    print(
        "4. Average Stats by Position"
    )
    print(
        "5. Average Stats by League"
    )

    choice = input(
        "\nChoose an option: "
    ).strip()

    if choice == "1":
        value = df[
            ["goals", "xg"]
        ].corr().iloc[0, 1]

        print(
            "Goals vs xG correlation:",
            round(value, 3)
        )

    elif choice == "2":
        value = df[
            ["assists", "xag"]
        ].corr().iloc[0, 1]

        print(
            "Assists vs xAG correlation:",
            round(value, 3)
        )

    elif choice == "3":
        value = df[
            ["minutes", "goals"]
        ].corr().iloc[0, 1]

        print(
            "Minutes vs goals correlation:",
            round(value, 3)
        )

    elif choice == "4":
        result = (
            df.groupby("position")[
                [
                    "goals",
                    "assists",
                    "xg",
                    "xag"
                ]
            ]
            .mean()
            .round(2)
        )

        print(result)

    elif choice == "5":
        result = (
            df.groupby("league")[
                [
                    "goals",
                    "assists",
                    "xg",
                    "xag"
                ]
            ]
            .mean()
            .round(2)
        )

        print(result)

    else:
        print("Invalid option.")


def charts(df):
    qualified = df[
        df["minutes"] >= 450
    ].copy()

    print("\nCHARTS")
    print("1. Top Scorers")
    print("2. Top Assisters")
    print("3. Top Goal Contributions")
    print("4. Goals Per 90")
    print("5. Assists Per 90")
    print("6. Contributions Per 90")
    print("7. Goals vs xG Scatter Plot")

    choice = input(
        "\nChoose an option: "
    ).strip()

    if choice == "1":
        result = df.sort_values(
            "goals",
            ascending=False
        ).head(10)

        plot_top_scorers(result)

    elif choice == "2":
        result = df.sort_values(
            "assists",
            ascending=False
        ).head(10)

        plot_top_assists(result)

    elif choice == "3":
        result = df.sort_values(
            "goal_contributions",
            ascending=False
        ).head(10)

        plot_top_contributors(result)

    elif choice == "4":
        result = qualified.sort_values(
            "goals_per_90",
            ascending=False
        ).head(10)

        plot_top_goals_per_90(
            result
        )

    elif choice == "5":
        result = qualified.sort_values(
            "assists_per_90",
            ascending=False
        ).head(10)

        plot_top_assists_per_90(
            result
        )

    elif choice == "6":
        result = qualified.sort_values(
            "contributions_per_90",
            ascending=False
        ).head(10)

        plot_top_contributions_per_90(
            result
        )

    elif choice == "7":
        plt.scatter(
            qualified["xg"],
            qualified["goals"]
        )

        plt.xlabel(
            "Expected Goals (xG)"
        )
        plt.ylabel("Goals")
        plt.title(
            "Goals vs Expected Goals"
        )
        plt.tight_layout()
        plt.show()

    else:
        print("Invalid option.")


def historical_analysis():
    print(
        "\nHISTORICAL ANALYSIS"
    )

    try:
        seasons = get_saved_seasons()

    except Exception as error:
        print(
            f"Database error: {error}"
        )
        return

    if not seasons:
        print(
            "No saved seasons found."
        )
        return

    print("\nSaved seasons:")

    for season in seasons:
        if isinstance(
            season,
            (tuple, list)
        ):
            print(season[0])
        else:
            print(season)

    print(
        "\n1. Players from a saved season"
    )
    print(
        "2. Player history"
    )
    print(
        "3. Return"
    )

    choice = input(
        "\nChoose an option: "
    ).strip()

    if choice == "1":
        season = input(
            "Enter season, for example 2024: "
        ).strip()

        try:
            result = get_players_by_season(
                int(season)
            )

        except Exception as error:
            print(
                f"Database error: {error}"
            )
            return

        for item in result:
            print(item)

    elif choice == "2":
        name = input(
            "Enter player name: "
        ).strip()

        try:
            result = get_player_history(
                name
            )

        except Exception as error:
            print(
                f"Database error: {error}"
            )
            return

        if not result:
            print(
                "No saved history found."
            )
            return

        for item in result:
            print(item)


def data_summary(df):
    print("\nDATA SUMMARY")
    print(
        "Players:",
        len(df)
    )
    print(
        "Teams:",
        df["team"].nunique()
    )
    print(
        "Leagues:",
        df["league"].nunique()
    )
    print(
        "Total goals:",
        int(
            df["goals"].sum()
        )
    )
    print(
        "Total assists:",
        int(
            df["assists"].sum()
        )
    )
    print(
        "Total minutes:",
        int(
            df["minutes"].sum()
        )
    )


def live_matches():
    print("\nLIVE MATCHES")

    try:
        matches = get_live_matches()

    except Exception as error:
        print(
            f"API error: {error}"
        )
        return

    if not matches:
        print(
            "No live matches right now."
        )
        return

    for match in matches:
        fixture = match.get(
            "fixture",
            {}
        )

        teams = match.get(
            "teams",
            {}
        )

        goals = match.get(
            "goals",
            {}
        )

        status = fixture.get(
            "status",
            {}
        )

        home = teams.get(
            "home",
            {}
        ).get(
            "name",
            "Unknown"
        )

        away = teams.get(
            "away",
            {}
        ).get(
            "name",
            "Unknown"
        )

        home_goals = goals.get(
            "home"
        )

        away_goals = goals.get(
            "away"
        )

        elapsed = status.get(
            "elapsed"
        )

        short = status.get(
            "short",
            ""
        )

        match_status = (
            f"{elapsed}'"
            if elapsed is not None
            else short
        )

        print(
            f"{home} "
            f"{home_goals} - "
            f"{away_goals} "
            f"{away} "
            f"({match_status})"
        )


def api_player_analysis():
    print(
        "\nAPI PLAYER ANALYSIS "
        f"({API_SEASON})"
    )

    name = input(
        "Enter player name: "
    ).strip()

    team = input(
        "Enter player's team: "
    ).strip()

    player = get_player_for_comparison(
        name,
        team
    )

    if player is None:
        return

    print_api_player(
        player,
        team
    )



def get_transfer_history(player_id):
    try:
        results = api_get(
            "transfers",
            {
                "player": player_id
            }
        )
    except Exception:
        return []

    transfers = []

    for item in results:
        for transfer in item.get(
            "transfers",
            []
        ):
            teams = transfer.get(
                "teams",
                {}
            )

            old_team = teams.get(
                "out",
                {}
            )

            new_team = teams.get(
                "in",
                {}
            )

            transfers.append(
                {
                    "date": transfer.get(
                        "date"
                    ),
                    "type": transfer.get(
                        "type"
                    ),
                    "from": old_team.get(
                        "name"
                    ),
                    "to": new_team.get(
                        "name"
                    )
                }
            )

    return transfers


def get_player_trophies(player_id):
    try:
        results = api_get(
            "trophies",
            {
                "player": player_id
            }
        )
    except Exception:
        return []

    trophies = []

    for item in results:
        trophies.append(
            {
                "league": item.get(
                    "league"
                ),
                "country": item.get(
                    "country"
                ),
                "season": item.get(
                    "season"
                ),
                "place": item.get(
                    "place"
                )
            }
        )

    return trophies


def complete_player_profile():
    print(
        "\nCOMPLETE PLAYER PROFILE"
    )

    name = input(
        "Enter player name: "
    ).strip()

    team = input(
        "Enter current or known team: "
    ).strip()

    if not name or not team:
        print(
            "Player name and team are required."
        )
        return

    print(
        "\nFinding player..."
    )

    player = get_player_for_comparison(
        name,
        team
    )

    if player is None:
        return

    totals = totals_from_api_player(
        player
    )

    print(
        "\n"
        + "=" * 55
    )
    print(
        "PLAYER PROFILE"
    )
    print(
        "=" * 55
    )

    print(
        "Name:",
        player.get(
            "name",
            name
        )
    )

    print(
        "Age:",
        player.get(
            "age",
            "Unknown"
        )
    )

    print(
        "Player ID:",
        player.get(
            "id",
            "Unknown"
        )
    )

    print(
        "Known Team:",
        team
    )

    print(
        "\n"
        + "=" * 55
    )
    print(
        f"{API_SEASON} SEASON TOTALS"
    )
    print(
        "=" * 55
    )

    print(
        "Appearances:",
        totals[
            "appearances"
        ]
    )

    print(
        "Starts:",
        totals[
            "starts"
        ]
    )

    print(
        "Minutes:",
        totals[
            "minutes"
        ]
    )

    print(
        "Goals:",
        totals[
            "goals"
        ]
    )

    print(
        "Assists:",
        totals[
            "assists"
        ]
    )

    print(
        "Goal Contributions:",
        totals[
            "goal_contributions"
        ]
    )

    print(
        "Goals per 90:",
        round(
            totals[
                "goals_per_90"
            ],
            2
        )
    )

    print(
        "Assists per 90:",
        round(
            totals[
                "assists_per_90"
            ],
            2
        )
    )

    print(
        "Contributions per 90:",
        round(
            totals[
                "contributions_per_90"
            ],
            2
        )
    )

    print(
        "\n"
        + "=" * 55
    )
    print(
        "COMPETITION BREAKDOWN"
    )
    print(
        "=" * 55
    )

    statistics = player.get(
        "statistics",
        []
    )

    if not statistics:
        print(
            "No competition statistics found."
        )

    for item in statistics:
        print(
            "\n"
            + item.get(
                "competition",
                "Unknown"
            )
        )

        print(
            "Team:",
            item.get(
                "team",
                "Unknown"
            )
        )

        print(
            "Appearances:",
            item.get(
                "appearances",
                0
            )
        )

        print(
            "Starts:",
            item.get(
                "starts",
                0
            )
        )

        print(
            "Minutes:",
            item.get(
                "minutes",
                0
            )
        )

        print(
            "Goals:",
            item.get(
                "goals",
                0
            )
        )

        print(
            "Assists:",
            item.get(
                "assists",
                0
            )
        )

    player_id = player.get(
        "id"
    )

    print(
        "\n"
        + "=" * 55
    )
    print(
        "CLUB / TEAM CAREER"
    )
    print(
        "=" * 55
    )

    if player_id is None:
        print(
            "Player ID unavailable."
        )
        return

    try:
        career = get_player_teams(
            player_id
        )

    except Exception as error:
        print(
            "Could not load career history:"
        )
        print(error)
        return

    if not career:
        print(
            "No career history found."
        )
        return

    for club in career:
        club_name = club.get(
            "team",
            "Unknown"
        )

        seasons = club.get(
            "seasons",
            []
        )

        print(
            f"\n{club_name}"
        )

        if seasons:
            print(
                "Seasons:",
                ", ".join(
                    str(season)
                    for season in seasons
                )
            )
        else:
            print(
                "Seasons: Unknown"
            )


    all_clubs = []

    for club in career:
        club_name = club.get(
            "team",
            "Unknown"
        )

        if (
            club_name
            and club_name != "Unknown"
            and club_name not in all_clubs
        ):
            all_clubs.append(
                club_name
            )

    print(
        "\n"
        + "=" * 55
    )
    print(
        "ALL CLUBS PLAYED"
    )
    print(
        "=" * 55
    )

    if all_clubs:
        print(
            " -> ".join(
                all_clubs
            )
        )
    else:
        print(
            "No club history available."
        )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "DETAILED CAREER STATS"
    )
    print(
        "=" * 55
    )

    try:
        career_stats = get_player_career_stats(
            player_id
        )
    except Exception as error:
        print(
            "Could not load detailed career statistics:"
        )
        print(error)
        career_stats = []

    if not career_stats:
        print(
            "No detailed career statistics available."
        )
    else:
        current_season = None
        current_team = None

        for stats in career_stats:
            season = stats.get(
                "season"
            )
            team_name = stats.get(
                "team",
                "Unknown"
            )

            if (
                season != current_season
                or team_name != current_team
            ):
                current_season = season
                current_team = team_name

                print(
                    "\n"
                    + "=" * 50
                )

                if isinstance(
                    season,
                    int
                ):
                    season_label = (
                        f"{season}/"
                        f"{str(season + 1)[-2:]}"
                    )
                else:
                    season_label = str(
                        season
                    )

                print(
                    f"{season_label} - {team_name}"
                )

                print(
                    "=" * 50
                )

            print(
                "\n"
                + stats.get(
                    "competition",
                    "Unknown"
                )
            )

            print(
                "Appearances:",
                stats.get(
                    "appearances",
                    0
                )
            )

            print(
                "Starts:",
                stats.get(
                    "starts",
                    0
                )
            )

            print(
                "Minutes:",
                stats.get(
                    "minutes",
                    0
                )
            )

            print(
                "Goals:",
                stats.get(
                    "goals",
                    0
                )
            )

            print(
                "Assists:",
                stats.get(
                    "assists",
                    0
                )
            )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "BEST PERFORMANCE"
    )
    print(
        "=" * 55
    )

    if not career_stats:
        print(
            "No performance data available."
        )
    else:
        best_performance = max(
            career_stats,
            key=lambda stats: (
                (
                    stats.get(
                        "goals",
                        0
                    )
                    or 0
                )
                + (
                    stats.get(
                        "assists",
                        0
                    )
                    or 0
                ),
                stats.get(
                    "goals",
                    0
                )
                or 0,
                stats.get(
                    "assists",
                    0
                )
                or 0,
                stats.get(
                    "appearances",
                    0
                )
                or 0
            )
        )

        best_season = best_performance.get(
            "season"
        )

        if isinstance(
            best_season,
            int
        ):
            best_season_label = (
                f"{best_season}/"
                f"{str(best_season + 1)[-2:]}"
            )
        else:
            best_season_label = str(
                best_season
            )

        best_goals = (
            best_performance.get(
                "goals",
                0
            )
            or 0
        )

        best_assists = (
            best_performance.get(
                "assists",
                0
            )
            or 0
        )

        best_contributions = (
            best_goals
            + best_assists
        )

        best_minutes = (
            best_performance.get(
                "minutes",
                0
            )
            or 0
        )

        if best_minutes > 0:
            best_contributions_per_90 = (
                best_contributions
                / best_minutes
            ) * 90
        else:
            best_contributions_per_90 = 0

        print(
            "Season:",
            best_season_label
        )
        print(
            "Club/Team:",
            best_performance.get(
                "team",
                "Unknown"
            )
        )
        print(
            "Competition:",
            best_performance.get(
                "competition",
                "Unknown"
            )
        )
        print(
            "Appearances:",
            best_performance.get(
                "appearances",
                0
            )
        )
        print(
            "Goals:",
            best_goals
        )
        print(
            "Assists:",
            best_assists
        )
        print(
            "Goal Contributions:",
            best_contributions
        )
        print(
            "Goal Contributions per 90:",
            round(
                best_contributions_per_90,
                2
            )
        )
        print(
            "Based on the highest goal contributions "
            "in the API-accessible career data."
        )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "CAREER TOTALS BY CLUB"
    )
    print(
        "=" * 55
    )

    if not career_stats:
        print(
            "No club career totals available."
        )
    else:
        club_totals = {}

        for stats in career_stats:
            team_name = stats.get(
                "team",
                "Unknown"
            )

            if team_name not in club_totals:
                club_totals[team_name] = {
                    "appearances": 0,
                    "starts": 0,
                    "minutes": 0,
                    "goals": 0,
                    "assists": 0
                }

            club_totals[team_name]["appearances"] += (
                stats.get(
                    "appearances",
                    0
                )
                or 0
            )

            club_totals[team_name]["starts"] += (
                stats.get(
                    "starts",
                    0
                )
                or 0
            )

            club_totals[team_name]["minutes"] += (
                stats.get(
                    "minutes",
                    0
                )
                or 0
            )

            club_totals[team_name]["goals"] += (
                stats.get(
                    "goals",
                    0
                )
                or 0
            )

            club_totals[team_name]["assists"] += (
                stats.get(
                    "assists",
                    0
                )
                or 0
            )

        for team_name, totals in club_totals.items():
            goal_contributions = (
                totals["goals"]
                + totals["assists"]
            )

            if totals["minutes"] > 0:
                goals_per_90 = (
                    totals["goals"]
                    / totals["minutes"]
                ) * 90

                assists_per_90 = (
                    totals["assists"]
                    / totals["minutes"]
                ) * 90

                contributions_per_90 = (
                    goal_contributions
                    / totals["minutes"]
                ) * 90
            else:
                goals_per_90 = 0
                assists_per_90 = 0
                contributions_per_90 = 0

            print(
                "\n"
                + team_name
            )
            print(
                "-" * len(team_name)
            )
            print(
                "Appearances:",
                totals["appearances"]
            )
            print(
                "Starts:",
                totals["starts"]
            )
            print(
                "Minutes:",
                totals["minutes"]
            )
            print(
                "Goals:",
                totals["goals"]
            )
            print(
                "Assists:",
                totals["assists"]
            )
            print(
                "Goal Contributions:",
                goal_contributions
            )
            print(
                "Goals per 90:",
                round(
                    goals_per_90,
                    2
                )
            )
            print(
                "Assists per 90:",
                round(
                    assists_per_90,
                    2
                )
            )
            print(
                "Goal Contributions per 90:",
                round(
                    contributions_per_90,
                    2
                )
            )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "TRANSFER HISTORY"
    )
    print(
        "=" * 55
    )

    transfers = get_transfer_history(
        player_id
    )

    if not transfers:
        print(
            "No transfer history available."
        )
    else:
        for transfer in transfers:
            print(
                "\nDate:",
                transfer.get(
                    "date"
                )
                or "Unknown"
            )

            print(
                "From:",
                transfer.get(
                    "from"
                )
                or "Unknown"
            )

            print(
                "To:",
                transfer.get(
                    "to"
                )
                or "Unknown"
            )

            print(
                "Type/Fee:",
                transfer.get(
                    "type"
                )
                or "Unknown"
            )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "TROPHIES"
    )
    print(
        "=" * 55
    )

    trophies = get_player_trophies(
        player_id
    )

    if not trophies:
        print(
            "No trophy data available."
        )
    else:
        for trophy in trophies:
            title = trophy.get(
                "league"
            ) or "Unknown competition"

            season = trophy.get(
                "season"
            ) or "Unknown season"

            country = trophy.get(
                "country"
            ) or "Unknown country"

            place = trophy.get(
                "place"
            ) or "Unknown result"

            print(
                f"\n{title}"
            )
            print(
                "Season:",
                season
            )
            print(
                "Country:",
                country
            )
            print(
                "Result:",
                place
            )


    print(
        "\n"
        + "=" * 55
    )
    print(
        "NATIONAL TEAM STATS"
    )
    print(
        "=" * 55
    )

    international_keywords = [
        "world cup",
        "euro",
        "uefa nations league",
        "copa america",
        "africa cup",
        "afcon",
        "asian cup",
        "concacaf",
        "friendlies",
        "friendly",
        "olympics",
        "olympic"
    ]

    national_stats = []

    for stats in career_stats:
        competition_name = str(
            stats.get(
                "competition",
                ""
            )
        ).lower()

        if any(
            keyword in competition_name
            for keyword in international_keywords
        ):
            national_stats.append(
                stats
            )

    if not national_stats:
        print(
            "No national-team statistics found "
            "in the available API seasons."
        )
    else:
        national_totals = {}

        for stats in national_stats:
            team_name = stats.get(
                "team",
                "Unknown"
            )

            if team_name not in national_totals:
                national_totals[team_name] = {
                    "appearances": 0,
                    "starts": 0,
                    "minutes": 0,
                    "goals": 0,
                    "assists": 0
                }

            national_totals[team_name]["appearances"] += (
                stats.get(
                    "appearances",
                    0
                )
                or 0
            )

            national_totals[team_name]["starts"] += (
                stats.get(
                    "starts",
                    0
                )
                or 0
            )

            national_totals[team_name]["minutes"] += (
                stats.get(
                    "minutes",
                    0
                )
                or 0
            )

            national_totals[team_name]["goals"] += (
                stats.get(
                    "goals",
                    0
                )
                or 0
            )

            national_totals[team_name]["assists"] += (
                stats.get(
                    "assists",
                    0
                )
                or 0
            )

        for team_name, totals in national_totals.items():
            goal_contributions = (
                totals["goals"]
                + totals["assists"]
            )

            print(
                "\n"
                + team_name
            )
            print(
                "-" * len(team_name)
            )
            print(
                "Appearances:",
                totals["appearances"]
            )
            print(
                "Starts:",
                totals["starts"]
            )
            print(
                "Minutes:",
                totals["minutes"]
            )
            print(
                "Goals:",
                totals["goals"]
            )
            print(
                "Assists:",
                totals["assists"]
            )
            print(
                "Goal Contributions:",
                goal_contributions
            )

        print(
            "\nInternational competition breakdown:"
        )

        for stats in national_stats:
            season = stats.get(
                "season"
            )

            if isinstance(
                season,
                int
            ):
                season_label = (
                    f"{season}/"
                    f"{str(season + 1)[-2:]}"
                )
            else:
                season_label = str(
                    season
                )

            print(
                "\n"
                + f"{season_label} - "
                + stats.get(
                    "team",
                    "Unknown"
                )
                + " - "
                + stats.get(
                    "competition",
                    "Unknown"
                )
            )
            print(
                "Appearances:",
                stats.get(
                    "appearances",
                    0
                )
            )
            print(
                "Goals:",
                stats.get(
                    "goals",
                    0
                )
            )
            print(
                "Assists:",
                stats.get(
                    "assists",
                    0
                )
            )


def main():
    create_tables()

    df = None

    while True:
        print(
            "\n"
            + "=" * 45
        )
        print(
            "SOCCER DATA ANALYZER"
        )
        print(
            "=" * 45
        )

        print(
            "1. Player Analysis (CSV)"
        )
        print(
            "2. Compare Players (API)"
        )
        print(
            "3. Team Analysis (API)"
        )
        print(
            "4. Compare Teams"
        )
        print(
            "5. League Analysis"
        )
        print(
            "6. Compare Leagues"
        )
        print(
            "7. Position Analysis"
        )
        print(
            "8. Player Rankings"
        )
        print(
            "9. Team Rankings"
        )
        print(
            "10. xG / xAG Analysis"
        )
        print(
            "11. Scoring Efficiency"
        )
        print(
            "12. Young Player Analysis"
        )
        print(
            "13. Playing-Time Analysis"
        )
        print(
            "14. Advanced Data Science"
        )
        print(
            "15. Charts & Visualizations"
        )
        print(
            "16. Historical Analysis"
        )
        print(
            "17. Data Summary"
        )
        print(
            "18. Live Matches"
        )
        print(
            f"19. API Player Analysis ({API_SEASON})"
        )
        print(
            "20. Complete Player Profile"
        )
        print(
            "21. Exit"
        )

        choice = input(
            "\nChoose an option: "
        ).strip()

        if choice == "1":
            df = get_csv_data(df)
            player_analysis(df)

        elif choice == "2":
            compare_players()

        elif choice == "3":
            team_analysis_api()

        elif choice == "4":
            df = get_csv_data(df)
            compare_teams(df)

        elif choice == "5":
            df = get_csv_data(df)
            league_analysis(df)

        elif choice == "6":
            df = get_csv_data(df)
            compare_leagues(df)

        elif choice == "7":
            df = get_csv_data(df)
            position_analysis(df)

        elif choice == "8":
            df = get_csv_data(df)
            player_rankings(df)

        elif choice == "9":
            df = get_csv_data(df)
            team_rankings(df)

        elif choice == "10":
            df = get_csv_data(df)
            xg_analysis(df)

        elif choice == "11":
            df = get_csv_data(df)
            scoring_efficiency(df)

        elif choice == "12":
            df = get_csv_data(df)
            young_player_analysis(df)

        elif choice == "13":
            df = get_csv_data(df)
            playing_time_analysis(df)

        elif choice == "14":
            df = get_csv_data(df)
            advanced_analysis(df)

        elif choice == "15":
            df = get_csv_data(df)
            charts(df)

        elif choice == "16":
            historical_analysis()

        elif choice == "17":
            df = get_csv_data(df)
            data_summary(df)

        elif choice == "18":
            live_matches()

        elif choice == "19":
            api_player_analysis()

        elif choice == "20":
            complete_player_profile()

        elif choice == "21":
            print(
                "\nGoodbye!"
            )
            break

        else:
            print(
                "\nInvalid option. Try again."
            )


if __name__ == "__main__":
    main()
  