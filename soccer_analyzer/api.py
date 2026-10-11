import requests
import unicodedata

from config import API_KEY


BASE_URL = "https://v3.football.api-sports.io"

API_SEASON = 2024


def get_headers():
    return {
        "x-apisports-key": API_KEY
    }


def api_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=get_headers(),
        params=params or {},
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    errors = data.get("errors")

    if errors:
        if isinstance(errors, dict):
            messages = []

            for key, value in errors.items():
                if value:
                    messages.append(
                        f"{key}: {value}"
                    )

            if messages:
                raise RuntimeError(
                    " | ".join(messages)
                )

        raise RuntimeError(
            str(errors)
        )

    return data.get(
        "response",
        []
    )


def normalize_text(text):
    text = str(
        text or ""
    ).lower().strip()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        character
        for character in text
        if not unicodedata.combining(
            character
        )
    )


def normalize_player_name(text):
    text = normalize_text(text)

    replacements = {
        "-": " ",
        ".": " ",
        "_": " "
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new
        )

    return " ".join(
        text.split()
    )


def get_live_matches():
    return api_get(
        "fixtures",
        {
            "live": "all"
        }
    )


def team_search_terms(name):
    name = str(name or "").strip()

    if not name:
        return []

    normalized = normalize_text(name)

    aliases = {
        "bayern": ["Bayern", "Bayern Munich", "Bayern München"],
        "bayern munich": ["Bayern Munich", "Bayern", "Bayern München"],
        "bayern munchen": ["Bayern München", "Bayern Munich", "Bayern"],
        "fc bayern": ["Bayern", "Bayern Munich", "Bayern München"],
        "fc bayern munich": ["Bayern Munich", "Bayern", "Bayern München"],
        "fc bayern munchen": ["Bayern München", "Bayern Munich", "Bayern"],
        "man united": ["Manchester United"],
        "man utd": ["Manchester United"],
        "manchester utd": ["Manchester United"],
        "man city": ["Manchester City"],
        "psg": ["Paris Saint Germain", "Paris Saint-Germain"],
        "paris saint germain": ["Paris Saint Germain", "Paris Saint-Germain"],
        "barca": ["Barcelona"],
        "fc barcelona": ["Barcelona"],
        "real": ["Real Madrid"],
        "real madrid cf": ["Real Madrid"],
        "atletico": ["Atletico Madrid", "Atlético Madrid"],
        "atletico madrid": ["Atletico Madrid", "Atlético Madrid"],
        "athletico madrid": ["Atletico Madrid", "Atlético Madrid"],
        "inter milan": ["Inter", "Inter Milan"],
        "internazionale": ["Inter", "Inter Milan"],
        "ac milan": ["AC Milan", "Milan"],
        "milan": ["AC Milan", "Milan"],
        "juve": ["Juventus"],
        "bvb": ["Borussia Dortmund"],
        "dortmund": ["Borussia Dortmund"],
        "leverkusen": ["Bayer Leverkusen"],
        "rb leipzig": ["RB Leipzig"],
        "leipzig": ["RB Leipzig"]
    }

    terms = [name]
    terms.extend(aliases.get(normalized, []))

    words = name.split()

    if len(words) > 1:
        terms.append(words[-1])

    unique = []
    seen = set()

    for term in terms:
        key = normalize_text(term)

        if key and key not in seen:
            seen.add(key)
            unique.append(term)

    return unique


def search_team(name):
    results = []
    seen_ids = set()

    for term in team_search_terms(name):
        try:
            response = api_get(
                "teams",
                {
                    "search": term
                }
            )
        except RuntimeError:
            continue

        for item in response:
            team = item.get(
                "team",
                {}
            )

            team_id = team.get("id")

            if team_id and team_id not in seen_ids:
                seen_ids.add(team_id)
                results.append(item)

        if results:
            break

    return results


def team_match_score(search_name, team_name):
    wanted = normalize_text(search_name)
    candidate = normalize_text(team_name)

    aliases = {
        "bayern": "bayern munich",
        "bayern munchen": "bayern munich",
        "fc bayern": "bayern munich",
        "fc bayern munich": "bayern munich",
        "fc bayern munchen": "bayern munich",
        "man united": "manchester united",
        "man utd": "manchester united",
        "manchester utd": "manchester united",
        "man city": "manchester city",
        "psg": "paris saint germain",
        "paris saint-germain": "paris saint germain",
        "barca": "barcelona",
        "fc barcelona": "barcelona",
        "real madrid cf": "real madrid",
        "atletico": "atletico madrid",
        "athletico madrid": "atletico madrid",
        "inter milan": "inter",
        "internazionale": "inter",
        "juve": "juventus",
        "bvb": "borussia dortmund",
        "dortmund": "borussia dortmund",
        "leverkusen": "bayer leverkusen",
        "leipzig": "rb leipzig"
    }

    wanted = aliases.get(wanted, wanted)
    candidate = aliases.get(candidate, candidate)

    if wanted == candidate:
        return 100

    if wanted in candidate or candidate in wanted:
        return 90

    wanted_words = set(wanted.split())
    candidate_words = set(candidate.split())

    if wanted_words and candidate_words:
        overlap = len(wanted_words & candidate_words)
        union = len(wanted_words | candidate_words)

        if union:
            return int((overlap / union) * 80)

    return 0


def find_team(name):
    results = search_team(name)

    if not results:
        return None

    ranked = sorted(
        results,
        key=lambda item: team_match_score(
            name,
            item.get(
                "team",
                {}
            ).get(
                "name",
                ""
            )
        ),
        reverse=True
    )

    return ranked[0]


def get_team_by_id(team_id):
    results = api_get(
        "teams",
        {
            "id": team_id
        }
    )

    if not results:
        return None

    return results[0]


def get_team_profile(team_name):
    result = find_team(team_name)

    if not result:
        return None

    team = result.get(
        "team",
        {}
    )

    venue = result.get(
        "venue",
        {}
    ) or {}

    return {
        "id": team.get("id"),
        "name": team.get(
            "name",
            team_name
        ),
        "code": team.get("code"),
        "country": team.get("country"),
        "founded": team.get("founded"),
        "national": team.get("national"),
        "logo": team.get("logo"),
        "venue": venue.get("name"),
        "venue_city": venue.get("city"),
        "venue_capacity": venue.get("capacity")
    }


def get_team_squad(team_name):
    team_result = find_team(
        team_name
    )

    if not team_result:
        return []

    team = team_result.get(
        "team",
        {}
    )

    team_id = team.get(
        "id"
    )

    if not team_id:
        return []

    results = api_get(
        "players/squads",
        {
            "team": team_id
        }
    )

    if not results:
        return []

    players = results[0].get(
        "players",
        []
    )

    cleaned = []

    for player in players:
        cleaned.append(
            {
                "id": player.get("id"),
                "name": player.get("name"),
                "age": player.get("age"),
                "number": player.get("number"),
                "position": player.get("position"),
                "photo": player.get("photo")
            }
        )

    return cleaned


def get_team_squad_data(team_name):
    team_result = find_team(
        team_name
    )

    if not team_result:
        return None

    team = team_result.get(
        "team",
        {}
    )

    team_id = team.get("id")

    if not team_id:
        return None

    players = get_team_squad(
        team.get(
            "name",
            team_name
        )
    )

    return {
        "team": {
            "id": team_id,
            "name": team.get(
                "name",
                team_name
            ),
            "code": team.get("code"),
            "country": team.get("country"),
            "founded": team.get("founded"),
            "logo": team.get("logo")
        },
        "players": players
    }


def team_matches(
    statistics,
    team_name
):
    wanted = normalize_text(
        team_name
    )

    for item in statistics:
        team = item.get(
            "team",
            {}
        )

        name = normalize_text(
            team.get(
                "name",
                ""
            )
        )

        if name == wanted:
            return True

    return False


def player_name_matches(
    player_name,
    search_name
):
    player = normalize_player_name(
        player_name
    )

    search = normalize_player_name(
        search_name
    )

    if not player or not search:
        return False

    if player == search:
        return True

    if search in player:
        return True

    player_parts = player.split()
    search_parts = search.split()

    if not player_parts:
        return False

    if not search_parts:
        return False

    if (
        player_parts[-1]
        == search_parts[-1]
    ):
        return True

    if len(search_parts) >= 2:
        search_initial = (
            search_parts[0][0]
        )

        search_last = (
            search_parts[-1]
        )

        player_initial = (
            player_parts[0][0]
        )

        player_last = (
            player_parts[-1]
        )

        if (
            search_initial
            == player_initial
            and search_last
            == player_last
        ):
            return True

    return False


def build_player_data(item):
    if not item:
        return None

    player = item.get(
        "player",
        {}
    )

    statistics = item.get(
        "statistics",
        []
    )

    result = {
        "name": player.get(
            "name",
            "Unknown"
        ),
        "id": player.get(
            "id"
        ),
        "age": player.get(
            "age"
        ),
        "firstname": player.get(
            "firstname"
        ),
        "lastname": player.get(
            "lastname"
        ),
        "nationality": player.get(
            "nationality"
        ),
        "height": player.get(
            "height"
        ),
        "weight": player.get(
            "weight"
        ),
        "injured": player.get(
            "injured"
        ),
        "photo": player.get(
            "photo"
        ),
        "statistics": []
    }

    for stats in statistics:
        league = stats.get(
            "league",
            {}
        )

        team = stats.get(
            "team",
            {}
        )

        games = stats.get(
            "games",
            {}
        )

        goals = stats.get(
            "goals",
            {}
        )

        appearances = (
            games.get(
                "appearences"
            )
            or 0
        )

        starts = (
            games.get(
                "lineups"
            )
            or 0
        )

        minutes = (
            games.get(
                "minutes"
            )
            or 0
        )

        goals_total = (
            goals.get(
                "total"
            )
            or 0
        )

        assists = (
            goals.get(
                "assists"
            )
            or 0
        )

        result[
            "statistics"
        ].append(
            {
                "competition":
                    league.get(
                        "name",
                        "Unknown"
                    ),

                "competition_id":
                    league.get(
                        "id"
                    ),

                "competition_logo":
                    league.get(
                        "logo"
                    ),

                "competition_country":
                    league.get(
                        "country"
                    ),

                "team":
                    team.get(
                        "name",
                        "Unknown"
                    ),

                "team_id":
                    team.get(
                        "id"
                    ),

                "team_logo":
                    team.get(
                        "logo"
                    ),

                "appearances":
                    appearances,

                "starts":
                    starts,

                "minutes":
                    minutes,

                "goals":
                    goals_total,

                "assists":
                    assists
            }
        )

    return result


def search_player_stats(
    name,
    team_id,
    team_name
):
    page = 1

    while page <= 3:
        try:
            results = api_get(
                "players",
                {
                    "team":
                        team_id,

                    "season":
                        API_SEASON,

                    "search":
                        name,

                    "page":
                        page
                }
            )

        except RuntimeError:
            return None

        if not results:
            break

        for item in results:
            player = item.get(
                "player",
                {}
            )

            if not player_name_matches(
                player.get(
                    "name",
                    ""
                ),
                name
            ):
                continue

            statistics = item.get(
                "statistics",
                []
            )

            if team_matches(
                statistics,
                team_name
            ):
                return item

        page += 1

    return None


def find_player_id_in_squad(
    name,
    team_id
):
    try:
        results = api_get(
            "players/squads",
            {
                "team":
                    team_id
            }
        )

    except RuntimeError:
        return None

    if not results:
        return None

    players = results[0].get(
        "players",
        []
    )

    for player in players:
        if player_name_matches(
            player.get(
                "name",
                ""
            ),
            name
        ):
            return player.get(
                "id"
            )

    search = normalize_player_name(
        name
    )

    if not search:
        return None

    first_letter = search[0]

    candidates = []

    for player in players:
        player_name = (
            normalize_player_name(
                player.get(
                    "name",
                    ""
                )
            )
        )

        if not player_name:
            continue

        if (
            player_name.startswith(
                first_letter + " "
            )
            or player_name.startswith(
                first_letter + "."
            )
        ):
            candidates.append(
                player
            )

    if len(candidates) == 1:
        return candidates[0].get(
            "id"
        )

    return None


def search_player_profile(name):
    if not name:
        return []

    search = name.strip()

    if len(search) < 3:
        return []

    try:
        return api_get(
            "players/profiles",
            {
                "search":
                    search
            }
        )

    except RuntimeError:
        return []


def search_player_candidates(name):
    results = search_player_profile(
        name
    )

    candidates = []

    for item in results:
        player = item.get(
            "player",
            {}
        )

        candidates.append(
            {
                "id":
                    player.get(
                        "id"
                    ),

                "name":
                    player.get(
                        "name",
                        "Unknown"
                    ),

                "firstname":
                    player.get(
                        "firstname"
                    ),

                "lastname":
                    player.get(
                        "lastname"
                    ),

                "age":
                    player.get(
                        "age"
                    ),

                "nationality":
                    player.get(
                        "nationality"
                    ),

                "height":
                    player.get(
                        "height"
                    ),

                "weight":
                    player.get(
                        "weight"
                    ),

                "photo":
                    player.get(
                        "photo"
                    )
            }
        )

    return candidates


def get_player_teams(
    player_id
):
    try:
        results = api_get(
            "players/teams",
            {
                "player":
                    player_id
            }
        )

    except RuntimeError:
        return []

    teams = []

    for item in results:
        team = item.get(
            "team",
            {}
        )

        seasons = item.get(
            "seasons",
            []
        )

        teams.append(
            {
                "team_id":
                    team.get(
                        "id"
                    ),

                "team":
                    team.get(
                        "name",
                        "Unknown"
                    ),

                "logo":
                    team.get(
                        "logo"
                    ),

                "seasons":
                    seasons
            }
        )

    return teams


def player_played_for_team(
    player_id,
    team_id
):
    teams = get_player_teams(
        player_id
    )

    for item in teams:
        if (
            item.get(
                "team_id"
            )
            == team_id
        ):
            return True

    return False


def find_player_id_from_profiles(
    name,
    team_id
):
    results = search_player_profile(
        name
    )

    if not results:
        return None

    strong_matches = []

    for item in results:
        player = item.get(
            "player",
            {}
        )

        if player_name_matches(
            player.get(
                "name",
                ""
            ),
            name
        ):
            strong_matches.append(
                player
            )

    for player in strong_matches:
        player_id = player.get(
            "id"
        )

        if not player_id:
            continue

        try:
            if player_played_for_team(
                player_id,
                team_id
            ):
                return player_id

        except RuntimeError:
            continue

    if len(strong_matches) == 1:
        return strong_matches[
            0
        ].get(
            "id"
        )

    return None


def get_player_stats_by_id(
    player_id,
    team_name
):
    try:
        results = api_get(
            "players",
            {
                "id":
                    player_id,

                "season":
                    API_SEASON
            }
        )

    except RuntimeError:
        return None

    if not results:
        return None

    wanted_team = normalize_text(
        team_name
    )

    for item in results:
        statistics = item.get(
            "statistics",
            []
        )

        matching_statistics = []

        for stats in statistics:
            team = stats.get(
                "team",
                {}
            )

            current_team = normalize_text(
                team.get(
                    "name",
                    ""
                )
            )

            if current_team == wanted_team:
                matching_statistics.append(
                    stats
                )

        if matching_statistics:
            item = dict(
                item
            )

            item[
                "statistics"
            ] = matching_statistics

            return item

    return None


def get_player_stats_by_player_id(
    player_id,
    season=API_SEASON
):
    try:
        results = api_get(
            "players",
            {
                "id":
                    player_id,

                "season":
                    season
            }
        )

    except RuntimeError:
        return None

    if not results:
        return None

    return build_player_data(
        results[0]
    )


def get_player_stats(
    name,
    team_name
):
    name = str(
        name or ""
    ).strip()

    team_name = str(
        team_name or ""
    ).strip()

    if len(name) < 3:
        raise ValueError(
            "Player name must contain at least 3 characters."
        )

    if not team_name:
        raise ValueError(
            "Team name is required."
        )


    team_result = find_team(
        team_name
    )

    if not team_result:
        return None

    team = team_result.get(
        "team",
        {}
    )

    team_id = team.get(
        "id"
    )

    official_team_name = team.get(
        "name",
        team_name
    )

    if not team_id:
        return None


    direct_result = (
        search_player_stats(
            name,
            team_id,
            official_team_name
        )
    )

    if direct_result:
        return build_player_data(
            direct_result
        )


    player_id = (
        find_player_id_in_squad(
            name,
            team_id
        )
    )

    if player_id:
        result = (
            get_player_stats_by_id(
                player_id,
                official_team_name
            )
        )

        if result:
            return build_player_data(
                result
            )


    player_id = (
        find_player_id_from_profiles(
            name,
            team_id
        )
    )

    if player_id:
        result = (
            get_player_stats_by_id(
                player_id,
                official_team_name
            )
        )

        if result:
            return build_player_data(
                result
            )

    return None


def get_player_profile_by_id(
    player_id
):
    try:
        results = api_get(
            "players/profiles",
            {
                "player":
                    player_id
            }
        )

    except RuntimeError:
        return None

    if not results:
        return None

    return results[0].get(
        "player",
        {}
    )


def get_player_transfers(
    player_id
):
    try:
        results = api_get(
            "transfers",
            {
                "player":
                    player_id
            }
        )

    except RuntimeError:
        return []

    transfers = []

    for item in results:
        transfer_items = item.get(
            "transfers",
            []
        )

        for transfer in transfer_items:
            teams = transfer.get(
                "teams",
                {}
            ) or {}

            team_in = teams.get(
                "in",
                {}
            ) or {}

            team_out = teams.get(
                "out",
                {}
            ) or {}

            transfers.append(
                {
                    "date":
                        transfer.get(
                            "date"
                        ),

                    "type":
                        transfer.get(
                            "type"
                        ),

                    "from_team":
                        team_out.get(
                            "name"
                        ),

                    "from_logo":
                        team_out.get(
                            "logo"
                        ),

                    "to_team":
                        team_in.get(
                            "name"
                        ),

                    "to_logo":
                        team_in.get(
                            "logo"
                        )
                }
            )

    return transfers


def get_player_trophies(
    player_id
):
    try:
        results = api_get(
            "trophies",
            {
                "player":
                    player_id
            }
        )

    except RuntimeError:
        return []

    trophies = []

    for item in results:
        trophies.append(
            {
                "league":
                    item.get(
                        "league"
                    ),

                "country":
                    item.get(
                        "country"
                    ),

                "season":
                    item.get(
                        "season"
                    ),

                "place":
                    item.get(
                        "place"
                    )
            }
        )

    return trophies


def get_player_career_stats(
    player_id
):
    career = []

    seasons = [
        2022,
        2023,
        2024
    ]

    for season in seasons:
        try:
            results = api_get(
                "players",
                {
                    "id":
                        player_id,

                    "season":
                        season
                }
            )

        except RuntimeError:
            continue

        if not results:
            continue

        player_data = build_player_data(
            results[0]
        )

        if not player_data:
            continue

        statistics = player_data.get(
            "statistics",
            []
        )

        appearances = 0
        starts = 0
        minutes = 0
        goals = 0
        assists = 0

        teams = []

        for stats in statistics:
            appearances += (
                stats.get(
                    "appearances",
                    0
                )
                or 0
            )

            starts += (
                stats.get(
                    "starts",
                    0
                )
                or 0
            )

            minutes += (
                stats.get(
                    "minutes",
                    0
                )
                or 0
            )

            goals += (
                stats.get(
                    "goals",
                    0
                )
                or 0
            )

            assists += (
                stats.get(
                    "assists",
                    0
                )
                or 0
            )

            team_name = stats.get(
                "team"
            )

            if (
                team_name
                and team_name
                not in teams
            ):
                teams.append(
                    team_name
                )

        goal_contributions = (
            goals
            + assists
        )

        if minutes > 0:
            goals_per_90 = (
                goals
                / minutes
            ) * 90

            assists_per_90 = (
                assists
                / minutes
            ) * 90

            contributions_per_90 = (
                goal_contributions
                / minutes
            ) * 90

        else:
            goals_per_90 = 0.0
            assists_per_90 = 0.0
            contributions_per_90 = 0.0

        career.append(
            {
                "season":
                    season,

                "teams":
                    teams,

                "appearances":
                    appearances,

                "starts":
                    starts,

                "minutes":
                    minutes,

                "goals":
                    goals,

                "assists":
                    assists,

                "goal_contributions":
                    goal_contributions,

                "goals_per_90":
                    goals_per_90,

                "assists_per_90":
                    assists_per_90,

                "contributions_per_90":
                    contributions_per_90,

                "statistics":
                    statistics
            }
        )

    return career
  

def get_team_leagues(team_id, season=API_SEASON):
    try:
        results = api_get("leagues", {"team": team_id, "season": season})
    except RuntimeError:
        return []
    leagues = []
    for item in results:
        league = item.get("league", {}) or {}
        if league.get("type") == "League":
            leagues.append({"id": league.get("id"), "name": league.get("name"), "logo": league.get("logo"), "country": (item.get("country") or {}).get("name")})
    return leagues


def get_team_statistics(team_name, season=API_SEASON):
    profile = get_team_profile(team_name)
    if not profile:
        return None
    leagues = get_team_leagues(profile["id"], season)
    if not leagues:
        return None
    # Prefer the team's own domestic league over continental cups/friendlies,
    # since a team can appear in several competitions for the same season and
    # we only spend one API request on "teams/statistics" per comparison.
    non_friendlies = [l for l in leagues if l.get("name") != "Friendlies Clubs"]
    pool = non_friendlies or leagues
    domestic = [l for l in pool if l.get("country") == profile.get("country")]
    candidates = domestic or pool
    preferred = candidates[0]
    try:
        result = api_get("teams/statistics", {"team": profile["id"], "league": preferred["id"], "season": season})
    except RuntimeError:
        return None
    if not result:
        return None
    data = result[0] if isinstance(result, list) else result
    fixtures=data.get("fixtures",{}) or {}; played=fixtures.get("played",{}) or {}; wins=fixtures.get("wins",{}) or {}; draws=fixtures.get("draws",{}) or {}; loses=fixtures.get("loses",{}) or {}
    goals=data.get("goals",{}) or {}; gf=(goals.get("for",{}) or {}).get("total",{}) or {}; ga=(goals.get("against",{}) or {}).get("total",{}) or {}
    clean=data.get("clean_sheet",{}) or {}
    return {**profile, "team_id":profile["id"], "league_id":preferred["id"], "league_name":preferred["name"], "season":season,
            "matches":played.get("total",0) or 0,"wins":wins.get("total",0) or 0,"draws":draws.get("total",0) or 0,"losses":loses.get("total",0) or 0,
            "goals_for":gf.get("total",0) or 0,"goals_against":ga.get("total",0) or 0,"clean_sheets":clean.get("total",0) or 0,"form":data.get("form") or ""}  