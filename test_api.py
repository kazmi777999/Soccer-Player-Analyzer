from soccer_analyzer.api import (
    get_player_stats,
    API_SEASON
)


player = get_player_stats(
    "Bellingham",
    "Real Madrid"
)


if player is None:
    print("Player not found.")

else:
    print("\nPLAYER")
    print("Name:", player["name"])
    print("ID:", player["id"])
    print("Age:", player["age"])

    print(
        f"\n{API_SEASON} "
        "SEASON STATISTICS"
    )

    for stats in player["statistics"]:
        print()

        print(
            "Competition:",
            stats["competition"]
        )

        print(
            "Team:",
            stats["team"]
        )

        print(
            "Appearances:",
            stats["appearances"]
        )

        print(
            "Starts:",
            stats["starts"]
        )

        print(
            "Minutes:",
            stats["minutes"]
        )

        print(
            "Goals:",
            stats["goals"]
        )

        print(
            "Assists:",
            stats["assists"]
        ) 