import matplotlib.pyplot as plt


def plot_top_scorers(df):
    plt.figure()

    plt.bar(
        df["name"],
        df["goals"]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Scorers Overall"
    )

    plt.ylabel("Goals")

    plt.tight_layout()
    plt.show()


def plot_top_assists(df):
    plt.figure()

    plt.bar(
        df["name"],
        df["assists"]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Assists Overall"
    )

    plt.ylabel("Assists")

    plt.tight_layout()
    plt.show()


def plot_top_contributors(df):
    plt.figure()

    plt.bar(
        df["name"],
        df["goal_contributions"]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Goal Contributions"
    )

    plt.ylabel(
        "Goal Contributions"
    )

    plt.tight_layout()
    plt.show()


def plot_top_goals_per_90(df):
    plt.figure()

    plt.bar(
        df["name"],
        df["goals_per_90"]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Goals Per 90"
    )

    plt.ylabel(
        "Goals Per 90"
    )

    plt.tight_layout()
    plt.show()


def plot_top_assists_per_90(df):
    plt.figure()

    plt.bar(
        df["name"],
        df["assists_per_90"]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Assists Per 90"
    )

    plt.ylabel(
        "Assists Per 90"
    )

    plt.tight_layout()
    plt.show()


def plot_top_contributions_per_90(
    df
):
    plt.figure()

    plt.bar(
        df["name"],
        df[
            "contributions_per_90"
        ]
    )

    plt.xticks(
        rotation=45
    )

    plt.title(
        "Top 10 Goal "
        "Contributions Per 90"
    )

    plt.ylabel(
        "Goal Contributions Per 90"
    )

    plt.tight_layout()
    plt.show() 