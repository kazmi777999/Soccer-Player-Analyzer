
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const API_BASE_URL = "https://sportapi.ai/api";

const LEAGUES: Record<string, string[]> = {
  all: [],
  "39": ["premier league"],
  "140": ["la liga", "primera division"],
  "135": ["serie a"],
  "78": ["bundesliga"],
  "61": ["ligue 1"],
  "2": ["champions league"],
};

type Fixture = {
  id?: number | string;
  league_name?: string;
  status?: string;
  minute?: number | string | null;
  kickoff_utc?: string;
  home_team?: string;
  away_team?: string;
  home_score?: number | null;
  away_score?: number | null;
};

function isLive(status: string): boolean {
  const value = status.toUpperCase();

  return [
    "LIVE",
    "1H",
    "2H",
    "HT",
    "ET",
    "P",
    "PEN",
    "IN_PLAY",
    "IN PROGRESS",
  ].includes(value);
}

function matchesLeague(
  leagueName: string,
  selectedLeague: string
): boolean {
  if (selectedLeague === "all") {
    return true;
  }

  const allowedNames = LEAGUES[selectedLeague];

  return allowedNames.some((name) =>
    leagueName.toLowerCase().includes(name)
  );
}

export async function GET(request: NextRequest) {
  const apiKey = process.env.SPORTAPI_KEY;

  if (!apiKey) {
    return NextResponse.json(
      {
        error:
          "SPORTAPI_KEY is missing. Add it to frontend/.env.local and restart the server.",
      },
      { status: 503 }
    );
  }

  const searchParams = request.nextUrl.searchParams;

  const mode =
    searchParams.get("mode") === "today" ? "today" : "live";

  const league = searchParams.get("league") || "all";

  if (!(league in LEAGUES)) {
    return NextResponse.json(
      { error: "Invalid league selection." },
      { status: 400 }
    );
  }

  // Fetch today's fixtures using the UTC date.
  const today = new Date().toISOString().slice(0, 10);

  const endpoint = `${API_BASE_URL}/fixtures/date/${today}`;

  try {
    const response = await fetch(endpoint, {
      method: "GET",
      headers: {
        "X-Api-Key": apiKey,
        Accept: "application/json",
      },
      cache: "no-store",
      signal: AbortSignal.timeout(12000),
    });

    const data = await response.json();

    if (!response.ok || data.success === false) {
      const message =
        typeof data.error === "string"
          ? data.error
          : typeof data.message === "string"
          ? data.message
          : `HTTP ${response.status}`;

      return NextResponse.json(
        {
          error: `SportAPI error: ${message}`,
        },
        {
          status: response.status === 429 ? 429 : 502,
        }
      );
    }

    const fixtures: Fixture[] = Array.isArray(data.data)
      ? data.data
      : [];

    const matches = fixtures
      .filter((fixture) => {
        const leagueName = fixture.league_name || "";
        const status = fixture.status || "";

        const leagueAllowed = matchesLeague(
          leagueName,
          league
        );

        const modeAllowed =
          mode === "today" || isLive(status);

        return leagueAllowed && modeAllowed;
      })
      .map((fixture) => ({
        id: fixture.id ?? "",
        league: fixture.league_name || "Unknown competition",
        status: fixture.status || "Scheduled",
        minute: fixture.minute ?? null,
        kickoff: fixture.kickoff_utc || "",
        home: fixture.home_team || "Home team",
        away: fixture.away_team || "Away team",
        homeGoals: fixture.home_score ?? null,
        awayGoals: fixture.away_score ?? null,
      }));

    return NextResponse.json(
      {
        matches,
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      }
    );
  } catch (error) {
    const message =
      error instanceof Error
        ? error.name === "TimeoutError"
          ? "SportAPI request timed out."
          : "Could not connect to SportAPI."
        : "Unexpected SportAPI connection error.";

    return NextResponse.json(
      {
        error: message,
      },
      { status: 502 }
    );
  }
}
 