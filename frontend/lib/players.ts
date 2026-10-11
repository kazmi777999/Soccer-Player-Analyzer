import rawPlayers from "./players-data.json";

export type Player = {
  name: string; team: string; league: string; nation: string; position: string;
  matches: number; minutes: number; goals: number; assists: number;
  xg: number; xa: number; goalsPer90: number; assistsPer90: number;
};

export const players: Player[] = rawPlayers as Player[];
export const topScorers = [...players].sort((a, b) => b.goals - a.goals || b.assists - a.assists);
export const teams = [...new Set(players.map(p => p.team))].sort();
export function searchPlayers(query: string, limit = 30): Player[] {
  const q = query.trim().toLocaleLowerCase();
  return (q ? players.filter(p => [p.name,p.team,p.league].some(v => v.toLocaleLowerCase().includes(q))) : topScorers).slice(0,limit);
}
