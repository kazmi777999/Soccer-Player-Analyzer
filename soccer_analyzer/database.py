import sqlite3
import unicodedata


DATABASE_NAME = "soccer_data.db"


def normalize_text(text):
    text = str(text).lower().strip()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    return text


def create_connection():
    return sqlite3.connect(
        DATABASE_NAME
    )


def create_players_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_players (
            id INTEGER,
            name TEXT,
            age INTEGER,
            team TEXT,
            season INTEGER,
            appearances INTEGER,
            starts INTEGER,
            minutes INTEGER,
            goals INTEGER,
            assists INTEGER,
            PRIMARY KEY (
                id,
                team,
                season
            )
        )
        """
    )


def create_competitions_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_player_competitions (
            player_id INTEGER,
            player_name TEXT,
            age INTEGER,
            team TEXT,
            season INTEGER,
            competition TEXT,
            appearances INTEGER,
            starts INTEGER,
            minutes INTEGER,
            goals INTEGER,
            assists INTEGER,
            PRIMARY KEY (
                player_id,
                team,
                season,
                competition
            )
        )
        """
    )


def create_player_metadata_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_player_metadata (
            player_id INTEGER PRIMARY KEY,
            name TEXT,
            nationality TEXT,
            height TEXT,
            weight TEXT,
            photo TEXT,
            team_id INTEGER,
            team TEXT,
            team_logo TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )




def create_teams_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_teams (
            team_id INTEGER PRIMARY KEY,
            name TEXT,
            country TEXT,
            code TEXT,
            founded INTEGER,
            logo TEXT,
            venue TEXT,
            venue_city TEXT,
            venue_capacity INTEGER,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def create_team_statistics_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_team_statistics (
            team_id INTEGER,
            league_id INTEGER,
            league_name TEXT,
            season INTEGER,
            matches INTEGER,
            wins INTEGER,
            draws INTEGER,
            losses INTEGER,
            goals_for INTEGER,
            goals_against INTEGER,
            clean_sheets INTEGER,
            form TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (team_id, league_id, season)
        )
        """
    )

def players_table_needs_migration(cursor):
    cursor.execute(
        """
        PRAGMA table_info(api_players)
        """
    )

    columns = cursor.fetchall()

    if not columns:
        return False

    primary_keys = []

    for column in columns:
        if column[5] > 0:
            primary_keys.append(
                (
                    column[5],
                    column[1]
                )
            )

    primary_keys.sort()

    primary_key_names = [
        item[1]
        for item in primary_keys
    ]

    expected = [
        "id",
        "team",
        "season"
    ]

    return primary_key_names != expected


def migrate_players_table(
    connection,
    cursor
):
    print("Upgrading player database...")

    cursor.execute(
        """
        ALTER TABLE api_players
        RENAME TO api_players_old
        """
    )

    create_players_table(cursor)

    cursor.execute(
        """
        INSERT OR REPLACE INTO api_players (
            id,
            name,
            age,
            team,
            season,
            appearances,
            starts,
            minutes,
            goals,
            assists
        )
        SELECT
            id,
            name,
            age,
            team,
            season,
            appearances,
            starts,
            minutes,
            goals,
            assists
        FROM api_players_old
        """
    )

    cursor.execute(
        """
        DROP TABLE api_players_old
        """
    )

    connection.commit()

    print("Database upgrade complete.")


def create_tables():
    connection = create_connection()
    cursor = connection.cursor()

    create_players_table(cursor)

    if players_table_needs_migration(cursor):
        migrate_players_table(
            connection,
            cursor
        )

    create_competitions_table(cursor)
    create_player_metadata_table(cursor)
    create_teams_table(cursor)
    create_team_statistics_table(cursor)

    connection.commit()
    connection.close()


def save_player(
    player_id,
    name,
    age,
    team,
    season,
    appearances,
    starts,
    minutes,
    goals,
    assists
):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO api_players (
            id,
            name,
            age,
            team,
            season,
            appearances,
            starts,
            minutes,
            goals,
            assists
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            player_id,
            name,
            age,
            team,
            season,
            appearances,
            starts,
            minutes,
            goals,
            assists
        )
    )

    connection.commit()
    connection.close()


def save_player_competition(
    player_id,
    player_name,
    age,
    team,
    season,
    competition,
    appearances,
    starts,
    minutes,
    goals,
    assists
):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO api_player_competitions (
            player_id,
            player_name,
            age,
            team,
            season,
            competition,
            appearances,
            starts,
            minutes,
            goals,
            assists
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            player_id,
            player_name,
            age,
            team,
            season,
            competition,
            appearances,
            starts,
            minutes,
            goals,
            assists
        )
    )

    connection.commit()
    connection.close()


def save_player_metadata(
    player_id,
    name,
    nationality=None,
    height=None,
    weight=None,
    photo=None,
    team_id=None,
    team=None,
    team_logo=None
):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO api_player_metadata (
            player_id,
            name,
            nationality,
            height,
            weight,
            photo,
            team_id,
            team,
            team_logo,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

        ON CONFLICT(player_id)
        DO UPDATE SET
            name = excluded.name,
            nationality = excluded.nationality,
            height = excluded.height,
            weight = excluded.weight,
            photo = excluded.photo,
            team_id = excluded.team_id,
            team = excluded.team,
            team_logo = excluded.team_logo,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            player_id,
            name,
            nationality,
            height,
            weight,
            photo,
            team_id,
            team,
            team_logo
        )
    )

    connection.commit()
    connection.close()


def get_player_metadata(player_id):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            player_id,
            name,
            nationality,
            height,
            weight,
            photo,
            team_id,
            team,
            team_logo,
            updated_at
        FROM api_player_metadata
        WHERE player_id = ?
        """,
        (player_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "player_id": row[0],
        "name": row[1],
        "nationality": row[2],
        "height": row[3],
        "weight": row[4],
        "photo": row[5],
        "team_id": row[6],
        "team": row[7],
        "team_logo": row[8],
        "updated_at": row[9]
    }


def get_saved_player(
    name,
    team,
    season
):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM api_players
        WHERE season = ?
        """,
        (season,)
    )

    players = cursor.fetchall()

    connection.close()

    search_name = normalize_text(name)
    search_team = normalize_text(team)

    name_parts = search_name.split()

    last_name = ""

    if name_parts:
        last_name = name_parts[-1]

    for player in players:
        saved_name = normalize_text(player[1])
        saved_team = normalize_text(player[3])

        if saved_team != search_team:
            continue

        if saved_name == search_name:
            return player

    for player in players:
        saved_name = normalize_text(player[1])
        saved_team = normalize_text(player[3])

        if saved_team != search_team:
            continue

        if search_name in saved_name:
            return player

    if last_name:
        for player in players:
            saved_name = normalize_text(player[1])
            saved_team = normalize_text(player[3])

            if saved_team != search_team:
                continue

            if last_name in saved_name:
                return player

    return None


def search_saved_players(
    name,
    season=None,
    limit=20
):
    connection = create_connection()
    cursor = connection.cursor()

    if season is None:
        cursor.execute(
            """
            SELECT *
            FROM api_players
            ORDER BY season DESC, goals DESC
            """
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM api_players
            WHERE season = ?
            ORDER BY goals DESC
            """,
            (season,)
        )

    rows = cursor.fetchall()

    connection.close()

    wanted = normalize_text(name)

    matches = []

    for row in rows:
        saved_name = normalize_text(row[1])

        if (
            not wanted
            or saved_name == wanted
            or wanted in saved_name
            or saved_name in wanted
        ):
            matches.append(row)

        if len(matches) >= limit:
            break

    return matches


def get_player_competitions(
    player_id,
    team,
    season
):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM api_player_competitions
        WHERE player_id = ?
        AND season = ?
        ORDER BY competition
        """,
        (
            player_id,
            season
        )
    )

    competitions = cursor.fetchall()

    connection.close()

    search_team = normalize_text(team)

    filtered = []

    for competition in competitions:
        competition_team = normalize_text(
            competition[3]
        )

        if competition_team == search_team:
            filtered.append(competition)

    return filtered


def get_all_saved_players():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM api_players
        ORDER BY season, goals DESC
        """
    )

    players = cursor.fetchall()

    connection.close()

    return players


def get_saved_seasons():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT season
        FROM api_players
        ORDER BY season
        """
    )

    rows = cursor.fetchall()

    connection.close()

    seasons = []

    for row in rows:
        seasons.append(row[0])

    return seasons


def get_players_by_season(season):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM api_players
        WHERE season = ?
        ORDER BY goals DESC
        """,
        (season,)
    )

    players = cursor.fetchall()

    connection.close()

    return players


def get_player_history(name):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM api_players
        ORDER BY season
        """
    )

    players = cursor.fetchall()

    connection.close()

    search_name = normalize_text(name)

    name_parts = search_name.split()

    last_name = ""

    if name_parts:
        last_name = name_parts[-1]

    matches = []

    for player in players:
        saved_name = normalize_text(player[1])

        if saved_name == search_name:
            matches.append(player)

    if matches:
        return matches

    for player in players:
        saved_name = normalize_text(player[1])

        if search_name in saved_name:
            matches.append(player)

    if matches:
        return matches

    if last_name:
        for player in players:
            saved_name = normalize_text(player[1])

            if last_name in saved_name:
                matches.append(player)

    return matches  

def save_team_profile(team):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO api_teams (team_id, name, country, code, founded, logo, venue, venue_city, venue_capacity, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(team_id) DO UPDATE SET
            name=excluded.name, country=excluded.country, code=excluded.code, founded=excluded.founded,
            logo=excluded.logo, venue=excluded.venue, venue_city=excluded.venue_city,
            venue_capacity=excluded.venue_capacity, updated_at=CURRENT_TIMESTAMP
        """,
        (team.get("id"), team.get("name"), team.get("country"), team.get("code"), team.get("founded"),
         team.get("logo"), team.get("venue"), team.get("venue_city"), team.get("venue_capacity"))
    )
    connection.commit()
    connection.close()


def get_saved_team(name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT team_id, name, country, code, founded, logo, venue, venue_city, venue_capacity FROM api_teams")
    rows = cursor.fetchall()
    connection.close()
    wanted = normalize_text(name)
    for row in rows:
        if normalize_text(row[1]) == wanted:
            return {"id":row[0],"name":row[1],"country":row[2],"code":row[3],"founded":row[4],"logo":row[5],"venue":row[6],"venue_city":row[7],"venue_capacity":row[8]}
    for row in rows:
        current = normalize_text(row[1])
        if wanted in current or current in wanted:
            return {"id":row[0],"name":row[1],"country":row[2],"code":row[3],"founded":row[4],"logo":row[5],"venue":row[6],"venue_city":row[7],"venue_capacity":row[8]}
    return None


def save_team_statistics(stats):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO api_team_statistics
        (team_id, league_id, league_name, season, matches, wins, draws, losses, goals_for, goals_against, clean_sheets, form, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (stats.get("team_id"), stats.get("league_id"), stats.get("league_name"), stats.get("season"),
         stats.get("matches"), stats.get("wins"), stats.get("draws"), stats.get("losses"),
         stats.get("goals_for"), stats.get("goals_against"), stats.get("clean_sheets"), stats.get("form"))
    )
    connection.commit()
    connection.close()


def get_saved_team_statistics(team_id, season):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        """SELECT team_id, league_id, league_name, season, matches, wins, draws, losses, goals_for, goals_against, clean_sheets, form
        FROM api_team_statistics WHERE team_id=? AND season=? ORDER BY matches DESC LIMIT 1""",
        (team_id, season)
    )
    row = cursor.fetchone()
    connection.close()
    if not row:
        return None
    keys=["team_id","league_id","league_name","season","matches","wins","draws","losses","goals_for","goals_against","clean_sheets","form"]
    return dict(zip(keys,row))
  