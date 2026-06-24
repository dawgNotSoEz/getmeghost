"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";

interface Movie {
  id: string;
  title: string;
  year: number;
  country: string;
  genres: string[];
  director: string;
}

interface RecommendationItem {
  movie_id: string;
  title: string;
  year?: number;
  country?: string;
  genres?: string[];
  similarity_score: number;
  final_score: number;
  why: string[];
  warnings: string[];
}

interface HealthStatus {
  status: string;
  database: string;
}

export default function Home() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [liked, setLiked] = useState<string[]>([]);
  const [disliked, setDisliked] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [backendStatus, setBackendStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recLoading, setRecLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Preference Filter State
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedVibes, setSelectedVibes] = useState<string[]>([]);
  const [selectedAvoids, setSelectedAvoids] = useState<string[]>([]);
  const [yearMin, setYearMin] = useState<string>("");
  const [yearMax, setYearMax] = useState<string>("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const regionOptions = ["South Korea", "Taiwan", "United States", "Japan", "Hong Kong"];
  const vibeOptions = ["ritual", "occult", "found-footage", "folklore", "cursed", "dread", "asian", "modern"];
  const avoidOptions = ["slow-burn", "gore", "jump-scare", "family drama", "investigation"];

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      // Check backend health
      const healthRes = await axios.get<HealthStatus>(`${API_URL}/health`, { timeout: 3000 });
      setBackendStatus(healthRes.data);

      // Fetch movies
      const moviesRes = await axios.get<Movie[]>(`${API_URL}/api/movies`);
      setMovies(moviesRes.data);
    } catch (err: any) {
      console.error(err);
      setError("Cannot reach the FastAPI backend. Please check that it is running.");
      setBackendStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLike = (id: string) => {
    if (liked.includes(id)) {
      setLiked(liked.filter((item) => item !== id));
    } else {
      setLiked([...liked, id]);
      setDisliked(disliked.filter((item) => item !== id));
    }
  };

  const handleDislike = (id: string) => {
    if (disliked.includes(id)) {
      setDisliked(disliked.filter((item) => item !== id));
    } else {
      setDisliked([...disliked, id]);
      setLiked(liked.filter((item) => item !== id));
    }
  };

  const toggleRegion = (region: string) => {
    setSelectedRegions(
      selectedRegions.includes(region)
        ? selectedRegions.filter((r) => r !== region)
        : [...selectedRegions, region]
    );
  };

  const toggleVibe = (vibe: string) => {
    setSelectedVibes(
      selectedVibes.includes(vibe)
        ? selectedVibes.filter((v) => v !== vibe)
        : [...selectedVibes, vibe]
    );
  };

  const toggleAvoid = (avoid: string) => {
    setSelectedAvoids(
      selectedAvoids.includes(avoid)
        ? selectedAvoids.filter((a) => a !== avoid)
        : [...selectedAvoids, avoid]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (liked.length === 0 && disliked.length === 0) {
      alert("Please select at least one movie to like or dislike.");
      return;
    }

    try {
      setRecLoading(true);
      const res = await axios.post(`${API_URL}/api/recommend`, {
        liked,
        disliked,
        preferences: {
          region: selectedRegions.length > 0 ? selectedRegions : null,
          vibe: selectedVibes.length > 0 ? selectedVibes : null,
          avoid: selectedAvoids.length > 0 ? selectedAvoids : null,
          year_min: yearMin ? parseInt(yearMin, 10) : null,
          year_max: yearMax ? parseInt(yearMax, 10) : null,
        },
      });
      setRecommendations(res.data.results);
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to generate recommendations.");
    } finally {
      setRecLoading(false);
    }
  };

  const clearSelection = () => {
    setLiked([]);
    setDisliked([]);
    setRecommendations([]);
    setSelectedRegions([]);
    setSelectedVibes([]);
    setSelectedAvoids([]);
    setYearMin("");
    setYearMax("");
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans selection:bg-rose-500 selection:text-white relative overflow-hidden">
      {/* Background glowing gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-rose-950/15 blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-950/15 blur-[130px] pointer-events-none" />

      {/* Header */}
      <header className="border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <span className="font-black text-white text-lg">T</span>
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-neutral-200 to-neutral-400 bg-clip-text text-transparent">
            TASTE ENGINE
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-neutral-900 border border-neutral-800 text-xs">
            <span className={`h-2.5 w-2.5 rounded-full ${backendStatus ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`} />
            <span>API Status: {loading ? "Checking..." : backendStatus ? "Connected" : "Offline"}</span>
          </div>
          <button 
            onClick={fetchData}
            className="p-1.5 hover:bg-neutral-900 border border-transparent hover:border-neutral-800 rounded-lg transition-all"
            title="Refresh database catalog"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className={`bi bi-arrow-clockwise ${loading ? "animate-spin" : ""}`} viewBox="0 0 16 16">
              <path fillRule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
              <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
            </svg>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-10 flex flex-col gap-8">
        <div className="space-y-2">
          <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold uppercase tracking-wider">
            Phase 3 Preference Intelligence
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-b from-white to-neutral-400 bg-clip-text text-transparent">
            Multi-Factor Recommender
          </h1>
          <p className="text-neutral-400 text-sm max-w-2xl">
            Calibrate constraints, diversity weights (MMR), and positive/negative preferences to get tailored recommendations with natural explanations.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-2xl flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
            </svg>
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left panel - Movie Catalog Selector */}
          <div className="lg:col-span-8 space-y-6">
            {/* Preferences Setup Panel */}
            <div className="bg-neutral-900/40 border border-neutral-850 rounded-3xl p-6 space-y-6">
              <h3 className="text-md font-bold tracking-tight text-neutral-200 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="text-indigo-400" viewBox="0 0 16 16">
                  <path d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.33L10 7.953V13.5a.5.5 0 0 1-.276.447l-3 1.5A.5.5 0 0 1 6 15V7.953L2.128 3.83a.5.5 0 0 1-.128-.33zm1.5.856V3h10v-.644L12.793 4H3.207z"/>
                </svg>
                Preference Filters & Vibe Adjusters
              </h3>

              <div className="space-y-4 text-sm">
                {/* Region Filter */}
                <div className="space-y-2">
                  <span className="text-xs text-neutral-400 font-semibold uppercase tracking-wider block">Countries/Regions</span>
                  <div className="flex flex-wrap gap-2">
                    {regionOptions.map((r) => (
                      <button
                        key={r}
                        onClick={() => toggleRegion(r)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          selectedRegions.includes(r)
                            ? "bg-indigo-500/10 border-indigo-500 text-indigo-300"
                            : "bg-neutral-950 border-neutral-800 hover:border-neutral-700 text-neutral-400"
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Vibe Overlap */}
                <div className="space-y-2">
                  <span className="text-xs text-neutral-400 font-semibold uppercase tracking-wider block">Explicit Vibes (Vibe Overlap Match)</span>
                  <div className="flex flex-wrap gap-2">
                    {vibeOptions.map((v) => (
                      <button
                        key={v}
                        onClick={() => toggleVibe(v)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          selectedVibes.includes(v)
                            ? "bg-emerald-500/10 border-emerald-500 text-emerald-300"
                            : "bg-neutral-950 border-neutral-800 hover:border-neutral-700 text-neutral-400"
                        }`}
                      >
                        #{v}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Avoid Tag Constraint */}
                <div className="space-y-2">
                  <span className="text-xs text-neutral-400 font-semibold uppercase tracking-wider block">Avoid Tags (Warnings Penalty)</span>
                  <div className="flex flex-wrap gap-2">
                    {avoidOptions.map((a) => (
                      <button
                        key={a}
                        onClick={() => toggleAvoid(a)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          selectedAvoids.includes(a)
                            ? "bg-rose-500/10 border-rose-500 text-rose-300"
                            : "bg-neutral-950 border-neutral-800 hover:border-neutral-700 text-neutral-400"
                        }`}
                      >
                        Avoid: {a}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Year Range */}
                <div className="space-y-2">
                  <span className="text-xs text-neutral-400 font-semibold uppercase tracking-wider block">Release Year Range</span>
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      placeholder="Min Year (e.g. 2000)"
                      value={yearMin}
                      onChange={(e) => setYearMin(e.target.value)}
                      className="bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 text-xs w-full focus:outline-none focus:border-indigo-500 text-neutral-200"
                    />
                    <span className="text-neutral-500">to</span>
                    <input
                      type="number"
                      placeholder="Max Year (e.g. 2026)"
                      value={yearMax}
                      onChange={(e) => setYearMax(e.target.value)}
                      className="bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 text-xs w-full focus:outline-none focus:border-indigo-500 text-neutral-200"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold tracking-tight text-neutral-200">Movie Catalog Selector</h2>
                <span className="text-xs text-neutral-500">{movies.length} items loaded</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {loading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-36 bg-neutral-900/40 border border-neutral-800 animate-pulse rounded-2xl" />
                  ))
                ) : (
                  movies.map((movie) => {
                    const isLiked = liked.includes(movie.id);
                    const isDisliked = disliked.includes(movie.id);
                    
                    return (
                      <motion.div
                        key={movie.id}
                        layout
                        className={`p-5 bg-neutral-900/60 border rounded-2xl flex flex-col justify-between gap-4 transition-all ${
                          isLiked 
                            ? "border-emerald-500/40 bg-emerald-950/5" 
                            : isDisliked 
                              ? "border-rose-500/40 bg-rose-950/5" 
                              : "border-neutral-850 hover:border-neutral-700"
                        }`}
                      >
                        <div className="space-y-1.5">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-bold text-neutral-100 leading-snug">{movie.title}</h3>
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 shrink-0">
                              {movie.year}
                            </span>
                          </div>
                          <p className="text-xs text-neutral-400">Dir: {movie.director} • {movie.country}</p>
                          <div className="flex flex-wrap gap-1 pt-1.5">
                            {movie.genres.map((g) => (
                              <span key={g} className="text-[10px] bg-neutral-800/80 px-2 py-0.5 rounded text-neutral-300">
                                {g}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Interaction Controls */}
                        <div className="flex items-center gap-2 pt-2 border-t border-neutral-800/50">
                          <button
                            onClick={() => handleLike(movie.id)}
                            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                              isLiked
                                ? "bg-emerald-500 text-neutral-950 font-bold shadow-md shadow-emerald-500/10"
                                : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
                            }`}
                          >
                            <span>{isLiked ? "Liked" : "Like"}</span>
                          </button>

                          <button
                            onClick={() => handleDislike(movie.id)}
                            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                              isDisliked
                                ? "bg-rose-500 text-white font-bold shadow-md shadow-rose-500/10"
                                : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
                            }`}
                          >
                            <span>{isDisliked ? "Disliked" : "Dislike"}</span>
                          </button>
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Right panel - Selection Profile & Trigger */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-6 space-y-6 sticky top-28">
              <h2 className="text-lg font-bold tracking-tight text-neutral-200">Your Selection</h2>
              
              <div className="space-y-4">
                {/* Liked list */}
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold tracking-wider text-neutral-400 uppercase mb-2">
                    <span>Liked Titles ({liked.length})</span>
                    {liked.length > 0 && <span className="h-2 w-2 rounded-full bg-emerald-500" />}
                  </div>
                  {liked.length === 0 ? (
                    <div className="p-3 rounded-xl border border-dashed border-neutral-800 text-xs text-neutral-500 text-center">
                      No titles liked yet
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1.5">
                      {liked.map((id) => {
                        const movie = movies.find((m) => m.id === id);
                        return (
                          <div key={id} className="flex items-center justify-between bg-neutral-950 px-3 py-2 rounded-xl border border-neutral-850 text-xs">
                            <span className="font-semibold text-neutral-200 truncate pr-2">{movie?.title}</span>
                            <button onClick={() => handleLike(id)} className="text-neutral-500 hover:text-neutral-300">
                              ✕
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Disliked list */}
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold tracking-wider text-neutral-400 uppercase mb-2">
                    <span>Disliked Titles ({disliked.length})</span>
                    {disliked.length > 0 && <span className="h-2 w-2 rounded-full bg-rose-500" />}
                  </div>
                  {disliked.length === 0 ? (
                    <div className="p-3 rounded-xl border border-dashed border-neutral-800 text-xs text-neutral-500 text-center">
                      No titles disliked yet
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1.5">
                      {disliked.map((id) => {
                        const movie = movies.find((m) => m.id === id);
                        return (
                          <div key={id} className="flex items-center justify-between bg-neutral-950 px-3 py-2 rounded-xl border border-neutral-850 text-xs">
                            <span className="font-semibold text-neutral-200 truncate pr-2">{movie?.title}</span>
                            <button onClick={() => handleDislike(id)} className="text-neutral-500 hover:text-neutral-300">
                              ✕
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-2 pt-4 border-t border-neutral-800">
                <button
                  onClick={handleSubmit}
                  disabled={liked.length === 0 && disliked.length === 0 || recLoading}
                  className={`w-full py-3.5 rounded-xl text-sm font-bold text-white transition-all flex items-center justify-center gap-2 ${
                    liked.length === 0 && disliked.length === 0 || recLoading
                      ? "bg-neutral-800 text-neutral-500 cursor-not-allowed"
                      : "bg-gradient-to-r from-rose-500 to-indigo-600 hover:shadow-lg hover:shadow-rose-500/20 active:scale-[0.98]"
                  }`}
                >
                  {recLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Reranking Candidates (MMR)...</span>
                    </>
                  ) : (
                    <span>Compute Recommendations</span>
                  )}
                </button>

                {(liked.length > 0 || disliked.length > 0) && (
                  <button
                    onClick={clearSelection}
                    className="w-full py-2.5 rounded-xl text-xs font-semibold border border-neutral-800 hover:bg-neutral-950 text-neutral-400 hover:text-neutral-200 transition-all"
                  >
                    Reset Dashboard
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Panel - Recommendation Results with Explanations */}
        <AnimatePresence>
          {recommendations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              className="space-y-4 pt-4 border-t border-neutral-900"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold tracking-tight text-neutral-200">Personalized Recommendations</h2>
                <span className="text-xs text-neutral-500 font-mono">MMR diversity enabled (λ=0.7)</span>
              </div>

              <div className="flex flex-col gap-4">
                {recommendations.map((m, index) => (
                  <motion.div
                    key={m.movie_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className="bg-neutral-900/60 border border-neutral-800/80 p-6 rounded-2xl relative overflow-hidden group hover:border-indigo-500/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
                  >
                    <div className="space-y-3 flex-1">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-neutral-500 font-mono">#{index + 1}</span>
                          <h3 className="font-extrabold text-neutral-100 text-lg leading-snug">{m.title}</h3>
                          <span className="text-xs font-medium px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 shrink-0">
                            {m.year}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-400">{m.country} | {m.genres?.join(", ")}</p>
                      </div>

                      {/* Reasons & Warnings */}
                      <div className="space-y-1.5 pt-1">
                        {m.why?.map((reason, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-emerald-400/90 leading-relaxed">
                            <span className="mt-0.5 select-none text-emerald-500">✓</span>
                            <span>{reason}</span>
                          </div>
                        ))}
                        {m.warnings?.map((warning, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-rose-400/90 leading-relaxed">
                            <span className="mt-0.5 select-none text-rose-500">⚠</span>
                            <span>{warning}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center border-t md:border-t-0 border-neutral-800/60 pt-3 md:pt-0 shrink-0 gap-1.5 min-w-[100px]">
                      <div>
                        <div className="text-[10px] text-neutral-500 font-mono tracking-wider">MATCH SCORE</div>
                        <div className="font-black font-mono text-xl text-indigo-400">
                          {m.final_score.toFixed(3)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[9px] text-neutral-600 font-mono">SEMANTIC SIM</div>
                        <div className="font-semibold font-mono text-xs text-neutral-400">
                          {m.similarity_score.toFixed(3)}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t border-neutral-900 bg-neutral-950/60 text-center text-xs text-neutral-500 mt-20">
        Taste Engine Intelligence Layer v0.3.0 • Phase 3 Core Complete
      </footer>
    </div>
  );
}
