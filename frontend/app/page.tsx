"use client";

import { useEffect, useMemo, useState } from "react";
import { players, searchPlayers, topScorers, teams, type Player } from "../lib/players";

const features = [
  {
    number: "01",
    title: "PLAYER INTELLIGENCE",
    text: "Search players and explore performance, career history, teams, competitions, and advanced football statistics.",
    tag: "PLAYER DATA",
  },
  {
    number: "02",
    title: "TEAM ANALYSIS",
    text: "Explore squads, team statistics, performances, and comparisons across the biggest competitions in football.",
    tag: "TEAM DATA",
  },
  {
    number: "03",
    title: "LIVE FOOTBALL",
    text: "Follow matches, scores, events, and key information from competitions around the world.",
    tag: "LIVE DATA",
  },
];

const stats = [
  ["01", "PLAYER PROFILES"],
  ["02", "TEAM ANALYSIS"],
  ["03", "LIVE MATCHES"],
  ["04", "ADVANCED METRICS"],
];



export default function Home() {
  const [loaded, setLoaded] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Player>(topScorers[0]);
  const [compare, setCompare] = useState<Player>(topScorers[1]);
  const [teamFilter, setTeamFilter] = useState("");
  const [compareQuery, setCompareQuery] = useState("");
  const [metric, setMetric] = useState<"goals"|"assists"|"goalsPer90"|"xg">("goals");
  const [league, setLeague] = useState("all");
  const [matchMode, setMatchMode] = useState<"live"|"today">("live");
  const [matches, setMatches] = useState<any[]>([]);
  const [matchError, setMatchError] = useState("");
  const [matchLoading, setMatchLoading] = useState(false);
  const [updatedAt, setUpdatedAt] = useState("");
  const compareResults = useMemo(() => searchPlayers(compareQuery, 20), [compareQuery]);
  async function refreshMatches() {
    setMatchLoading(true);
    try {
      const response = await fetch(`/api/matches?mode=${matchMode}&league=${league}`, {cache:"no-store"});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Unable to load matches");
      setMatches(payload.matches || []); setMatchError(""); setUpdatedAt(new Date().toLocaleTimeString());
    } catch (err) { setMatchError(err instanceof Error ? err.message : "Match feed unavailable"); setMatches([]); }
    finally { setMatchLoading(false); }
  }
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch(`/api/matches?mode=${matchMode}&league=${league}`, {cache:"no-store"});
        const payload = await response.json();
        if (cancelled) return;
        if (!response.ok) throw new Error(payload.error || "Unable to load matches");
        setMatches(payload.matches || []); setMatchError(""); setUpdatedAt(new Date().toLocaleTimeString());
      } catch (err) { if (!cancelled) {setMatchError(err instanceof Error ? err.message : "Match feed unavailable");setMatches([]);} }
    }
    load(); const interval = window.setInterval(load, 60000);
    return () => {cancelled = true;window.clearInterval(interval);};
  }, [matchMode,league]);
  const results = useMemo(() => searchPlayers(query, 24), [query]);
  const teamPlayers = useMemo(() => players.filter(p => p.team === teamFilter).sort((a,b) => b.goals+b.assists-a.goals-a.assists).slice(0,12), [teamFilter]);
  const chartPlayers = [...players].sort((a,b)=>b[metric]-a[metric]).slice(0,10);
  const chartMax = Math.max(1,...chartPlayers.map(p=>p[metric]));

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoaded(true);
    }, 50);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className={`site ${loaded ? "loaded" : ""}`}>
      {/* BACKGROUND */}
      <div className="ambient ambientOne" />
      <div className="ambient ambientTwo" />

      {/* NAVIGATION */}
      <nav className="navbar">
        <a className="brand" href="#top">
          <span className="brandBall">◉</span>
          <span>SOCCERANALYZER</span>
        </a>

        <div className="navLinks">
          <a href="#players">PLAYERS</a>
          <a href="#teams">TEAMS</a>
          <a href="#compare">COMPARE</a>
          <a href="#analytics">ANALYTICS</a>
          <a href="#live">LIVE</a>
        </div>

        <a className="navButton" href="#explore">
          EXPLORE
          <span>↗</span>
        </a>
      </nav>

      {/* HERO */}
      <section className="hero" id="top">
        <div className="heroGrid" />

        {/* LEFT SIDE */}
        <div className="heroCopy">
          <div className="eyebrow">
            <span className="pulseDot" />
            FOOTBALL INTELLIGENCE PLATFORM
          </div>

          <h1>
            UNDERSTAND
            <br />
            THE <span>GAME.</span>
          </h1>

          <p className="heroText">
            Player data. Team intelligence. Season analytics.
            <br />
            One platform built to understand the game beyond the score.
          </p>

          <div className="heroActions">
            <a className="primaryButton" href="#players">
              SEARCH PLAYERS
              <span>↗</span>
            </a>

            <a className="secondaryButton" href="#analytics">
              EXPLORE DATA
            </a>
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className="heroVideoArea">
          <div className="videoGlow" />

          <div className="videoFrame">
            <video
              className="heroVideo"
              autoPlay
              muted
              loop
              playsInline
              preload="auto"
            >
              <source
                src="/videos/ronaldo-hero.mp4"
                type="video/mp4"
              />
            </video>

            <div className="videoDarkOverlay" />
            <div className="videoGreenOverlay" />
            <div className="videoEdgeFade" />

            <div className="momentLabel">
              <span className="momentLine" />

              <div>
                <small>ICONIC MOMENT</small>
                <strong>RONALDO</strong>
                <p>TURIN • 2018</p>
              </div>
            </div>

            <div className="videoNumber">07</div>
          </div>

          {/* ANALYSIS LIVE */}
          <div className="floatingStat statTwo">
            <span>ANALYSIS</span>
            <strong>LIVE</strong>
          </div>

          <div className="videoCoordinates">
            <span>FOOTBALL HISTORY</span>
            <b>01</b>
          </div>
        </div>

        <div className="scrollHint">
          <div />
          <span>SCROLL TO EXPLORE</span>
        </div>
      </section>

      {/* TICKER */}
      <section className="ticker">
        <div className="tickerTrack">
          <span>PLAYER ANALYSIS</span>
          <b>✦</b>

          <span>TEAM INTELLIGENCE</span>
          <b>✦</b>

          <span>LIVE FOOTBALL</span>
          <b>✦</b>

          <span>PERFORMANCE DATA</span>
          <b>✦</b>

          <span>PLAYER ANALYSIS</span>
          <b>✦</b>

          <span>TEAM INTELLIGENCE</span>
          <b>✦</b>

          <span>LIVE FOOTBALL</span>
          <b>✦</b>

          <span>PERFORMANCE DATA</span>
          <b>✦</b>
        </div>
      </section>

      {/* STATS */}
      <section className="statsStrip">
        {stats.map(([number, label]) => (
          <div className="statItem" key={number}>
            <span>{number}</span>
            <strong>{label}</strong>
          </div>
        ))}
      </section>

      {/* PLATFORM */}
      <section className="exploreSection" id="explore">
        <div className="sectionHeading">
          <div>
            <span className="sectionNumber">01 / PLATFORM</span>

            <h2>
              EVERYTHING.
              <br />
              <span>ONE PLACE.</span>
            </h2>
          </div>

          <p>
            From individual player performance to complete team analysis,
            Soccer Analyzer brings football intelligence together in one
            modern platform.
          </p>
        </div>

        <div className="featureGrid">
          {features.map((feature, index) => (
            <button
              className={`featureCard ${
                activeFeature === index ? "active" : ""
              }`}
              key={feature.number}
              type="button"
              onClick={() => { setActiveFeature(index); document.getElementById(["players","teams","live"][index])?.scrollIntoView({behavior:"smooth"}); }}
              onMouseEnter={() => setActiveFeature(index)}
              onFocus={() => setActiveFeature(index)}
            >
              <div className="featureTop">
                <span>{feature.number}</span>
                <span className="featureArrow">↗</span>
              </div>

              <div>
                <span className="featureTag">{feature.tag}</span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* WORKING PLAYER SEARCH */}
      <section className="playerSection" id="players" style={{display:"block",padding:"90px 6%"}}>
        <span className="sectionNumber">02 / PLAYER DATABASE • 2025–26</span>
        <h2 style={{fontSize:"clamp(2.5rem,6vw,5rem)",margin:"20px 0"}}>KNOW THE <span>PLAYER.</span></h2>
        <p>Search {players.length.toLocaleString()} player records from the uploaded season dataset. Select a player to inspect real statistics.</p>
        <input aria-label="Search player, team or league" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player, team, or league..." style={{width:"100%",maxWidth:640,padding:16,margin:"20px 0",background:"#111d19",color:"white",border:"1px solid #4e8a6c",borderRadius:8}} />
        <div style={{display:"flex",flexWrap:"wrap",gap:8,maxHeight:180,overflowY:"auto"}}>
          {results.map((p,i)=><button key={`${p.name}-${p.team}-${i}`} type="button" onClick={()=>setSelected(p)} style={{padding:"10px 14px",borderRadius:6,border:"1px solid #3b5d4d",background:selected===p?"#267e54":"#15231d",color:"white",cursor:"pointer"}}>{p.name} · {p.team}</button>)}
          {results.length===0 && <p>No players match that search.</p>}
        </div>
        <div style={{background:"#111d19",border:"1px solid #2f6248",borderRadius:16,padding:24,marginTop:24}}>
          <span className="sectionNumber">PLAYER PROFILE</span>
          <h3 style={{fontSize:"clamp(1.8rem,4vw,3rem)",margin:"10px 0"}}>{selected.name}</h3>
          <p>{selected.team} · {selected.league} · {selected.position}</p>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(115px,1fr))",gap:14,marginTop:22}}>
            {[["MATCHES",selected.matches],["MINUTES",selected.minutes],["GOALS",selected.goals],["ASSISTS",selected.assists],["GOALS / 90",selected.goalsPer90],["ASSISTS / 90",selected.assistsPer90],["xG",selected.xg],["xAG",selected.xa]].map(([label,value])=><div key={label} style={{padding:14,background:"#1b3025",borderRadius:8}}><small style={{display:"block",color:"#a8bdb0"}}>{label}</small><strong style={{fontSize:26}}>{value}</strong></div>)}
          </div>
        </div>
      </section>
      <section className="exploreSection" id="teams">
        <div className="sectionHeading"><div><span className="sectionNumber">03 / TEAM ANALYSIS</span><h2>EXPLORE <span>SQUADS.</span></h2></div><p>Choose a team to view its leading players in the dataset.</p></div>
        <select aria-label="Choose a team" value={teamFilter} onChange={e=>setTeamFilter(e.target.value)} style={{padding:14,background:"#13241b",color:"white",border:"1px solid #4e8a6c",maxWidth:"100%"}}><option value="">Select a team</option>{teams.map(t=><option key={t}>{t}</option>)}</select>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))",gap:12,marginTop:20}}>{teamPlayers.map((p,i)=><div key={`${p.name}-${i}`} style={{background:"#17251e",padding:16,borderRadius:8}}><strong>{p.name}</strong><p>{p.matches} matches · {p.goals} goals · {p.assists} assists</p></div>)}</div>
      </section>
      <section className="analyticsSection" id="analytics">
        <div className="analyticsHeader"><div><span className="sectionNumber">04 / ANALYTICS</span><h2>REAL <span>NUMBERS.</span></h2></div><p>Explore player rankings from the uploaded season dataset. Choose a metric below.</p></div>
        <div style={{margin:"18px 0"}}><label htmlFor="metricSelect">Ranking metric: </label><select id="metricSelect" value={metric} onChange={e=>setMetric(e.target.value as typeof metric)} style={{padding:12,background:"#21382a",color:"white"}}><option value="goals">Goals</option><option value="assists">Assists</option><option value="goalsPer90">Goals per 90</option><option value="xg">Expected goals (xG)</option></select></div>
        <div className="chartCard" style={{padding:24}}>{chartPlayers.map((p,i)=><div key={`${p.name}-${i}`} style={{display:"grid",gridTemplateColumns:"minmax(120px,220px) 1fr 35px",alignItems:"center",gap:12,margin:"12px 0"}}><span style={{fontSize:13}}>{p.name}</span><div style={{background:"#22362b",height:18,borderRadius:4}}><div style={{width:`${100*p[metric]/chartMax}%`,height:"100%",background:"#56d991",borderRadius:4}} /></div><strong>{p[metric]}</strong></div>)}</div>
        <div id="compare" style={{marginTop:36,background:"#111d19",padding:24,borderRadius:12}}>
          <h3 style={{marginBottom:15}}>COMPARE TWO PLAYERS</h3>
          <p>Player 1: {selected.name} — change using Player Search above.</p>
          <label htmlFor="compareSearch">Search for Player 2</label>
          <input id="compareSearch" value={compareQuery} onChange={e=>setCompareQuery(e.target.value)} placeholder="Search any player or team" style={{display:"block",width:"100%",maxWidth:560,padding:12,margin:"12px 0",background:"#21382a",color:"white",border:"1px solid #4e8a6c"}} />
          <div style={{display:"flex",flexWrap:"wrap",gap:8,maxHeight:150,overflowY:"auto"}}>
            {compareResults.map((p,i)=><button key={`${p.name}-${p.team}-${i}`} type="button" onClick={()=>{setCompare(p);setCompareQuery(p.name)}} style={{padding:"8px 12px",background:compare===p?"#267e54":"#21382a",color:"white",border:"1px solid #456",borderRadius:6,cursor:"pointer"}}>{p.name} · {p.team}</button>)}
          </div>
          <div style={{overflowX:"auto",marginTop:22}}><table style={{width:"100%",borderCollapse:"collapse",textAlign:"left"}}><thead><tr><th style={{padding:12}}>STAT</th><th>{selected.name}</th><th>{compare.name}</th></tr></thead><tbody>
          {([['Matches','matches'],['Minutes','minutes'],['Goals','goals'],['Assists','assists'],['Goal contributions','contributions'],['Goals / 90','goalsPer90'],['Assists / 90','assistsPer90'],['xG','xg'],['xAG','xa']] as const).map(([label,key])=><tr key={key} style={{borderTop:"1px solid #395344"}}><td style={{padding:12}}>{label}</td><td>{key==='contributions'?selected.goals+selected.assists:selected[key]}</td><td>{key==='contributions'?compare.goals+compare.assists:compare[key]}</td></tr>)}
          </tbody></table></div>
        </div>
      </section>
      <section className="liveSection" id="live" style={{display:"block",padding:"80px 6%"}}>
        <span className="sectionNumber">05 / API-FOOTBALL</span>
        <h2>LIVE <span>MATCHES.</span></h2>
        
        <div style={{display:"flex",flexWrap:"wrap",gap:12,margin:"24px 0"}}>
          <select aria-label="Match mode" value={matchMode} onChange={e=>setMatchMode(e.target.value as "live"|"today")} style={{padding:12,background:"#162b20",color:"white"}}><option value="live">Live now</option><option value="today">All matches today</option></select>
          <select aria-label="Competition" value={league} onChange={e=>setLeague(e.target.value)} style={{padding:12,background:"#162b20",color:"white"}}><option value="all">All competitions</option><option value="39">Premier League</option><option value="140">La Liga</option><option value="135">Serie A</option><option value="78">Bundesliga</option><option value="61">Ligue 1</option><option value="2">Champions League</option></select>
          <button type="button" disabled={matchLoading} onClick={refreshMatches} style={{padding:"12px 20px",background:"#267e54",color:"white",border:0,borderRadius:6,cursor:"pointer"}}>{matchLoading?"Loading...":"Refresh scores"}</button>
        </div>
        {updatedAt && <p style={{fontSize:13}}>Last updated: {updatedAt}</p>}
        {matchError && <p role="alert" style={{color:"#ffb4a2",padding:16,border:"1px solid #934b40",borderRadius:8}}>{matchError}</p>}
        {!matchError && matches.length===0 && <p>No matches found for this selection. Try “All matches today” or another competition.</p>}
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:14}}>
          {matches.map((m:any)=><article key={m.id} style={{padding:20,background:"#13251b",border:"1px solid #3c654c",borderRadius:12}}>
            <small>{m.league} · {m.status} {m.minute!=null?`· ${m.minute}′`:""}</small>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,marginTop:14}}><strong>{m.home}</strong><strong style={{fontSize:24,whiteSpace:"nowrap"}}>{m.homeGoals??"–"} : {m.awayGoals??"–"}</strong><strong style={{textAlign:"right"}}>{m.away}</strong></div>
            <small style={{display:"block",marginTop:12}}>{m.kickoff ? new Date(m.kickoff).toLocaleString():""}</small>
          </article>)}
        </div>
      </section>
      {/* FOOTER */}
      <footer>
        <div className="footerBrand">
          <span>SOCCERANALYZER</span>
        </div>

        <p>FOOTBALL INTELLIGENCE PLATFORM</p>

        <span>© 2026</span>
      </footer>
    </main>
  );
}  