import unicodedata

import pandas as pd
import streamlit as st

from soccer_analyzer.database import (
    create_tables,
    get_saved_player,
    get_saved_seasons,
    get_players_by_season,
    get_player_history,
    get_player_competitions,
    save_player,
    save_player_competition,
    save_player_metadata,
    get_player_metadata,
    search_saved_players,
    save_team_profile,
    get_saved_team,
    save_team_statistics,
    get_saved_team_statistics
)

from soccer_analyzer.api import (
    API_SEASON,
    get_live_matches,
    get_player_stats,
    search_player_candidates,
    get_player_teams,
    get_player_transfers,
    get_player_trophies,
    get_team_squad,
    get_team_statistics,
    get_player_career_stats
)


st.set_page_config(
    page_title="Soccer Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_tables()


def normalize_text(text):
    text = str(text or "").lower().strip()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )


def safe_number(value, default=0):
    if value is None:
        return float(default)

    try:
        return float(value)

    except (TypeError, ValueError):
        return float(default)


def format_number(value):
    number = safe_number(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.2f}"


def calculate_metrics(player):
    goals = safe_number(
        player.get("goals")
    )

    assists = safe_number(
        player.get("assists")
    )

    appearances = safe_number(
        player.get("appearances")
    )

    starts = safe_number(
        player.get("starts")
    )

    minutes = safe_number(
        player.get("minutes")
    )

    contributions = goals + assists

    if minutes > 0:
        goals_per_90 = (
            goals / minutes
        ) * 90

        assists_per_90 = (
            assists / minutes
        ) * 90

        contributions_per_90 = (
            contributions / minutes
        ) * 90

    else:
        goals_per_90 = 0
        assists_per_90 = 0
        contributions_per_90 = 0

    return {
        "appearances": appearances,
        "starts": starts,
        "minutes": minutes,
        "goals": goals,
        "assists": assists,
        "goal_contributions": contributions,
        "goals_per_90": goals_per_90,
        "assists_per_90": assists_per_90,
        "contributions_per_90": contributions_per_90
    }


def unpack_saved_player(row):
    if row is None:
        return None

    if isinstance(row, dict):
        player = {
            "id": row.get("id"),
            "name": row.get("name", "Unknown"),
            "age": row.get("age"),
            "team": row.get("team", "Unknown"),
            "season": row.get("season"),
            "appearances": row.get("appearances", 0) or 0,
            "starts": row.get("starts", 0) or 0,
            "minutes": row.get("minutes", 0) or 0,
            "goals": row.get("goals", 0) or 0,
            "assists": row.get("assists", 0) or 0
        }

        return enrich_saved_player(player)

    if isinstance(row, (list, tuple)):
        values = list(row)

        if len(values) >= 10:
            player = {
                "id": values[0],
                "name": values[1],
                "age": values[2],
                "team": values[3],
                "season": values[4],
                "appearances": values[5] or 0,
                "starts": values[6] or 0,
                "minutes": values[7] or 0,
                "goals": values[8] or 0,
                "assists": values[9] or 0
            }

            return enrich_saved_player(player)

    return None


def enrich_saved_player(player):
    if not player:
        return player

    try:
        metadata = get_player_metadata(
            player.get("id")
        )

    except Exception:
        metadata = None

    player.setdefault("photo", None)
    player.setdefault("team_logo", None)
    player.setdefault("nationality", None)
    player.setdefault("height", None)
    player.setdefault("weight", None)

    if metadata:
        player["photo"] = metadata.get("photo")
        player["team_logo"] = metadata.get("team_logo")
        player["nationality"] = metadata.get("nationality")
        player["height"] = metadata.get("height")
        player["weight"] = metadata.get("weight")

    return player


def get_available_seasons():
    try:
        seasons = get_saved_seasons()

    except Exception:
        seasons = []

    cleaned = []

    for season in seasons or []:
        if isinstance(season, (list, tuple)):
            if season:
                season = season[0]

        try:
            cleaned.append(int(season))

        except (TypeError, ValueError):
            pass

    cleaned.append(API_SEASON)

    return sorted(
        set(cleaned),
        reverse=True
    )


def load_players_for_season(season):
    try:
        rows = get_players_by_season(
            season
        )

    except Exception:
        rows = []

    players = []

    for row in rows or []:
        player = unpack_saved_player(row)

        if player:
            players.append(player)

    return players


def load_all_saved_players():
    players = []

    for season in get_available_seasons():
        players.extend(
            load_players_for_season(
                season
            )
        )

    return players


def get_history(player_name):
    try:
        rows = get_player_history(
            player_name
        )

    except Exception:
        rows = []

    history = []

    for row in rows or []:
        player = unpack_saved_player(row)

        if player:
            history.append(player)

    return sorted(
        history,
        key=lambda player: (
            safe_number(player.get("season")),
            player.get("team", "")
        )
    )


def save_api_player_to_database(
    player_data,
    season=API_SEASON
):
    if not player_data:
        return []

    statistics = player_data.get(
        "statistics",
        []
    )

    if not statistics:
        return []

    totals_by_team = {}

    for stats in statistics:
        team = stats.get(
            "team",
            "Unknown"
        )

        if not team or team == "Unknown":
            continue

        if team not in totals_by_team:
            totals_by_team[team] = {
                "appearances": 0,
                "starts": 0,
                "minutes": 0,
                "goals": 0,
                "assists": 0,
                "team_id": stats.get("team_id"),
                "team_logo": stats.get("team_logo")
            }

        totals = totals_by_team[team]

        totals["appearances"] += safe_number(
            stats.get("appearances")
        )

        totals["starts"] += safe_number(
            stats.get("starts")
        )

        totals["minutes"] += safe_number(
            stats.get("minutes")
        )

        totals["goals"] += safe_number(
            stats.get("goals")
        )

        totals["assists"] += safe_number(
            stats.get("assists")
        )

        save_player_competition(
            player_data.get("id"),
            player_data.get("name", "Unknown"),
            player_data.get("age"),
            team,
            season,
            stats.get("competition", "Unknown"),
            int(safe_number(stats.get("appearances"))),
            int(safe_number(stats.get("starts"))),
            int(safe_number(stats.get("minutes"))),
            int(safe_number(stats.get("goals"))),
            int(safe_number(stats.get("assists")))
        )

    saved_teams = []

    for team, totals in totals_by_team.items():
        save_player(
            player_data.get("id"),
            player_data.get("name", "Unknown"),
            player_data.get("age"),
            team,
            season,
            int(totals["appearances"]),
            int(totals["starts"]),
            int(totals["minutes"]),
            int(totals["goals"]),
            int(totals["assists"])
        )

        save_player_metadata(
            player_data.get("id"),
            player_data.get("name", "Unknown"),
            player_data.get("nationality"),
            player_data.get("height"),
            player_data.get("weight"),
            player_data.get("photo"),
            totals.get("team_id"),
            team,
            totals.get("team_logo")
        )

        saved_teams.append(team)

    return saved_teams


def fetch_and_cache_player(
    player_name,
    team_name
):
    saved = get_saved_player(
        player_name,
        team_name,
        API_SEASON
    )

    if saved:
        return unpack_saved_player(saved)

    player_data = get_player_stats(
        player_name,
        team_name
    )

    if not player_data:
        return None

    saved_teams = save_api_player_to_database(
        player_data,
        API_SEASON
    )

    saved = get_saved_player(
        player_data.get("name", player_name),
        team_name,
        API_SEASON
    )

    if saved:
        return unpack_saved_player(saved)

    for saved_team in saved_teams:
        saved = get_saved_player(
            player_data.get("name", player_name),
            saved_team,
            API_SEASON
        )

        if saved:
            return unpack_saved_player(saved)

    return None


def api_error_message(error):
    text = str(error)
    lower = text.lower()

    if (
        "limit" in lower
        or "request" in lower
        or "quota" in lower
    ):
        return (
            "API request limit reached. "
            "Your saved SQLite data still works."
        )

    return f"API request failed: {text}"


def api_player_search(
    prefix,
    title="Search Player"
):
    st.subheader(title)

    player_state_key = f"{prefix}_loaded_player"

    c1, c2 = st.columns(2)

    with c1:
        name = st.text_input(
            "Player",
            placeholder="Erling Haaland",
            key=f"{prefix}_name"
        )

    with c2:
        team = st.text_input(
            "Club",
            placeholder="Manchester City",
            key=f"{prefix}_team"
        )

    if st.button(
        "Load Player",
        key=f"{prefix}_button",
        type="primary",
        use_container_width=True
    ):
        if not name.strip():
            st.warning("Enter a player name.")
            return st.session_state.get(player_state_key)

        if not team.strip():
            try:
                candidates = search_player_candidates(name.strip())

                if candidates:
                    st.warning(
                        "Enter the player's club "
                        "to load the correct player."
                    )
                    st.dataframe(
                        [
                            {
                                "Player": item.get("name"),
                                "Nationality": item.get("nationality"),
                                "Age": item.get("age")
                            }
                            for item in candidates[:10]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.error("No matching player found.")

            except Exception as error:
                st.error(api_error_message(error))

            return st.session_state.get(player_state_key)

        try:
            with st.spinner(f"Loading {name}..."):
                player = fetch_and_cache_player(
                    name.strip(),
                    team.strip()
                )

            if player:
                st.session_state[player_state_key] = player
                st.success(
                    f"{player['name']} loaded "
                    "and saved to SQLite."
                )
                return player

            st.error(
                "Player not found. "
                "Check the name and club."
            )

        except Exception as error:
            st.error(api_error_message(error))

    return st.session_state.get(player_state_key)

def render_player_visual(player):
    photo = player.get("photo")

    if photo:
        st.image(
            photo,
            width=180
        )

    else:
        st.markdown(
            """
            <div class="image-placeholder">
                <div class="avatar-icon">
                    👤
                </div>
                <div class="muted">
                    Player photo
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_player_summary(player):
    player = enrich_saved_player(player)
    metrics = calculate_metrics(player)

    left, right = st.columns([1, 3])

    with left:
        render_player_visual(player)

        if player.get("team_logo"):
            st.image(
                player["team_logo"],
                width=65
            )

    with right:
        st.header(player["name"])

        st.write(
            f"⚽ {player['team']}"
        )

        details = []

        for value in [
            player.get("nationality"),
            player.get("height"),
            player.get("weight")
        ]:
            if value:
                details.append(str(value))

        if details:
            st.caption(
                " • ".join(details)
            )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Appearances",
            format_number(
                metrics["appearances"]
            )
        )

        c2.metric(
            "Goals",
            format_number(
                metrics["goals"]
            )
        )

        c3.metric(
            "Assists",
            format_number(
                metrics["assists"]
            )
        )

        c4.metric(
            "G+A",
            format_number(
                metrics["goal_contributions"]
            )
        )

    return metrics


def similarity_score(
    target,
    candidate,
    population
):
    target_metrics = calculate_metrics(
        target
    )

    candidate_metrics = calculate_metrics(
        candidate
    )

    features = [
        "goals_per_90",
        "assists_per_90",
        "contributions_per_90",
        "appearances",
        "minutes"
    ]

    differences = []

    for feature in features:
        values = [
            calculate_metrics(player)[feature]
            for player in population
        ]

        minimum = min(values)
        maximum = max(values)

        if maximum == minimum:
            differences.append(0)
            continue

        target_value = (
            target_metrics[feature] - minimum
        ) / (
            maximum - minimum
        )

        candidate_value = (
            candidate_metrics[feature] - minimum
        ) / (
            maximum - minimum
        )

        differences.append(
            abs(
                target_value - candidate_value
            )
        )

    average = (
        sum(differences)
        / len(differences)
    )

    return round(
        max(
            0,
            (1 - average) * 100
        ),
        1
    )


def build_percentiles(
    player,
    population
):
    target = calculate_metrics(player)

    metrics = {
        "Goals / 90": "goals_per_90",
        "Assists / 90": "assists_per_90",
        "G+A / 90": "contributions_per_90",
        "Goals": "goals",
        "Assists": "assists"
    }

    rows = []

    for label, key in metrics.items():
        values = [
            calculate_metrics(other)[key]
            for other in population
        ]

        if values:
            count = sum(
                1
                for value in values
                if value <= target[key]
            )

            percentile = (
                count
                / len(values)
                * 100
            )

        else:
            percentile = 0

        rows.append(
            {
                "Metric": label,
                "Value": round(
                    target[key],
                    2
                ),
                "Percentile": round(
                    percentile,
                    1
                )
            }
        )

    return rows


def team_summary(
    players,
    team
):
    team_players = [
        player
        for player in players
        if normalize_text(
            player["team"]
        ) == normalize_text(team)
    ]

    goals = 0
    assists = 0
    appearances = 0
    minutes = 0

    for player in team_players:
        metrics = calculate_metrics(player)

        goals += metrics["goals"]
        assists += metrics["assists"]
        appearances += metrics["appearances"]
        minutes += metrics["minutes"]

    return {
        "players": len(team_players),
        "goals": goals,
        "assists": assists,
        "goal_contributions": goals + assists,
        "appearances": appearances,
        "minutes": minutes
    }


def live_match_rows(matches):
    rows = []

    for match in matches:
        fixture = match.get(
            "fixture",
            {}
        )

        league = match.get(
            "league",
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
        ) or {}

        away = teams.get(
            "away",
            {}
        ) or {}

        elapsed = status.get(
            "elapsed"
        )

        status_text = (
            status.get("short")
            or status.get("long")
            or "Live"
        )

        if elapsed is not None:
            status_text = (
                f"{status_text} {elapsed}'"
            )

        rows.append(
            {
                "Competition": league.get(
                    "name",
                    "Unknown"
                ),
                "Home": home.get(
                    "name",
                    "Unknown"
                ),
                "Score": (
                    f"{goals.get('home', 0)}"
                    " - "
                    f"{goals.get('away', 0)}"
                ),
                "Away": away.get(
                    "name",
                    "Unknown"
                ),
                "Status": status_text
            }
        )

    return rows


st.markdown(
    """
    <style>
    .stApp { background:#050505; color:#fff; }
    .block-container { max-width:1500px; padding-top:2rem; padding-bottom:4rem; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#090909; border-right:1px solid #1f1f1f; }
    [data-testid="stSidebar"] * { color:#fff; }
    .main-title { font-size:54px; line-height:1; font-weight:900; letter-spacing:-2px; margin-bottom:10px; color:#fff; }
    .subtitle { color:#9a9a9a; font-size:17px; margin-top:0; margin-bottom:30px; }
    .hero { min-height:570px; border-radius:24px; padding:75px 65px; display:flex; flex-direction:column; justify-content:center; background:radial-gradient(circle at 78% 42%,rgba(234,255,47,.28),transparent 20%),radial-gradient(circle at 85% 55%,rgba(19,105,72,.55),transparent 35%),linear-gradient(110deg,#07120d 0%,#07130e 48%,#0c0c0c 100%); border:1px solid #202020; overflow:hidden; margin-bottom:38px; position:relative; }
    .hero:after { content:"⚽"; position:absolute; right:7%; top:50%; transform:translateY(-50%); font-size:280px; opacity:.18; filter:grayscale(1); }
    .hero-kicker { color:#eaff2f; font-size:14px; font-weight:800; letter-spacing:3px; margin-bottom:20px; }
    .hero-title { font-size:76px; line-height:.95; font-weight:900; letter-spacing:-4px; max-width:800px; margin:0; color:#fff; position:relative; z-index:2; }
    .hero-highlight { color:#eaff2f; }
    .hero-description { max-width:580px; color:#b6b6b6; font-size:18px; line-height:1.6; margin-top:28px; margin-bottom:30px; position:relative; z-index:2; }
    .hero-pill { display:inline-block; width:fit-content; background:#eaff2f; color:#000; padding:15px 28px; border-radius:999px; font-weight:800; position:relative; z-index:2; }
    .section-label { color:#eaff2f; font-size:13px; font-weight:800; letter-spacing:2px; margin-top:12px; }
    .section-title { font-size:36px; font-weight:850; letter-spacing:-1px; margin:5px 0 20px; }
    .feature-card { background:#101010; padding:24px; border:1px solid #242424; border-radius:18px; min-height:155px; transition:.2s ease; }
    .feature-card:hover { border-color:#eaff2f; transform:translateY(-3px); }
    .feature-card h3 { margin:0 0 10px; color:#fff; }
    .feature-card p { color:#9a9a9a; margin:0; line-height:1.5; }
    .image-placeholder { min-height:190px; background:#101010; border:1px solid #242424; border-radius:20px; display:flex; flex-direction:column; justify-content:center; align-items:center; }
    .avatar-icon { font-size:88px; } .muted { color:#8a8a8a; }
    .api-box { padding:15px; background:#101010; border:1px solid #242424; border-radius:12px; margin-bottom:15px; }
    .stButton > button { border-radius:999px; font-weight:700; }
    .stButton > button[kind="primary"] { background:#eaff2f; color:#000; border:none; }
    [data-testid="stMetric"] { background:#101010; border:1px solid #242424; padding:18px; border-radius:16px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.title(
    "⚽ Soccer Analyzer"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Player Profile",
        "Compare Players",
        "Teams",
        "Team Comparison",
        "Rankings",
        "Similar Players",
        "Analytics",
        "Database Explorer",
        "Live Matches"
    ]
)

st.sidebar.divider()

st.sidebar.success(
    "Hybrid Mode\n\n"
    "SQLite + API-Football"
)

st.sidebar.caption(
    "Players are cached automatically "
    "after API searches."
)


if page == "Home":
    players = load_all_saved_players()
    unique_players = {normalize_text(player["name"]) for player in players}
    unique_teams = {normalize_text(player["team"]) for player in players}

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">SOCCER ANALYZER</div>
            <h1 class="hero-title">UNDERSTAND<br>THE <span class="hero-highlight">GAME.</span></h1>
            <div class="hero-description">
                Explore player performance, compare clubs, follow live matches and turn football data into clear insights.
            </div>
            <div class="hero-pill">EXPLORE THE DATA &nbsp; →</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-label">YOUR DATABASE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Football at a glance</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Cached Players", len(unique_players))
    c2.metric("Cached Teams", len(unique_teams))
    c3.metric("Saved Seasons", len(get_available_seasons()))

    st.markdown('<div class="section-label">EXPLORE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Everything you need to analyze the game</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="feature-card"><h3>⚡ Player Intelligence</h3><p>Search players, inspect performance, per-90 metrics, career data, transfers and trophies.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feature-card"><h3>🛡️ Team Analysis</h3><p>Explore squads and compare clubs across wins, goals, clean sheets and season performance.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feature-card"><h3>◉ Live Football</h3><p>Pull current matches from API-Football and keep the analytics experience connected to the game.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Go beyond the scoreboard</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="feature-card"><h3>Player Comparison</h3><p>Put two players side by side and compare production and per-90 performance.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feature-card"><h3>Rankings</h3><p>Rank cached players by goals, assists, contributions, appearances and advanced rates.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feature-card"><h3>Similarity</h3><p>Find players with statistically similar profiles using your growing local database.</p></div>', unsafe_allow_html=True)


elif page == "Player Profile":

    st.markdown(
        '<p class="main-title">'
        'Player Profile'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Search cached players or fetch '
        'new players from API-Football.'
        '</p>',
        unsafe_allow_html=True
    )

    player = api_player_search(
        "profile",
        "Search"
    )

    if player:
        metrics = render_player_summary(
            player
        )

        st.divider()

        tabs = st.tabs(
            [
                "Overview",
                "Competitions",
                "Career",
                "Transfers",
                "Trophies",
                "Analytics"
            ]
        )

        with tabs[0]:
            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Starts",
                format_number(
                    metrics["starts"]
                )
            )

            c2.metric(
                "Minutes",
                format_number(
                    metrics["minutes"]
                )
            )

            c3.metric(
                "Goals / 90",
                f"{metrics['goals_per_90']:.2f}"
            )

            c4.metric(
                "G+A / 90",
                f"{metrics['contributions_per_90']:.2f}"
            )

        with tabs[1]:
            rows = get_player_competitions(
                player["id"],
                player["team"],
                player["season"]
            )

            competitions = []

            for row in rows:
                competitions.append(
                    {
                        "Competition": row[5],
                        "Appearances": row[6] or 0,
                        "Starts": row[7] or 0,
                        "Minutes": row[8] or 0,
                        "Goals": row[9] or 0,
                        "Assists": row[10] or 0
                    }
                )

            if competitions:
                st.dataframe(
                    competitions,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No competition data."
                )

        with tabs[2]:
            career_key = f"career_teams_{player['id']}"

            if st.button(
                "Load Career Teams",
                key=f"load_career_{player['id']}"
            ):
                try:
                    st.session_state[career_key] = get_player_teams(
                        player["id"]
                    )
                except Exception as error:
                    st.error(
                        api_error_message(error)
                    )

            if career_key in st.session_state:
                teams = st.session_state[career_key]

                if teams:
                    rows = []

                    for item in teams:
                        rows.append(
                            {
                                "Team": item.get("team"),
                                "Seasons": ", ".join(
                                    str(season)
                                    for season in item.get(
                                        "seasons",
                                        []
                                    )
                                )
                            }
                        )

                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(
                        "No career teams returned by API-Football."
                    )

            career_stats_key = f"career_stats_{player['id']}"
            if st.button("Load Career Statistics", key=f"load_career_stats_{player['id']}"):
                try:
                    st.session_state[career_stats_key] = get_player_career_stats(player["id"])
                except Exception as error:
                    st.error(api_error_message(error))
            if career_stats_key in st.session_state:
                career_stats = st.session_state[career_stats_key]
                if career_stats:
                    career_rows=[]
                    for item in career_stats:
                        career_rows.append({"Season":item.get("season"),"Teams":", ".join(item.get("teams",[])),"Appearances":item.get("appearances",0),"Starts":item.get("starts",0),"Minutes":item.get("minutes",0),"Goals":item.get("goals",0),"Assists":item.get("assists",0),"G+A":item.get("goal_contributions",0),"G+A / 90":round(item.get("contributions_per_90",0),2)})
                    st.dataframe(career_rows,use_container_width=True,hide_index=True)
                else:
                    st.info("No career statistics returned for the available API seasons.")

        with tabs[3]:
            transfers_key = f"transfers_{player['id']}"

            if st.button(
                "Load Transfers",
                key=f"load_transfers_{player['id']}"
            ):
                try:
                    st.session_state[transfers_key] = get_player_transfers(
                        player["id"]
                    )
                except Exception as error:
                    st.error(
                        api_error_message(error)
                    )

            if transfers_key in st.session_state:
                transfers = st.session_state[transfers_key]

                if transfers:
                    transfer_rows = []

                    for transfer in transfers:
                        transfer_rows.append(
                            {
                                "Date": transfer.get("date"),
                                "From": transfer.get("from_team", transfer.get("from")),
                                "To": transfer.get("to_team", transfer.get("to")),
                                "Type": transfer.get("type")
                            }
                        )

                    st.dataframe(
                        transfer_rows,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(
                        "No transfer history returned by API-Football for this player."
                    )

        with tabs[4]:
            trophies_key = f"trophies_{player['id']}"

            if st.button(
                "Load Trophies",
                key=f"load_trophies_{player['id']}"
            ):
                try:
                    st.session_state[trophies_key] = get_player_trophies(
                        player["id"]
                    )
                except Exception as error:
                    st.error(
                        api_error_message(error)
                    )

            if trophies_key in st.session_state:
                trophies = st.session_state[trophies_key]

                if trophies:
                    trophy_rows = []

                    for trophy in trophies:
                        trophy_rows.append(
                            {
                                "Competition": trophy.get("league"),
                                "Country": trophy.get("country"),
                                "Season": trophy.get("season"),
                                "Result": trophy.get("place")
                            }
                        )

                    st.dataframe(
                        trophy_rows,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(
                        "No trophy history returned by API-Football for this player."
                    )

        with tabs[5]:
            population = load_players_for_season(
                player["season"]
            )

            if population:
                percentiles = build_percentiles(
                    player,
                    population
                )

                st.dataframe(
                    percentiles,
                    use_container_width=True,
                    hide_index=True
                )

                st.bar_chart(
                    pd.DataFrame(
                        percentiles
                    ).set_index(
                        "Metric"
                    )[["Percentile"]]
                )


elif page == "Compare Players":

    st.markdown(
        '<p class="main-title">'
        'Compare Players'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Search any two players. Missing '
        'players are fetched and cached.'
        '</p>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        st.subheader(
            "Player 1"
        )

        p1_name = st.text_input(
            "Player 1 name",
            placeholder="Erling Haaland"
        )

        p1_team = st.text_input(
            "Player 1 club",
            placeholder="Manchester City"
        )

    with right:
        st.subheader(
            "Player 2"
        )

        p2_name = st.text_input(
            "Player 2 name",
            placeholder="Kylian Mbappe"
        )

        p2_team = st.text_input(
            "Player 2 club",
            placeholder="Real Madrid"
        )

    if st.button(
        "Compare Players",
        type="primary",
        use_container_width=True
    ):
        if (
            not p1_name.strip()
            or not p1_team.strip()
            or not p2_name.strip()
            or not p2_team.strip()
        ):
            st.warning(
                "Enter both player names "
                "and both clubs."
            )

        else:
            try:
                with st.spinner(
                    "Loading players..."
                ):
                    player1 = fetch_and_cache_player(
                        p1_name.strip(),
                        p1_team.strip()
                    )

                    player2 = fetch_and_cache_player(
                        p2_name.strip(),
                        p2_team.strip()
                    )

                if not player1:
                    st.error(
                        "Player 1 was not found."
                    )

                elif not player2:
                    st.error(
                        "Player 2 was not found."
                    )

                else:
                    m1 = calculate_metrics(
                        player1
                    )

                    m2 = calculate_metrics(
                        player2
                    )

                    st.divider()

                    c1, c2 = st.columns(2)

                    with c1:
                        render_player_visual(
                            player1
                        )

                        st.header(
                            player1["name"]
                        )

                        st.caption(
                            player1["team"]
                        )

                        st.metric(
                            "Goals",
                            format_number(
                                m1["goals"]
                            )
                        )

                        st.metric(
                            "Assists",
                            format_number(
                                m1["assists"]
                            )
                        )

                        st.metric(
                            "G+A",
                            format_number(
                                m1["goal_contributions"]
                            )
                        )

                        st.metric(
                            "G+A / 90",
                            f"{m1['contributions_per_90']:.2f}"
                        )

                    with c2:
                        render_player_visual(
                            player2
                        )

                        st.header(
                            player2["name"]
                        )

                        st.caption(
                            player2["team"]
                        )

                        st.metric(
                            "Goals",
                            format_number(
                                m2["goals"]
                            )
                        )

                        st.metric(
                            "Assists",
                            format_number(
                                m2["assists"]
                            )
                        )

                        st.metric(
                            "G+A",
                            format_number(
                                m2["goal_contributions"]
                            )
                        )

                        st.metric(
                            "G+A / 90",
                            f"{m2['contributions_per_90']:.2f}"
                        )

                    comparison = pd.DataFrame(
                        {
                            "Metric": [
                                "Appearances",
                                "Minutes",
                                "Goals",
                                "Assists",
                                "G+A",
                                "Goals / 90",
                                "Assists / 90",
                                "G+A / 90"
                            ],
                            player1["name"]: [
                                m1["appearances"],
                                m1["minutes"],
                                m1["goals"],
                                m1["assists"],
                                m1["goal_contributions"],
                                round(
                                    m1["goals_per_90"],
                                    2
                                ),
                                round(
                                    m1["assists_per_90"],
                                    2
                                ),
                                round(
                                    m1["contributions_per_90"],
                                    2
                                )
                            ],
                            player2["name"]: [
                                m2["appearances"],
                                m2["minutes"],
                                m2["goals"],
                                m2["assists"],
                                m2["goal_contributions"],
                                round(
                                    m2["goals_per_90"],
                                    2
                                ),
                                round(
                                    m2["assists_per_90"],
                                    2
                                ),
                                round(
                                    m2["contributions_per_90"],
                                    2
                                )
                            ]
                        }
                    )

                    st.subheader(
                        "Comparison"
                    )

                    st.dataframe(
                        comparison,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.bar_chart(
                        comparison[
                            comparison[
                                "Metric"
                            ].isin(
                                [
                                    "Goals / 90",
                                    "Assists / 90",
                                    "G+A / 90"
                                ]
                            )
                        ].set_index(
                            "Metric"
                        )
                    )

            except Exception as error:
                st.error(
                    api_error_message(error)
                )


elif page == "Teams":

    st.markdown(
        '<p class="main-title">'
        'Teams'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Search a club and load its current '
        'squad directly from API-Football.'
        '</p>',
        unsafe_allow_html=True
    )

    team_name = st.text_input(
        "Club",
        placeholder="Real Madrid"
    )

    if st.button(
        "Search Team",
        type="primary",
        use_container_width=True
    ):
        if not team_name.strip():
            st.warning(
                "Enter a club name."
            )

        else:
            try:
                with st.spinner(
                    "Loading squad..."
                ):
                    squad = get_team_squad(
                        team_name.strip()
                    )

                if not squad:
                    st.error(
                        "Team or squad "
                        "was not found."
                    )

                else:
                    st.header(
                        team_name
                    )

                    st.metric(
                        "Squad Players",
                        len(squad)
                    )

                    rows = []

                    for player in squad:
                        rows.append(
                            {
                                "Player": player.get("name"),
                                "Age": player.get("age"),
                                "Number": player.get("number"),
                                "Position": player.get("position")
                            }
                        )

                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.info(
                        "To add one of these "
                        "players to your analytics "
                        "database, search that player "
                        "in Player Profile."
                    )

            except Exception as error:
                st.error(
                    api_error_message(error)
                )


elif page == "Team Comparison":

    st.markdown('<p class="main-title">Team Comparison</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Compare real team season statistics with SQLite caching.</p>', unsafe_allow_html=True)

    season = st.selectbox("Season", get_available_seasons())
    c1, c2 = st.columns(2)
    with c1:
        team1 = st.text_input("Team 1", placeholder="Real Madrid")
    with c2:
        team2 = st.text_input("Team 2", placeholder="Bayern Munich")

    def load_team_comparison_data(name, selected_season):
        saved_team = get_saved_team(name)
        if saved_team:
            saved_stats = get_saved_team_statistics(saved_team["id"], selected_season)
            if saved_stats:
                return {**saved_team, **saved_stats}
        fresh = get_team_statistics(name, selected_season)
        if not fresh:
            return None
        save_team_profile(fresh)
        save_team_statistics(fresh)
        return fresh

    if st.button("Compare Teams", type="primary", use_container_width=True):
        if not team1.strip() or not team2.strip():
            st.warning("Enter both team names.")
        else:
            try:
                with st.spinner("Loading team statistics..."):
                    t1 = load_team_comparison_data(team1.strip(), season)
                    t2 = load_team_comparison_data(team2.strip(), season)
                if not t1 or not t2:
                    st.error("Team statistics were not available for one or both clubs for this season.")
                else:
                    left, right = st.columns(2)
                    for column, team in [(left,t1),(right,t2)]:
                        with column:
                            if team.get("logo"):
                                st.image(team["logo"], width=90)
                            st.header(team.get("name"))
                            st.caption(f"{team.get('league_name','')} • {team.get('season')}")
                            a,b,c=st.columns(3)
                            a.metric("Wins",team.get("wins",0)); b.metric("Draws",team.get("draws",0)); c.metric("Losses",team.get("losses",0))
                            a,b,c=st.columns(3)
                            a.metric("Matches",team.get("matches",0)); b.metric("Goals For",team.get("goals_for",0)); c.metric("Goals Against",team.get("goals_against",0))
                            st.metric("Goal Difference",(team.get("goals_for",0) or 0)-(team.get("goals_against",0) or 0))
                            st.metric("Clean Sheets",team.get("clean_sheets",0))
                            if team.get("form"):
                                st.caption(f"Form: {team['form']}")
                    rows=[]
                    for label,key in [("Matches","matches"),("Wins","wins"),("Draws","draws"),("Losses","losses"),("Goals For","goals_for"),("Goals Against","goals_against"),("Clean Sheets","clean_sheets")]:
                        rows.append({"Metric":label,t1["name"]:t1.get(key,0),t2["name"]:t2.get(key,0)})
                    comparison=pd.DataFrame(rows)
                    st.subheader("Season Comparison")
                    st.dataframe(comparison,use_container_width=True,hide_index=True)
                    st.bar_chart(comparison.set_index("Metric"))
            except Exception as error:
                st.error(api_error_message(error))


elif page == "Rankings":

    st.markdown(
        '<p class="main-title">'
        'Player Rankings'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Rank every player currently cached '
        'in your analytics database.'
        '</p>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:
        season = st.selectbox(
            "Season",
            get_available_seasons()
        )

    with c2:
        metric = st.selectbox(
            "Rank by",
            [
                "Goals",
                "Assists",
                "Goal Contributions",
                "Goals / 90",
                "Assists / 90",
                "G+A / 90",
                "Appearances",
                "Minutes"
            ]
        )

    players = load_players_for_season(
        season
    )

    rows = []

    for player in players:
        stats = calculate_metrics(
            player
        )

        rows.append(
            {
                "Player": player["name"],
                "Team": player["team"],
                "Age": player["age"],
                "Appearances": stats["appearances"],
                "Minutes": stats["minutes"],
                "Goals": stats["goals"],
                "Assists": stats["assists"],
                "Goal Contributions": stats["goal_contributions"],
                "Goals / 90": round(
                    stats["goals_per_90"],
                    2
                ),
                "Assists / 90": round(
                    stats["assists_per_90"],
                    2
                ),
                "G+A / 90": round(
                    stats["contributions_per_90"],
                    2
                )
            }
        )

    rows = sorted(
        rows,
        key=lambda row: safe_number(
            row.get(metric)
        ),
        reverse=True
    )

    for index, row in enumerate(
        rows,
        start=1
    ):
        row["Rank"] = index

    if not rows:
        st.info(
            "No cached players yet."
        )

    else:
        st.caption(
            f"{len(rows)} cached player-team "
            "records are included."
        )

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

        top = rows[:10]

        chart = pd.DataFrame(
            {
                "Player": [
                    row["Player"]
                    for row in top
                ],
                metric: [
                    row[metric]
                    for row in top
                ]
            }
        ).set_index(
            "Player"
        )

        st.subheader(
            f"Top 10 — {metric}"
        )

        st.bar_chart(chart)


elif page == "Similar Players":

    st.markdown(
        '<p class="main-title">'
        'Similar Players'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Search a player, cache them if '
        'necessary, then compare against '
        'your player database.'
        '</p>',
        unsafe_allow_html=True
    )

    target = api_player_search(
        "similar",
        "Target Player"
    )

    if target:
        players = load_players_for_season(
            target["season"]
        )

        if len(players) < 2:
            st.info(
                "Add more players to the "
                "database to improve similarity "
                "analysis."
            )

        else:
            results = []

            for candidate in players:
                if (
                    candidate["id"] == target["id"]
                    and
                    normalize_text(
                        candidate["team"]
                    ) == normalize_text(
                        target["team"]
                    )
                ):
                    continue

                stats = calculate_metrics(
                    candidate
                )

                results.append(
                    {
                        "Player": candidate["name"],
                        "Team": candidate["team"],
                        "Similarity": similarity_score(
                            target,
                            candidate,
                            players
                        ),
                        "Goals / 90": round(
                            stats["goals_per_90"],
                            2
                        ),
                        "Assists / 90": round(
                            stats["assists_per_90"],
                            2
                        ),
                        "G+A / 90": round(
                            stats["contributions_per_90"],
                            2
                        )
                    }
                )

            results = sorted(
                results,
                key=lambda row: row["Similarity"],
                reverse=True
            )

            st.subheader(
                f"Most Similar to "
                f"{target['name']}"
            )

            st.dataframe(
                results[:10],
                use_container_width=True,
                hide_index=True
            )

            for result in results[:5]:
                st.write(
                    f"### {result['Player']} "
                    f"— {result['Similarity']}%"
                )

                st.caption(
                    result["Team"]
                )

                st.progress(
                    min(
                        1.0,
                        max(
                            0.0,
                            result["Similarity"] / 100
                        )
                    )
                )


elif page == "Analytics":

    st.markdown(
        '<p class="main-title">'
        'Advanced Analytics'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Percentiles and performance '
        'analysis across your cached players.'
        '</p>',
        unsafe_allow_html=True
    )

    player = api_player_search(
        "analytics",
        "Analyze Player"
    )

    if player:
        metrics = render_player_summary(
            player
        )

        population = load_players_for_season(
            player["season"]
        )

        st.divider()

        per90 = pd.DataFrame(
            {
                "Metric": [
                    "Goals / 90",
                    "Assists / 90",
                    "G+A / 90"
                ],
                "Value": [
                    metrics["goals_per_90"],
                    metrics["assists_per_90"],
                    metrics["contributions_per_90"]
                ]
            }
        ).set_index(
            "Metric"
        )

        st.subheader(
            "Per-90 Performance"
        )

        st.bar_chart(per90)

        if population:
            percentiles = build_percentiles(
                player,
                population
            )

            st.subheader(
                "Percentiles"
            )

            st.dataframe(
                percentiles,
                use_container_width=True,
                hide_index=True
            )

            st.bar_chart(
                pd.DataFrame(
                    percentiles
                ).set_index(
                    "Metric"
                )[["Percentile"]]
            )

        history = get_history(
            player["name"]
        )

        if len(history) > 1:
            rows = []

            for item in history:
                stats = calculate_metrics(
                    item
                )

                rows.append(
                    {
                        "Season": str(
                            item["season"]
                        ),
                        "Goals": stats["goals"],
                        "Assists": stats["assists"],
                        "G+A": stats["goal_contributions"]
                    }
                )

            st.subheader(
                "Career Trend"
            )

            st.line_chart(
                pd.DataFrame(
                    rows
                ).set_index(
                    "Season"
                )
            )


elif page == "Database Explorer":

    st.markdown(
        '<p class="main-title">'
        'Database Explorer'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Browse every player cached '
        'from API-Football.'
        '</p>',
        unsafe_allow_html=True
    )

    season = st.selectbox(
        "Season",
        get_available_seasons()
    )

    players = load_players_for_season(
        season
    )

    search = st.text_input(
        "Search player or club"
    )

    query = normalize_text(
        search
    )

    rows = []

    for player in players:
        if query:
            if (
                query not in normalize_text(
                    player["name"]
                )
                and query not in normalize_text(
                    player["team"]
                )
            ):
                continue

        metrics = calculate_metrics(
            player
        )

        rows.append(
            {
                "Player": player["name"],
                "Team": player["team"],
                "Age": player["age"],
                "Appearances": metrics["appearances"],
                "Starts": metrics["starts"],
                "Minutes": metrics["minutes"],
                "Goals": metrics["goals"],
                "Assists": metrics["assists"],
                "G+A": metrics["goal_contributions"],
                "Goals / 90": round(
                    metrics["goals_per_90"],
                    2
                ),
                "Assists / 90": round(
                    metrics["assists_per_90"],
                    2
                ),
                "G+A / 90": round(
                    metrics["contributions_per_90"],
                    2
                )
            }
        )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Rows",
        len(rows)
    )

    c2.metric(
        "Players",
        len(
            {
                normalize_text(
                    row["Player"]
                )
                for row in rows
            }
        )
    )

    c3.metric(
        "Teams",
        len(
            {
                normalize_text(
                    row["Team"]
                )
                for row in rows
            }
        )
    )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True
    )

    if rows:
        export = pd.DataFrame(
            rows
        )

        st.download_button(
            "Download CSV",
            data=export.to_csv(
                index=False
            ).encode(
                "utf-8"
            ),
            file_name=(
                f"soccer_players_{season}.csv"
            ),
            mime="text/csv"
        )


elif page == "Live Matches":

    st.markdown(
        '<p class="main-title">'
        'Live Matches'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">'
        'Current matches directly '
        'from API-Football.'
        '</p>',
        unsafe_allow_html=True
    )

    st.caption(
        "Pressing refresh uses one "
        "API request."
    )

    if st.button(
        "Refresh Live Matches",
        type="primary",
        use_container_width=True
    ):
        try:
            with st.spinner(
                "Loading live matches..."
            ):
                matches = get_live_matches()

            rows = live_match_rows(
                matches
            )

            if rows:
                st.success(
                    f"{len(rows)} live "
                    "matches found."
                )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No live matches "
                    "right now."
                )

        except Exception as error:
            st.error(
                api_error_message(error)
            )       