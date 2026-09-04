# Graph Report - impeccable-init  (2026-09-04)

## Provenance

- Scanned tree: the `impeccable-init` linked worktree on branch
  `wip/batch-21` at `ee285ac` -- six commits ahead of `origin/main`
  (`f202b81`), all documentation-only.
- This graph therefore reflects `wip/batch-21` content, not `origin/main`.
  An agent bootstrapping from `origin/main` should expect the docs-layer
  nodes (plans, rulings, findings) to describe work and decisions that
  have not merged there yet. The code-layer nodes match `origin/main`
  because no production code changed on this branch.
- Built 2026-09-04 to let agents understand the repository faster at
  bootstrap. Query it with `graphify query "<question>"`; rebuild changed
  files with `graphify --update`. The graph data itself lives untracked in
  `graphify-out/`; this report is the tracked record.

## Session Verification Notes (2026-09-04)

Added by the session that built this graph, after tracing the suggested
questions against the raw edges. Two of the report's suggestions are
extraction artifacts, not structural findings:

1. **The `_reach_state()` "bridge" (Communities 50 to 1) is mislabeled.**
   Every EXTRACTED edge on `scripts_dev_frontend_gate_reach_state` stays
   inside Community 50; it is the shared helper for that community's six
   validation-state checks. Its betweenness score came entirely from one
   INFERRED `calls` edge to `valueerror`, where the AST captured a raised
   exception type as a callee. Treat it as a within-community funnel, not
   a cross-community bridge.

2. **The `patch` node's 133 INFERRED edges are mock-extraction noise.**
   `patch` is `unittest.mock.patch`; the extractor connected it to test
   functions that use it. These edges carry no architectural signal and
   should be pruned on any future rebuild.

Verified as genuine: the `create_app()` hub bridging the app factory,
frontend gate, startup-config and template-shell-test communities; and the
Batch 11-13 archive-log edges into `orchestrator.py` and `utils.py`
functions those batches shipped.

**Corpus exclusions, recorded rather than silent:**
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` was excluded from
semantic extraction (owner call: too large to parse; its durable content is
represented by the batch definitions and per-batch logs, which were
extracted). Two extraction sub-chunks (14-series retry and one 15-series
split) succeeded only after being re-dispatched as smaller chunks following
provider stream errors.

---

## Corpus Check
- 301 files | ~375,205 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3103 nodes | 5896 edges | 248 communities (149 shown, 99 thin omitted)
- Extraction: 92% EXTRACTED | 8% INFERRED | 0% AMBIGUOUS | INFERRED: 486 edges (avg confidence: 0.88)
- Token cost: 0 input | 0 output

## Community Hubs (Navigation)
- Album Results Pipeline
- Frontend Browser Gate
- Postgres Metadata Cache
- Last.fm Client
- Worktree Guard Tests
- Docsync Declarations
- Worktree Guard Core
- Background Album Job
- Spotify Client
- Heatmap Frontend
- Name Normalization
- Docsync Rotation Logic
- Gate Theme and Text Checks
- Docsync Integrity Checks
- Docsync Test Count Authority
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 218
- Community 219
- Community 220
- Community 221
- Community 222
- Community 223
- Community 224
- Community 225
- Community 226
- Community 227
- Community 228
- Community 230
- Community 231
- Community 232
- Community 233
- Community 237
- Community 238
- Community 240
- Community 241

## God Nodes (most connected - your core abstractions)
1. `collect_integrity_issues()` - 96 edges
2. `_valid_inputs()` - 78 edges
3. `create_job()` - 72 edges
4. `_repo()` - 66 edges
5. `_files()` - 64 edges
6. `Entry` - 53 edges
7. `inspect_worktree()` - 48 edges
8. `DeclarationError` - 46 edges
9. `_sync()` - 41 edges
10. `check_anchors()` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Batch 11` --implements--> `_fetch_spotify_misses()`  [EXTRACTED]
  docs/history/logs/BATCH11_LOG.md -> scrobblescope/orchestrator.py
- `Batch 12` --references--> `_fetch_spotify_misses()`  [EXTRACTED]
  docs/history/logs/BATCH12_LOG.md -> scrobblescope/orchestrator.py
- `Batch 13` --references--> `_fetch_spotify_misses()`  [EXTRACTED]
  docs/history/logs/BATCH13_LOG.md -> scrobblescope/orchestrator.py
- `Batch 11` --implements--> `_build_results()`  [EXTRACTED]
  docs/history/logs/BATCH11_LOG.md -> scrobblescope/orchestrator.py
- `Batch 12` --implements--> `format_seconds_mobile()`  [EXTRACTED]
  docs/history/logs/BATCH12_LOG.md -> scrobblescope/utils.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Scrobble filtering form controls** -- docs_images_index_dark_thresholds_decade_scrobble_filter_form, docs_images_index_dark_thresholds_decade_decade_filter, docs_images_index_dark_thresholds_decade_album_thresholds_panel, docs_images_index_dark_thresholds_decade_sort_by_play_count [INFERRED]
- **Documentation sync and gating system** -- _docsync_toml, _pre_commit_config_yaml_doc_state_sync_check, _pre_commit_config_yaml, _claude_session_context, _github_pull_request_template_pr_checklist [INFERRED 0.85]
- **Tailwind CSS reproducibility gates** -- _pre_commit_config_yaml_tailwind_css_drift, _github_workflows_test_tailwind_digest_step, _docsync_toml_light_muted_token [INFERRED 0.75]
- **Multi-agent orchestration method** -- development_amnesiac_engineers_problem, development_orchestration_architecture, development_batch_wp_structure, docs_agent_doc_map_anti_duplication_rule, agent_notes_template_extraction_intent [EXTRACTED 1.00]
- **Docsync toolchain modules** -- docs_architecture_documentation_tooling_doc_state_sync, docs_architecture_documentation_tooling_docsync_cli, docs_architecture_documentation_tooling_docsync_integrity, docs_architecture_documentation_tooling_docsync_logic, docs_architecture_documentation_tooling_docsync_models, docs_architecture_documentation_tooling_docsync_parser, docs_architecture_documentation_tooling_docsync_renderer [EXTRACTED 1.00]
- **Flask runtime modules** -- docs_architecture_runtime_system_app_py, docs_architecture_runtime_system_routes_py, docs_architecture_runtime_system_worker_py, docs_architecture_runtime_system_repositories_py, docs_architecture_runtime_system_orchestrator_py, docs_architecture_runtime_system_heatmap_py, docs_architecture_runtime_system_lastfm_py, docs_architecture_runtime_system_spotify_py, docs_architecture_runtime_system_cache_py, docs_architecture_runtime_system_utils_py, docs_architecture_runtime_system_domain_py, docs_architecture_runtime_system_errors_py [EXTRACTED 1.00]
- **Design token files composed by styles.css** -- docs_design_styles_css_design_system_entry_point, docs_design_tokens_colors_css_colors_tokens, docs_design_tokens_elevation_css_elevation_tokens, docs_design_tokens_fonts_css_fonts_tokens, docs_design_tokens_motion_css_motion_tokens, docs_design_tokens_spacing_css_spacing_tokens, docs_design_tokens_typography_css_typography_tokens [EXTRACTED 1.00]
- **Documentation sync toolchain** -- docs_architecture_documentation_tooling_md_doc_state_sync, docs_architecture_documentation_tooling_md_docsync_package, docs_architecture_documentation_tooling_md_pre_commit, docs_architecture_documentation_tooling_md_quality_gate [EXTRACTED 1.00]
- **Shared job pipeline participants** -- docs_architecture_heatmap_sequence_md_routes_py, docs_architecture_heatmap_sequence_md_worker_py, docs_architecture_heatmap_sequence_md_repositories_py, docs_architecture_runtime_system_md_jobs_state [EXTRACTED 1.00]
- **Design token system** -- docs_design_tokens_colors_css, docs_design_tokens_typography_css, docs_design_tokens_spacing_css, docs_design_tokens_motion_css, docs_design_tokens_elevation_css, docs_design_tokens_fonts_css [EXTRACTED 1.00]
- **Batches that built and polished the scrobble heatmap** -- docs_history_definitions_batch18_definition_batch_18, docs_history_definitions_batch19_definition_batch_19, batch21_definition_batch_21 [INFERRED 0.85]
- **Batches that built and hardened the docsync tooling** -- docs_history_definitions_batch14_definition_batch_14, docs_history_definitions_batch15_definition_batch_15, docs_history_definitions_batch20_definition_batch_20 [EXTRACTED 1.00]
- **Batches that shaped the frontend theme architecture** -- docs_history_definitions_batch11_definition_batch_11, docs_history_definitions_batch12_definition_batch_12, batch21_definition_batch_21 [EXTRACTED 1.00]
- **Batch 16 local-dev and testing tooling** -- scripts_dev_dev_start_py, scripts_testing__http_client_py, scripts_testing_smoke_cache_check_py, scripts_testing_concurrent_users_test_py [EXTRACTED 1.00]
- **Batch 8 modular refactor modules** -- scrobblescope, scrobblescope_orchestrator_py, scrobblescope_utils_py, scrobblescope_lastfm_py, scrobblescope_spotify_py, scrobblescope_repositories_py, scrobblescope_routes_py [EXTRACTED 1.00]
- **Heatmap feature stack introduced across Batches 18-19** -- scrobblescope_heatmap_py, heatmap_routes, static_js_heatmap_js, static_css_heatmap_css [EXTRACTED 1.00]
- **Batch 21 validation gates** -- concept_tailwind_css_drift_hook, concept_frontend_gate, concept_doc_state_sync, concept_worktree_guard [EXTRACTED 0.95]
- **Index wide-composition scaling defect cluster** -- concept_index_wide_scale_zoom, concept_scaling_formula_defect, concept_gate_viewport_blindness, concept_realistic_window_geometry_gate [EXTRACTED 0.95]
- **Tailwind toolchain (build, drift hook, theme tokens)** -- concept_tailwind_build, concept_tailwind_css_drift_hook, concept_theme_static, concept_adobe_fonts_kit_rwy8ghw [INFERRED 0.85]
- **Product analysis modes** -- product_scrobblescope, product_top_albums, product_listening_heatmap [EXTRACTED 1.00]
- **Batch 21 strangler migration machinery** -- product_batch21_strangler_migration, product_wp8_audit, product_batch21_definition_md, product_playbook_md [EXTRACTED 1.00]
- **Bootstrap verification ritual** -- handoff_bootstrap_verification, handoff_checklist, product_playbook_md, handoff_session_context_md [INFERRED 0.85]
- **Batch 21 work packages WP-0 through WP-8** -- playbook_batch_21_wp_0, playbook_batch_21_wp_1, playbook_batch_21_wp_2, playbook_batch_21_wp_3, playbook_batch_21_wp_4, playbook_batch_21_wp_5, playbook_batch_21_wp_6, playbook_batch_21_wp_7, playbook_batch_21_wp_8 [EXTRACTED 1.00]
- **Repository validation gates (docsync, worktree guard, frontend gate, tailwind drift hook)** -- concept_docsync, concept_worktree_guard, concept_frontend_gate, concept_tailwind_build [EXTRACTED 1.00]
- **F-B21 finding cluster driving Batch 21 scope and review** -- findings_f_b21_2, findings_f_b21_4, findings_f_b21_13, findings_f_b21_17, findings_f_b21_24 [EXTRACTED 1.00]
- **External memory layer of scoped documents for amnesiac agents** -- development_agents_md_role, development_handoff_prompt_role, development_agent_notes_role, development_playbook_role, development_session_context_role, development_history_archive [EXTRACTED 1.00]
- **Adobe Fonts type stack with family roles and weight constraints** -- docs_design_reconciliation_adobe_fonts, docs_design_reconciliation_font_families, docs_design_reconciliation_no_500_600_weights, agent_notes_adobe_kit_slop, agent_notes_wordmark_typeface [INFERRED 0.85]
- **Batch 21 frontend toolchain: Tailwind migration, build, scan scoping, Bootstrap retirement** -- readme_tailwind_daisyui_migration, development_frontend_asset_build, docs_design_reconciliation_tailwind_source_none, readme_bootstrap_retirement [EXTRACTED 1.00]
- **Background job pipeline participants** -- scrobblescope_worker__acquire_job_slot, scrobblescope_worker__start_job_thread, scrobblescope_repositories__create_job, scrobblescope_orchestrator__background_task, scrobblescope_heatmap__heatmap_task, scrobblescope_repositories__get_job_context [INFERRED 0.85]
- **Spotify enrichment pipeline** -- scrobblescope_orchestrator__run_spotify_search_phase, scrobblescope_orchestrator__run_spotify_batch_detail_phase, scrobblescope_spotify__search_for_spotify_album_id, scrobblescope_spotify__fetch_spotify_album_details_batch, scrobblescope_cache__batch_lookup_metadata [INFERRED 0.85]
- **Cross-thread rate limiting stack** -- scrobblescope_utils__global_throttle, scrobblescope_utils__throttled_limiter, scrobblescope_utils__get_lastfm_limiter, scrobblescope_utils__get_spotify_limiter [EXTRACTED 1.00]

## Communities (248 total, 99 thin omitted)

### Community 0 - "Album Results Pipeline"
Cohesion: 0.01
Nodes (145): _filter_results_for_display(), _group_unmatched_by_reason(), Remove albums with no play-time data when sorting by playtime. Albums without..., Group unmatched-album items by their ``reason`` string. Returns a tuple of..., parametrize, The Heatmap destination should resume this browser's latest run., GIVEN CSRF protection is active (default) WHEN POST /reset_progress is..., POST /heatmap_loading with a valid user returns 202 and a job_id. (+137 more)

### Community 1 - "Frontend Browser Gate"
Cohesion: 0.03
Nodes (127): route, check_body_font(), check_destination_empty_states(), check_fonts(), check_index_entrance_motion(), check_initial_visibility(), check_large_display_scale_parity(), check_loading_composition() (+119 more)

### Community 2 - "Postgres Metadata Cache"
Cohesion: 0.05
Nodes (74): _batch_lookup_metadata(), _batch_persist_metadata(), _cleanup_stale_metadata(), _get_db_connection(), Delete spotify_cache rows older than METADATA_CACHE_TTL_DAYS. Called..., Persist newly fetched Spotify metadata in a single INSERT statement. Uses..., Open a single asyncpg connection from DATABASE_URL, or return None. Returns..., Look up cached Spotify metadata for a batch of (artist_norm, album_norm) keys.... (+66 more)

### Community 3 - "Last.fm Client"
Cohesion: 0.05
Nodes (74): check_profile_is_public(), check_user_exists(), fetch_all_recent_tracks_async(), fetch_pages_batch_async(), fetch_recent_tracks_page_async(), Fetch a single page of Last.fm scrobbles with retry and rate limiting. Returns..., Fetch Last.fm pages with controlled concurrency to respect rate limits...., Fetch all Last.fm scrobble pages. Returns (pages, metadata) tuple. Args:... (+66 more)

### Community 4 - "Worktree Guard Tests"
Cohesion: 0.06
Nodes (66): parametrize, Behavior tests for caller-selected worktree comparison references., WT007 keeps the established actionable default-base guidance., Missing custom and local bases never prescribe the origin remote., Replace the fixture PLAYBOOK with controlled Section 3 content., No active batch means no ancestry contract, so a missing base is not an error., WT007 must not mask the higher-value wrong-branch finding., WT004 refresh guidance follows the configured remote-tracking base. (+58 more)

### Community 5 - "Docsync Declarations"
Cohesion: 0.05
Nodes (66): Match, check_values(), collect_declaration_issues(), _compile(), _compile_anchor(), _compile_value(), DeclarationError, _declared_matches() (+58 more)

### Community 6 - "Worktree Guard Core"
Cohesion: 0.08
Nodes (59): base_ref_label(), branch_label(), finish_diagnostics(), identical_tree_remediation(), inspection_failure_diagnostics(), is_display_safe_ref(), issue(), metadata_unavailable_diagnostic() (+51 more)

### Community 7 - "Background Album Job"
Cohesion: 0.06
Nodes (61): patch, background_task(), _detect_spotify_total_failure(), _fetch_and_process(), Return True and set job error if all filtered albums had no Spotify match. Only..., Fetch and process albums in the background for a single job., Run the async fetch pipeline in a dedicated event loop on this thread. On..., create_job() (+53 more)

### Community 8 - "Spotify Client"
Cohesion: 0.06
Nodes (54): fetch_spotify_access_token(), fetch_spotify_album_details_batch(), Return a valid Spotify access token, refreshing from the API if expired., Searches Spotify for a single album and returns its Spotify ID. Optimized: Uses..., Fetches full album details for a list of up to 50 Spotify album IDs in a single..., search_for_spotify_album_id(), get_spotify_limiter(), Return a throttled rate limiter for Spotify API calls. Official limit:... (+46 more)

### Community 9 - "Heatmap Frontend"
Cohesion: 0.09
Nodes (55): addDays(), appendKpi(), clearChildren(), computeStreak(), countToNorm(), drawKpis(), drawLegend(), exportHeaderLayout() (+47 more)

### Community 10 - "Name Normalization"
Cohesion: 0.06
Nodes (54): normalize_name(), normalize_track_name(), Return a simplified version of a track name for matching. Uses NFKC..., Normalizes artist and album names for more accurate matching by cleaning..., fetch_top_albums_async(), Fetch and filter top albums. Returns (filtered_albums, fetch_metadata) tuple...., _page(), asyncio (+46 more)

### Community 11 - "Docsync Rotation Logic"
Cohesion: 0.08
Nodes (36): _sync(), Path, Read the standard three files from the sync_env tmp directory., Passing None as session_lines should not raise., Entries from a completed batch inside current-batch markers should be rotated..., An untagged entry already in the monolith archive should not be duplicated when..., With keep_non_current=0, all non-current entries should rotate., Section 4 with markers but no entries (valid at batch boundary). (+28 more)

### Community 12 - "Gate Theme and Text Checks"
Cohesion: 0.05
Nodes (51): check_shell_scales_with_text(), check_theme_persistence(), check_theme_survives_blocked_storage(), FrontendGateError, _launch_chromium(), _load_playwright(), main(), _parse_args() (+43 more)

### Community 13 - "Docsync Integrity Checks"
Cohesion: 0.07
Nodes (50): check_anchors(), Every citation of a declared shape resolves in the document it names. The..., _files(), Tests for docsync.declarations: DOC009, DOC010 and DOC011. Each check exists..., Reading the key straight out of the mapping raised a bare KeyError. That ends..., The quietest way this file can be wrong, and the reason for a schema. `scans`..., A string where a list belongs is read one character at a time. Every character..., A declaration that visits no documents reports a clean result. `scan` was... (+42 more)

### Community 14 - "Docsync Test Count Authority"
Cohesion: 0.07
Nodes (33): _AmbiguousCount, _dedup_sorted(), latest_test_count_authority(), _latest_test_count_from_entries(), _monotonic_dates(), _newest_count(), Core sync logic for docsync. Every function in this module is pure: no file is..., Sentinel type: the newest entry recording counts quotes several of them. Kept... (+25 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (23): MonkeyPatch, Path, --fix repairs renderer-owned archive formatting without moving entries., Running --fix followed by --check should pass (exit 0)., The CLI supplies the active definition's finite plan to sync., The CLI preserves its malformed-environment exit contract for Git OSErrors., A failed tracked-file query cannot render credential-like stderr., --check must not fail solely because SESSION_CONTEXT.md is missing. (+15 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (28): _aggregate_daily_counts(), Aggregate raw Last.fm page data into a ``{YYYY-MM-DD: count}`` dict. This is a..., _make_track(), asyncio, A range spanning Feb 29 of a leap year produces 366 keys., Tracks at exactly from_date start and to_date end are included., Tracks outside the [from_date, to_date] window are excluded., Empty page list produces a dict of all zeros for the range. (+20 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (44): Heatmap request and rendering sequence diagram, heatmap.js, Heatmap pipeline (partial data is success with warning), heatmap.py, Last.fm API, repositories.py / JOBS, routes.py, worker.py (+36 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (41): check_retired(), _is_struck_through(), A claim that is no longer true is gone from every document that acts. History..., Is the match inside ~~...~~ on this line? A plan step that has been superseded..., Path, ~~this~~ already says the claim is not current. A superseded plan step is often..., The exemption is a guess about intent, so it must be declarable. Treating..., A single claim can be held to a stricter reading than the corpus. (+33 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (22): ActiveBatchState, Entry, Represents one dated execution-log entry block., Parsed batch state signals from PLAYBOOK Section 3., _collect_wp_numbers(), _build_status_block(), _next_wp_number(), Return the next positive WP number for the managed status block. When an active... (+14 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (37): is_runnable(), Path, Report whether a resolved tool path can actually be executed. On POSIX a..., Resolve the sole allowed environment for a normal or linked checkout., resolve_venv(), _checkout(), Path, Behavior tests for primary-checkout virtualenv resolution. (+29 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (37): Batch 21: UI overhaul -- Tailwind + daisyUI migration, scripts/dev/frontend_gate.py browser validation gate, Tailwind CSS v4 + daisyUI strangler migration, tailwind-css-drift pre-commit hook, Batch 10: Gemini audit remediation (non-normalization track), errors.py: ERROR_CODES + SpotifyUnavailableError, _GlobalThrottle + _ThrottledLimiter cross-job rate limiting, Batch 11: Gemini Priority 2 Audit Remediation (SoC, DRY, Architecture) (+29 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (35): CompletedProcess, _active_definition_candidates(), _check_definition_next_wp(), _check_findings_header_count(), _check_section3_next_wp(), _check_unbolded_test_counts(), collect_tracked_paths(), _concrete_references() (+27 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (32): _changed_paths(), _check_root_batch_files(), _collect_current_integrity_issues(), _format_issue(), _get_batch_log_path(), main(), Path, CLI entry point, file I/O, and path constants for docsync. (+24 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (35): parametrize, _playbook(), Behavior tests for PLAYBOOK parsing and lineage classification., Each non-divergent state maps to its deterministic diagnostic codes., Matching trees require approval and lease-protected realignment., Different or unavailable trees use the exact safe WT005 outcome., Only recognized CI may skip branch checks from detached HEAD., Dirty state warns first without erasing the rebase-artifact error. (+27 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (31): main(), _parse_args(), Namespace, Render the read-only ScrobbleScope worktree bootstrap diagnostic. The command..., Parse the comparison ref and explicit offline-mode contract., Render one stable diagnostic and its optional remediation., Print worktree diagnostics and return nonzero when errors exist. Under..., _render() (+23 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (34): A site carries no name, so it is named by its position and its parent., The adversary for the test above: same value, two spellings around it., The gate grades documents it may have just rewritten in memory. Reading from..., Path spelling must not choose stale disk content over rendered state., One malformed fact of each kind, reported together in a stable order., A declaration pointing at a deleted file must not pass silently. Reported..., The check reads every occurrence, not the first one it finds. index.css carries..., A max-width on an element is a width, not a breakpoint. Without the @media... (+26 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (32): build_tailwind(), main(), _parse_args(), Namespace, Verify the toolchain and compile the committed Tailwind stylesheet., Parse the developer-facing build options. Watch never returns, so it cannot be..., Fail when the committed stylesheet does not match a fresh rebuild. The pathspec..., Run the Tailwind build and translate expected failures to exit code 1. (+24 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (31): _apply_post_slice(), _apply_pre_slice(), _classify_exception_to_error_code(), Apply pre-Spotify pre-slicing and playtime cap. Playcount pre-slice: only when..., Truncate results to limit_results if it is a valid integer., Map an exception message to a classified error code, or None. Returns..., parametrize, 5 albums, limit=2, sort_mode='playcount', release_scope='all' -> 2. (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (29): check_container_status(), main(), Start an existing but stopped Docker container. Runs ``docker start <name>``..., Check the Postgres container state and launch Flask. Three-step startup flow:..., Return the Docker container's current state, or None if absent. Runs ``docker..., start_container(), Unit tests for scripts.dev.dev_start. All tests mock subprocess.run so Docker..., GIVEN docker start exits 0 WHEN start_container is called THEN no exception is... (+21 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (28): Barrier, build_parser(), ConcurrentResult, main(), print_aggregate(), print_thread_result(), ArgumentParser, Session (+20 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (29): _doc012_codes(), Behavioural tests for pure live-document integrity analysis., With no authoritative number anywhere, recording one is the only fix., A correction later in the Next action bullet supersedes old prose., The natural bolded header form is not invisible to DOC008., The default runner is never exercised through the CLI fixtures., Return the DOC012 codes raised for one PLAYBOOK body., An entry whose only count is unbolded is skipped in silence today.... (+21 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (29): GET /heatmap_data endpoint, Heatmap request and rendering sequence, heatmap_task, Job slot exhaustion -> 429 retryable, partial_data_warning (partial Last.fm data is success with warning), GET /progress polling loop, app.py application factory, cache.py (+21 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (26): ArtifactSpec, _daisyui_artifact(), _detect_libc(), _download_verified(), ensure_artifact(), ensure_toolchain(), _mark_executable(), Path (+18 more)

### Community 34 - "Community 34"
Cohesion: 0.12
Nodes (16): _check_session_section1_bootstrap_state(), _computed_next_wp(), Return the next WP number and whether the finite plan is complete. Parse the..., DOC007: SESSION_CONTEXT Section 1 must agree on batch and next WP. Section 1 is..., RuntimeError, Raised when deterministic sync cannot proceed safely., SyncError, _find_marker_pair() (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (23): Album thresholds (minimum 10 plays, 3 unique tracks), Centralized card layout, Dark mode theming, Export to CSV and Save as Image actions, Filter Information panel pattern (username, year, filter, thresholds summary), Grouped album table with count badge (reason-grouped rows), Light theme with dark-mode toggle, Listening summary and filter-applied panel (+15 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (23): build_parser(), main(), print_run_summary(), ArgumentParser, Session, Print one run's results in a stable, grep-friendly format. Output includes all..., Create and return the CLI argument parser. Defaults are tuned for local..., Run the cache smoke test and print cache effectiveness hints. Executes... (+15 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (24): collect_integrity_issues(), Return deterministic live-document integrity issues., A count rotated into a per-batch log still decides the header. Close-out purges..., Section 3 naming a different WP than Section 4 computes blocks., Section 3 agreeing with Section 4 raises nothing., A gap the definition plans for does not make DOC007 demand it. Batch 21 absorbs..., --check must not fail on a per-batch log --fix is about to generate., Only concrete matching root files participate in DOC002 uniqueness. (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (22): parametrize, Behavior tests for detached and linked worktree inspection outcomes., Detached CI skips cleanly while detached local work fails safely., A CI checkout skips topology even when PLAYBOOK cannot be parsed., Successful summaries expose topology and the sole qualified tool paths., The public inspection boundary honors a deterministic POSIX topology., test_detached_checkout_stops_before_local_topology_checks(), test_detached_ci_skips_before_playbook_metadata_is_required() (+14 more)

### Community 39 - "Community 39"
Cohesion: 0.08
Nodes (24): No count anywhere is not a mismatch -- there is nothing to agree with. Blocking..., Build one internally consistent active-Batch-21 document set., A Markdown link target is checked as well as a backtick path., The exact root Batch 21 token participates in uniqueness checking., Only the declared Definition path is exempt from generic reference checks., Multiple active definitions create ambiguous ownership., Trimming a no-entry archive prefix must operate on a defensive copy., The optional live session document participates in DOC001 scanning. (+16 more)

### Community 40 - "Community 40"
Cohesion: 0.11
Nodes (23): Bootstrap verification (git status / git log / pytest reconciliation), End-of-session handoff checklist, SESSION_CONTEXT.md, UI and accessibility rules, Account-free operation, AGENT_NOTES.md, AGENTS.md, BATCH21_DEFINITION.md (+15 more)

### Community 41 - "Community 41"
Cohesion: 0.16
Nodes (22): parse_batch_branch(), Parse the active batch and stable branch from PLAYBOOK Section 3., BatchBranch, Describe the active batch and its required worktree branch., _playbook(), parametrize, Section 3 parsing must tolerate ordinary prose and the bold label style., Forgery that needs no line break, so line normalization cannot hide it. One... (+14 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (22): createHiddenInput(), errorContainer, errorSource, errorText, fetchProgress(), liveStatsContainer, progressBar, progressTrack (+14 more)

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (23): Path, Documented templates must not be mistaken for concrete repository files., A command that searches a path is not itself a Markdown path reference., Windows separators never let a missing path evade the gate., Each literal reference has its own actionable diagnostic., Unordered input mappings still produce a stable issue sequence., The tracked-path source is git ls-files and normalizes separators., Git command failures surface safely rather than trusting incomplete paths. (+15 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (22): AI-driven development cycle, Batch 21, Linear-history merge policy (WT004), GitHub Actions Quality Gate, Review-fix push exception (Claude Code and Codex only), check_worktree_alignment.py guard, BATCH21_DEFINITION.md, docs/history/logs/ tagged batch entries (+14 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (21): _bar_feet(), _lockup(), Every page renders and loads exactly one framework stylesheet. WP-2 moves..., The modal opened by itself and its backdrop covered the header. Bootstrap's..., How many albums you list is not part of what counts as listened...., --text-* is Tailwind's font-size namespace, not a colour namespace. The design..., The CSS targets the blades structurally, so the shape is the contract...., Both rules are load-bearing and neither is obvious from its selector. The bar... (+13 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (20): AI-driven development cycle diagram, check_worktree_alignment.py guard, Review-fix push exception (Claude Code and Codex only), WT004 post-merge realignment rule, Documentation and tooling architecture diagram, AGENTS.md rules, BATCH21_DEFINITION.md, doc_state_sync.py (+12 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (18): acquire_job_slot(), Try to acquire a concurrency slot for a new background job. Returns True if the..., Release a previously acquired background job concurrency slot. Safe to call..., Start a daemon thread for a background job. Releases the acquired concurrency..., release_job_slot(), start_job_thread(), GIVEN a semaphore with available capacity WHEN acquire_job_slot is called THEN..., GIVEN a semaphore at capacity WHEN acquire_job_slot is called THEN it returns... (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.15
Nodes (19): _artifact(), Path, Serve payload in one read, then end-of-body, with a Content-Length., A cache miss publishes exactly the bytes covered by the pinned digest., A bad persistent file triggers one verified replacement download., Untrusted replacement bytes never overwrite the previous cache entry., A failed fetch leaves neither executable bytes nor a partial download., A connection that closes mid-body must not be blamed on the digest. A short... (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (16): create_app(), Application factory for ScrobbleScope., client(), csrf_app_client(), fresh_job_slots(), fixture, MonkeyPatch, Path (+8 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (17): check_current_validator_failure_replaces_old_verdict(), check_private_profile_is_blocked(), check_stale_validator_failure_is_discarded(), check_touch_targets(), check_validation_feedback(), check_validator_outage_is_recoverable(), An older failed request cannot clear a newer same-name verdict. Two blur..., A current network failure cannot leave an older invalid verdict visible. (+9 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (16): fetch_csrf_token(), Session, Shared HTTP transport layer for ScrobbleScope integration test scripts. This..., Submit a search job and return the ``job_id``. Performs the two-step flow: 1...., Fetch the CSRF token from the index page. GETs ``base_url/`` (the index page)..., submit_job(), GIVEN a POST response that contains no <script id="scrobble-config"> block WHEN..., GIVEN a POST response containing a scrobble-config block whose JSON has no... (+8 more)

### Community 52 - "Community 52"
Cohesion: 0.15
Nodes (9): When entries are in reverse chronological file order, the last entry in the..., The top side-task full-suite result supersedes the Batch WP baseline., A focused-only result cannot become the repository test authority., Wrap entry_body_lines inside a minimal PLAYBOOK with Section 4 markers., Flat playbook with no Section 4 markers returns None., Bold test count in a current-batch entry body is extracted., Entry with no bold count produces None., With two entries inside markers, the newest (last appended) entry's count is... (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (17): parametrize, The header bar and its stylesheet are on every page, migrated or not., The stylesheet is only half of Bootstrap. A migrated page that still loads the..., data-bs-* is Bootstrap's JS API, and it fails silently without it. A leftover..., CSS cannot stop SMIL, so prefers-reduced-motion never reaches it. An <animate>..., Stripping SMIL without a wrapper leaves a mark that never moves. The animation..., These land a commit before the markup that reads them. Tailwind v4 emits a..., The wrapper centres and spaces whatever a page adds after the content.... (+9 more)

### Community 54 - "Community 54"
Cohesion: 0.13
Nodes (16): GH_TOKEN fine-grained PAT authentication for the gh CLI, Local dev setup: dev_start.py one-command startup with ss-postgres Docker container, Single worker, multiple threads: Gunicorn --workers 1 --threads 4, Spotify cache TTL: 30 days from last fetch, hits do not refresh updated_at, Windows asyncio ProactorEventLoop guard in background_task, Heatmap empty-cell colours #e8e2d6 light / #262230 dark, Fly.io deployment with Postgres add-on; init_db.py as release_command, Global rate limiting via _GlobalThrottle in utils.py (+8 more)

### Community 55 - "Community 55"
Cohesion: 0.15
Nodes (16): Adobe Fonts kit rwy8ghw type stack (five families, weights 300/400/700), F-STYLE-1: cite by name or rule, never by line number, Exactly nine daisyUI components; stepper/disclosure/segmented control hand-built, pre-commit --all-files does not see untracked files; git add -N required, Strangler page-by-page migration (legacy_css block), scripts/dev/tailwind_build.py -- Tailwind standalone CLI build, tailwind-css-drift pre-commit hook (rebuild then diff), Batch 21 WP-2 base shell plan (+8 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (16): _normalize_libc(), platform_key(), RuntimeError, Map a reported C runtime name onto Tailwind's asset vocabulary...., Return the official Tailwind asset key for one supported host. Explicit values..., Report a safe, actionable toolchain or build failure., TailwindBuildError, parametrize (+8 more)

### Community 57 - "Community 57"
Cohesion: 0.16
Nodes (10): Partition all entries in monolith_lines by batch tag. Returns: remaining_lines:..., _split_archive(), _extract_entry_batch(), Extract the batch number from an entry heading, if present., GIVEN archive with a Batch 10 tagged entry, WHEN split, THEN the entry is in..., GIVEN archive with an untagged entry, WHEN split, THEN batch_groups is empty..., GIVEN archive with both tagged and untagged entries, WHEN split, THEN each..., TestSplitArchive (+2 more)

### Community 58 - "Community 58"
Cohesion: 0.23
Nodes (14): clampToBounds(), clearRegistrationState(), clearReleaseYearValidation(), clearYearValidation(), countOf(), getDecadeStart(), hasNonNumeric(), nudge() (+6 more)

### Community 59 - "Community 59"
Cohesion: 0.20
Nodes (6): Validate SECRET_KEY strength at startup. Raises RuntimeError in production if..., _validate_secret_key(), ensure_api_keys(), Raise ``RuntimeError`` if required API keys are missing., Tests for app factory startup secret-key validation (WP-4)., TestValidateSecretKey

### Community 60 - "Community 60"
Cohesion: 0.13
Nodes (15): Findings Archive (FINDINGS_ARCHIVE.md), Batch 18 Execution Log, Batch 18, Batch 20 Execution Log, Batch 20, F-ID format and findings rotation policy, shared rate limiter (_GlobalThrottle), heatmap route handlers (POST /heatmap_loading, GET /heatmap_data) (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (15): Batch 11 Execution Log, Batch 11, Batch 12 Execution Log, Batch 12, Batch 13 Execution Log, Batch 13, Batch 14 Execution Log, Batch 14 (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.18
Nodes (14): SESSION_CONTEXT.md (dashboard), Batch 21 status (WP-0..WP-4 done, WP-5 next), MAX_ACTIVE_JOBS concurrency cap, RotatingFileHandler WinError 32 risk on Windows, AGENT_NOTES.md (owner context), Adobe Fonts kit rationale (avoid AI-generated look), Single worker, multiple threads (Gunicorn --workers 1 --threads 4), Windows asyncio ProactorEventLoop guard (+6 more)

### Community 63 - "Community 63"
Cohesion: 0.16
Nodes (13): mermaid.instructions.md (Mermaid AI Skills), Validate Mermaid before presenting rule, Anti-duplication rule: each fact has one owner document, A dated audit report is never edited; corrections go in a new top section, scripts/doc_state_sync.py -- docsync state sync and integrity, Session Bootstrap read order (AGENTS.md-owned), docs/AGENT_DOC_MAP.md (document map), docs/ARCHITECTURE.md (diagram index) (+5 more)

### Community 64 - "Community 64"
Cohesion: 0.20
Nodes (14): Background job pipeline (slot -> thread -> event loop -> JOBS), MAX_ACTIVE_JOBS=5 load-test rationale, ERROR_CODES classification table, _aggregate_daily_counts, _fetch_and_process_heatmap, heatmap_task (thread entry point), ProactorEventLoop on Windows for asyncpg, HEATMAP_WINDOW_DAYS=365 single source (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.16
Nodes (14): Codex review process (twelve rounds, thirty threads, thumbs-up merge signal), Graphify advisory passes (five confirmed defect classes, hardened at shared seams), Owner's Claude Design audit (UI Audit v3) -- source of Batch 21 scope, F-B19-4: front-end UI audit notes -- basis of BATCH21_DEFINITION.md, F-B20-4: UI overhaul driven by owner audit (basis of Batch 21), F-B21-11: welcome modal covers the header theme toggle (resolved by WP-3), Batch 21: UI overhaul -- Tailwind + daisyUI migration (active), BATCH21_DEFINITION.md (repo root, active) (+6 more)

### Community 66 - "Community 66"
Cohesion: 0.21
Nodes (7): _playbook_lines_without_entry_blocks(), Blank dated Section 4 history without shifting source lines., _parse_entries(), A bare ### line without date-dash-title format is rejected., A ### line with a date but no ' - ' separator is rejected., ### lines inside fenced code blocks are ignored, not rejected., TestParseEntries

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (13): Batch 9 Audit Remediation Plan (2026-02-20), Batch 8 Execution Log, Batch 8, SWE Principles Audit (2026-06-22), Routes SoC Audit (2026-02-21), Test Quality Audit (2026-02-21), scrobblescope package, scrobblescope/lastfm.py (+5 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (11): Deferred / future-batch candidates block (Batch 18/19 audits), F-B21-14: heatmap has no path to its data that is not colour, F-B21-15: heatmap stays on the index page; split waits, F-DOCSYNC-1: ENTRY_BATCH_RE too loose, F-DOCSYNC-2: STATUS block misreports current batch between batches, F-DOCSYNC-3: close-out entries route to the monolith, not the batch log, FINDINGS severity key (P0/P1/P2/Info/Deferred), Batch 21 WP-5: results leaderboard (next) (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (6): _parse_active_batch_state(), When a batch is marked both complete and active, active wins., TestParseActiveBatchStateConflicting, When only completed batches exist and no 'not yet defined' guard, current_batch..., If current_batch matches next_undefined, current should be None., TestParseActiveBatchState

### Community 70 - "Community 70"
Cohesion: 0.21
Nodes (13): spotify_token_cache shared dict, check_profile_is_public, check_user_exists, fetch_all_recent_tracks_async, fetch_pages_batch_async, fetch_recent_tracks_page_async, route /validate_user, fetch_spotify_access_token (+5 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (13): _definition_with_status(), A definition naming the same next WP as PLAYBOOK raises nothing., A stale claim in the definition blocks at its own line., No parseable claim means no mismatch -- silence beats a false hit., The claim is the WP attached to 'is the next', not the first WP seen. A status..., With no current-batch entries there is no computed value to compare., The renderer's lowest-missing rule decides what 'next' means., test_doc007_agreeing_next_wp_claims_are_clean() (+5 more)

### Community 72 - "Community 72"
Cohesion: 0.21
Nodes (11): .flake8 config, Pull Request Template, PR checklist (pytest, pre-commit, docsync, PLAYBOOK entries), Quality Gate workflow (test.yml), CI frontend gate step, CI pre-commit step (SKIP worktree-alignment), Tailwind CSS digest diagnostic step, doc-state-sync-check hook (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.18
Nodes (12): scripts/dev/frontend_gate.py -- Playwright browser gate, WP-3 owner decisions table (full index migration, WP-6 absorbed, no heatmap.html, mode pills, SMIL strip, keep /validate_user), F-AUDIT-1: dark-mode toggle placement on mobile (resolved by WP-2), F-B18-12: mode pills differ in width (resolved by WP-3), F-B21-10: every error page reports 400 whatever the real status, F-B21-2: three dormant Tailwind seams WP-2 meets at once (resolved), F-B21-3: 115 dependency advisories; unused packages ship to production, F-B21-4: four screens where the design bundle contradicts itself (+4 more)

### Community 74 - "Community 74"
Cohesion: 0.21
Nodes (12): Defect: gate measures set_viewport_size geometry no real browser window has, --index-wide-scale / CSS zoom viewport-scaling path, Owner ruling 2026-09-01: the form widens then locks; it is never zoomed, Structured progress phase contract ({key,label,unit,current,total}) with backward-compatible /progress, Acceptance gate: realistic window geometry in either engine (Chromium == Firefox within 0.1px), Defect: scale formula divides by design viewport (1080), height term always wins, @theme static prevents token pruning in Tailwind v4, 3fr 4fr wide index split with 28rem form cap (1200px+) (+4 more)

### Community 75 - "Community 75"
Cohesion: 0.22
Nodes (11): AGENT_NOTES.md as owner of owner context and local setup facts, AGENTS.md as owner of repository rules, Batch and work-package structure as a lightweight SDLC, Definition of done written before work starts, not inferred after, doc_state_sync.py: deterministic rotation, dedup, status-block refresh as a script not a prompt, External memory architecture for amnesiac LLM agents, HANDOFF_PROMPT.md as owner of session start and handoff procedure, docs/history archive: definitions, logs, findings, reports; nothing deleted (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (11): Button component spec, One primary button per screen rule, 16px mobile input rule (iOS auto-zoom), Input component spec, Select component spec, HeatmapStrips mobile layout (four 13-week strips), HeatmapFrame component spec, Layout-independent export rule (CSV/JPEG always 53x7 grid) (+3 more)

### Community 77 - "Community 77"
Cohesion: 0.20
Nodes (11): Batch 16 Execution Log, Batch 16, Batch 7 Execution Log, Batch 7, init_db.py, persistent Spotify metadata cache (asyncpg/Postgres), scripts/dev/dev_start.py, scripts/testing/_http_client.py (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.27
Nodes (7): _merge_entries_into_log(), Merge new_entries into an existing per-batch log, deduplicating by fingerprint...., Build a minimal Entry with a properly computed fingerprint., GIVEN no existing log, WHEN an entry is merged, THEN a batch header line is..., GIVEN an entry already in the log, WHEN merged again with same entry, THEN the..., GIVEN an older and a newer entry, WHEN merged, THEN the newer date appears..., TestMergeEntriesIntoLog

### Community 79 - "Community 79"
Cohesion: 0.22
Nodes (11): _batch_lookup_metadata, _batch_persist_metadata, _cleanup_stale_metadata, spotify_cache table contract, background_task, _get_user_friendly_reason, _matches_release_criteria, _PLAYTIME_ALBUM_CAP=500 rationale (+3 more)

### Community 80 - "Community 80"
Cohesion: 0.18
Nodes (11): parametrize, DOC001 governs repository-relative references, so nothing else may block., Wildcard-like paths are documentation patterns, not concrete files., A long number or hex-alphabet word is not a pinned commit identity., Telling an author to remove a hash they never wrote is not actionable., Missing or duplicate Branch metadata is volatile-document drift., test_active_definition_requires_exactly_one_branch_field(), test_branch_metadata_remediation_matches_the_actual_violation() (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (10): Precedence: README canonical over reference docs, Generic AI-generated UI fixes (accent word, eyebrows, aphorism headlines), Second pass on the UI audit, Single centred index column (challenge split hero), Unmatched grouping bug: per-album reason sentence vs reason code, Component inventory (actions, forms, navigation, data, feedback, heatmap), Logo bars via CSS keyframes, not SMIL (transform-box: view-box, origin 0 63.5px), No icon system (deliberate) (+2 more)

### Community 82 - "Community 82"
Cohesion: 0.27
Nodes (5): _render_archive(), Empty prefix still renders entries correctly., A stale side-task archive preamble cannot survive a renderer pass., Per-batch logs keep their caller-supplied prefix., TestRenderArchive

### Community 83 - "Community 83"
Cohesion: 0.20
Nodes (10): The hand-maintained dashboard cannot name a stale next package., The dashboard's sole active row must name PLAYBOOK's active batch., The expected active batch and next package raise no dashboard issue., Close-out rejects next-WP claims after the finite plan is complete., Build the hand-maintained SESSION_CONTEXT Section 1 status table., _session_with_status_rows(), test_doc007_agreeing_session_section1_claim_is_clean(), test_doc007_all_planned_wps_reject_stale_numeric_claims() (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.20
Nodes (10): Return the stylesheet with every /* */ block removed. Both directions need..., Page pills use the typeface specified by the WP-4 design., Hero and header letterforms must remain legible in dark mode., The pinwheel's SMIL is gone, so shell.css owns every part of it. Five..., Return every selector in a rule whose body sets animation: none. Comments are..., _selectors_that_cancel_animation(), test_migrated_wordmarks_use_theme_ink_for_letterforms(), test_shared_navigation_uses_input_mono_narrow() (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (9): Module dependency graph (Section 4), Known open issues: CSP dropped as YAGNI, Celery/Redis out of scope, orchestrator split F-B20-2, Load testing findings 2026-03-04: shared Last.fm phase averages ~10/N req/s across jobs, Owner preferences: concise responses, no emojis, explain why, Firefox local testing, Enforced software principles (DRY, SoC, SRP, KISS, DI, Clean Architecture), Testing pyramid: mocked unit tests base, route integration middle, owner-driven E2E top, Acyclic module graph: leaf modules import nothing internal; routes.py highest-level, Bounded concurrency: MAX_ACTIVE_JOBS BoundedSemaphore rejects excess requests (+1 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (9): Any, poll_until_complete(), Poll ``/progress`` until the job completes or a timeout fires. Repeatedly GETs..., GIVEN a mock session whose first poll returns progress=100 WHEN..., GIVEN a mock session whose GET returns HTTP 500 WHEN poll_until_complete is..., GIVEN a mock session that always returns progress=50 and a mocked time that..., test_poll_raises_on_unexpected_status(), test_poll_raises_timeout_when_deadline_exceeded() (+1 more)

### Community 87 - "Community 87"
Cohesion: 0.22
Nodes (9): check-merge-conflict pre-commit hook, detect-private-key pre-commit hook, Batch 17 Execution Log, Batch 17, Flask-Talisman security headers, .github/dependabot.yml, .github/PULL_REQUEST_TEMPLATE.md, pip-audit security audit CI step (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.36
Nodes (9): Two-tier rate limiting (global throttle + per-loop limiter), _run_spotify_batch_detail_phase, fetch_spotify_album_details_batch, search_for_spotify_album_id, get_lastfm_limiter, get_spotify_limiter, _GlobalThrottle cross-thread rate cap, retry_with_semaphore (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.25
Nodes (9): docsync mechanism (doc_state_sync.py, DOC001-DOC011, STATUS block, rotation), F-B21-12: four pinned CI actions target deprecated Node runtime, F-B21-13: bootstrap state lives in three files, only one gated (closed by DOC007/DOC008), F-B21-9: findings-to-issues mirror is manual, F-DOCSYNC-7: _latest_test_count_from_entries has no production caller, GitHub issues mirror of open findings (manual, per F-B21-9), Batch 14: Doc hygiene (archive restructure, docsync package, per-batch routing), PR #170: guard and docsync source settlement (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.22
Nodes (8): CSRF protection (Flask-WTF), Batch 10 Execution Log, Batch 10, Batch 9 Execution Log, Batch 9, playtime album cap (_PLAYTIME_ALBUM_CAP), requirements-dev.txt, thread-safe REQUEST_CACHE (_cache_lock)

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (9): F-B18-11: heatmap Last.fm page fetch is rate-limit bound, F-B19-3: last.timer aggregate endpoints not a drop-in heatmap speedup, F-B20-2: orchestrator.py second-pass decomposition (promoted from F-B18-1), F-FEATURE-2: listening heatmap (shipped in Batches 18/19), F-SWE-7: utils.py holds five unrelated concerns, Batch 18: Scrobble heatmap iteration 1, Heatmap fetch speed is rate-limit bound (F-B18-11 single source), last.timer aggregate endpoints are not a drop-in heatmap speedup (F-B19-3) (+1 more)

### Community 92 - "Community 92"
Cohesion: 0.28
Nodes (5): _fingerprint(), _normalize_block(), When two entries have the same fingerprint, only the newest survives., TestDedupSorted, TestFingerprintNormalization

### Community 93 - "Community 93"
Cohesion: 0.22
Nodes (9): _declared(), _local_sheets(), Path, Return the repository file behind every href that names a local sheet., Return every custom property the stylesheet defines., Return every custom property the stylesheet reads with no fallback. A var()..., An undefined var() with no fallback voids the whole declaration. It fails..., _read_without_fallback() (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.25
Nodes (6): create_app, module-level app instance (gunicorn compat), _validate_secret_key, init_db.main (spotify_cache schema), run.py dev launcher, routes blueprint (main)

### Community 95 - "Community 95"
Cohesion: 0.29
Nodes (8): scripts/dev/check_worktree_alignment.py -- worktree guard, F-DOCSYNC-5: operational doc metadata drifted across path and branch changes (resolved), F-WORKTREE-1: rebase merges leave linked branches history-diverged (resolved), F-WORKTREE-2: linked worktrees cannot use relative virtualenv path (resolved), F-WORKTREE-3: guard boundaries outside the design decision table, F-WORKTREE-4: three guard files exceed their directory peer caps, F-WORKTREE-5: display-unsafe branch candidates dropped before conflict check (resolved), PR #169: repository-integrity gate + read-only worktree guard

### Community 96 - "Community 96"
Cohesion: 0.25
Nodes (8): No 500/600 weights rule (300/400/700 only), styles.css single entry point (imports only), elevation.css (borders do the work, three shadows), motion.css quiet durations + reduced-motion collapse, Pinwheel cycle as the one motion exception, spacing.css 4px base seven-step ladder, Gotham gets numbers, serif gets words, typography.css five font roles and type scale

### Community 97 - "Community 97"
Cohesion: 0.25
Nodes (4): Minimal urlopen stand-in: a context manager exposing headers and read. A real..., IncompleteRead subclasses HTTPException, so it escapes an OSError catch., _StubResponse, test_an_incomplete_read_is_translated_not_raised_raw()

### Community 98 - "Community 98"
Cohesion: 0.14
Nodes (8): The CLI has to be able to report it, or the gate ends in a traceback. Both..., Two empty captures must not agree and make a content-free value green., The quiet half of the per-line defect, and the reason it matters. A file that..., The check must be silent on correct code, or it stops being read., test_a_declaration_fault_reaches_the_cli_as_a_sync_error(), test_a_wrapped_occurrence_that_drifts_is_not_hidden_by_an_unwrapped_one(), test_an_empty_captured_value_is_refused(), test_sites_that_all_state_the_value_report_nothing()

### Community 100 - "Community 100"
Cohesion: 0.29
Nodes (7): Verified tooling gaps and dispositions: no webapp-testing skill, hook exclusion, CI Node absence, Frontend asset build: pinned Tailwind standalone CLI with SHA-256 verification, no Node project, Tailwind source(none) scan scoping (F-B21-8), Units rule: rem for type and spacing, px for fine detail a reader never scales, Retire Bootstrap entirely in Batch 21 to resolve the CDN provider split, GitHub Actions Quality Gate: pinned Tailwind rebuild, pre-commit, pytest coverage, pip-audit, Tailwind CSS 4 + daisyUI 5 migration toolchain (Batch 21)

### Community 101 - "Community 101"
Cohesion: 0.29
Nodes (7): Adobe Fonts kit rwy8ghw, Design tokens (port tokens/*.css into Tailwind theme), ScrobbleScope front-end design handoff README, Tailwind + DaisyUI stack decision (not React), Target visual language (warm palette + editorial type), akzidenz-grotesk-next-conden kept as licensing hedge, fonts.css Adobe kit rwy8ghw verified contents

### Community 102 - "Community 102"
Cohesion: 0.38
Nodes (7): Index page dark mode screenshot with decade filter and thresholds panel, Define Album Thresholds toggle with Minimum Track Plays (10 plays) and Minimum Unique Tracks (3 tracks), Dark Mode toggle, Album Release Date Filter: Choose Decade dropdown (1980s), Filter Your Album Scrobbles form card, ScrobbleScope wordmark with tagline 'Your top albums by year, visualized', Sort By: Play Count selector

### Community 103 - "Community 103"
Cohesion: 0.33
Nodes (7): cleanup_expired_jobs, create_job, get_job_context, JOBS shared in-memory job store, _get_validated_job_context, _LATEST_ALBUM_JOB / _LATEST_HEATMAP_JOB session keys, route /progress

### Community 104 - "Community 104"
Cohesion: 0.29
Nodes (5): _GlobalThrottle, Thread-safe throttle enforcing a global rate limit across all event loops. Each..., Return seconds to wait before the next call is allowed. Thread-safe. Advances..., GIVEN a _GlobalThrottle at rate=10 (0.1s minimum interval) WHEN next_wait() is..., test_global_throttle_serializes_rapid_calls()

### Community 105 - "Community 105"
Cohesion: 0.29
Nodes (6): parametrize, Behavior tests for sanitized worktree-guard subprocess execution., The real runner exposes return code and both captured text streams., Process-launch failures omit secrets and suppress their exception chain., test_run_git_returns_captured_process_data(), test_run_git_sanitizes_process_failures()

### Community 106 - "Community 106"
Cohesion: 0.33
Nodes (6): The Adobe kit is what keeps this UI from looking generated, Adobe Fonts kit rwy8ghw adopted as the type stack (self-hosted plan reversed 2026-08-22), Five Adobe font families with role map: akzidenz-grotesk-next-pro, instrument-serif, gotham, input-mono, input-mono-narrow, No 500/600 weights: font-weight-medium and font-weight-semibold deleted from @theme, Owner design decisions of 2026-08-21: type, authority, import scope, session scope, Theme marker decision: data-theme=dark on the html element

### Community 107 - "Community 107"
Cohesion: 0.33
Nodes (6): Batch 21 tooling map: skills sources, MCP servers, per-WP tool assignments, Claude Code skills: scrobblescope-bootstrap and pr-bot-triage, ScrobbleScope development methodology documentation, On rejecting code review suggestions with causal knowledge preserved, Worktrees, rebase merges and branch lineage diagnosis, Shared-document multi-agent development methodology

### Community 108 - "Community 108"
Cohesion: 0.33
Nodes (6): Six-step audit lifecycle (charter to retirement), docs/SWE_AUDIT_CHARTER.md (retired), 13-module grading matrix with depth tiers, Read-only audit executor contract, SWE principles audit report at docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md, SWE audit charter retired status

### Community 109 - "Community 109"
Cohesion: 0.33
Nodes (5): HeatmapFrameProps, HeatmapGridProps, HeatmapLegendProps, HeatmapStat, HeatmapStripsProps

### Community 110 - "Community 110"
Cohesion: 0.33
Nodes (6): Theme class goes on <html>, Curated subset import (61 of 207 files), data-theme="dark" marker override, Owner-approved overrides table, .prompt.md dual meaning (component spec vs authoring prompt), RECONCILIATION.md override list

### Community 111 - "Community 111"
Cohesion: 0.33
Nodes (6): ASCII-only authoring rule exempted for the verbatim design snapshot, docs/design/README.md canonical design specification, Design reconciliation override list, Curated text-only design import: 61 of 207 source project files, assets excluded, Design authority precedence: canonical README over reference docs, with recorded overrides, Five-step radius scale: 4px, 8px, 10px, 14px, 999px pills

### Community 112 - "Community 112"
Cohesion: 0.33
Nodes (6): Batch 19 Execution Log, Batch 19, heatmap frame / headline / KPIs / legend surface, unframed heatmap loading panel (heatmap-loading-panel), heatmap mobile vertical renderer (renderHeatmapMobile), heatmap spinner wrapper (fixed flex centering box)

### Community 113 - "Community 113"
Cohesion: 0.33
Nodes (6): F-B21-17: a third of the batch's review comments were one fact written twice, F-B21-18: browser JavaScript has no automated unit coverage, F-B21-19: heatmap mobile and day-detail behaviour drifted from design, F-B21-25: every gate runs at commit time, so the session is unguarded, F-MAS-2: no automated JS tests, F-STYLE-1: repository prose is denser than it needs to be

### Community 114 - "Community 114"
Cohesion: 0.33
Nodes (6): check_index_design_tokens(), check_theme_tokens(), _computed_colour(), Resolve a CSS value through a probe element to a computed rgb() string...., --bars-color aliases the theme primary, and no cool-grey survives., Rendered index states use the canonical status and radius tokens.

### Community 115 - "Community 115"
Cohesion: 0.40
Nodes (6): NFKC normalization preserves non-Latin scripts, normalize_name, normalize_track_name, fetch_top_albums_async, _run_spotify_search_phase, add_job_unmatched

### Community 116 - "Community 116"
Cohesion: 0.33
Nodes (4): Tests for the synchronous thread entry point., release_job_slot is called even when the task succeeds., release_job_slot is called even when the async pipeline explodes., TestHeatmapTask

### Community 117 - "Community 117"
Cohesion: 0.33
Nodes (4): Verify the no_scrobbles_in_range error code is registered correctly., The error code is present in ERROR_CODES with correct fields., The message template accepts a username substitution., TestErrorCode

### Community 118 - "Community 118"
Cohesion: 0.33
Nodes (6): Return the href of every stylesheet link in the rendered page., Two frameworks collide on .btn and .card; none strips the page's theme., A migrated page must not silently fall back to the legacy stack., _stylesheets(), test_each_page_loads_the_framework_its_markup_is_written_for(), test_every_page_loads_exactly_one_framework_stylesheet()

### Community 119 - "Community 119"
Cohesion: 0.50
Nodes (5): .docsync.toml (declared duplications), the single 860px breakpoint, the light muted text token (#6c6676), the 12px small-label floor, wide-desktop scale baseline and cap (1.075)

### Community 120 - "Community 120"
Cohesion: 0.40
Nodes (5): app_context_processor, inject_current_year(), inject_page_navigation(), Inject ``current_year`` into all Jinja2 templates., Build the shared, canonical page navigation for the current request.

### Community 121 - "Community 121"
Cohesion: 0.40
Nodes (5): app_errorhandler, internal_error(), page_not_found(), Handle 404 errors with a nice error page, Handle 500 errors with a nice error page

### Community 122 - "Community 122"
Cohesion: 0.40
Nodes (5): Owner's Impeccable Live annotation pass (paused, resume before WP-5), templates/partials/_loading.html (framework-neutral shared wait panel), F-B21-24: the index does not scale up on large displays, Batch 21 WP-4: unified loading + polling state machines (done; owner-review remediation next), docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md

### Community 123 - "Community 123"
Cohesion: 0.40
Nodes (5): MonkeyPatch, musl hosts report no libc version, so its loader is the only signal., A reported runtime is authoritative; the loader probe is a fallback., test_detect_libc_prefers_the_reported_runtime_over_the_loader_probe(), test_detect_libc_reads_the_musl_loader_when_python_reports_nothing()

### Community 124 - "Community 124"
Cohesion: 0.40
Nodes (4): parametrize, Guard the verbatim design import against in-place edits...., The snapshot must match its import digest byte for byte., test_imported_design_file_is_unedited()

### Community 125 - "Community 125"
Cohesion: 0.50
Nodes (3): load_dotenv anchored to file path, DATABASE_URL captured at import time, _get_db_connection

### Community 126 - "Community 126"
Cohesion: 0.50
Nodes (4): CI wip/** push triggers, Batch 15 Execution Log, Batch 15, docsync heading validation (### entries)

### Community 127 - "Community 127"
Cohesion: 0.83
Nodes (4): Four-blade expand-and-rotate loading animation (4 cardinal blades, 2.5s cycle, 1080-degree rotation), Pinwheel brand mark (ScrobbleScope wordmark motif), SMIL animation (animateTransform-based SVG motion), ScrobbleScope pinwheel expanded SVG (docs image)

### Community 128 - "Community 128"
Cohesion: 0.50
Nodes (4): Batch 0: Baseline freeze + approval parity suite, Batch 1: Proper upstream failure state + retry UX, Batch 2: Personalized minimum listening year from registration, Batch 3: Remove nested thread pattern

### Community 129 - "Community 129"
Cohesion: 0.67
Nodes (4): Ranked album results table (concept), Dark theme UI (concept), Results dark modal screenshot, Unmatched albums filter modal (concept)

### Community 130 - "Community 130"
Cohesion: 0.50
Nodes (4): F-B21-6: year gate reads host-local time, fetch window reads UTC, F-SWE-1: SWE-principles audit (executed 2026-08-20), F-SWE-2: album year window built from naive datetimes (resolved), Batch 21 WP-0: baseline freeze + definition

### Community 132 - "Community 132"
Cohesion: 0.67
Nodes (3): Wordmark and logo mean the SVG logotype, not the UI type stack; bars are a visualiser, Wordmark typeface: Oblong Regular by WAPType, outline geometry in the SVG, Lockup asset derivation with viewBox 0 0 453 74 deviation from canonical 0 0 453 69

### Community 133 - "Community 133"
Cohesion: 0.67
Nodes (3): config.py omitted from diagram (edge-crossing rationale), Flask + Jinja2 monolith, Full-stack application architecture

### Community 141 - "Community 141"
Cohesion: 0.67
Nodes (3): fonts.css design tokens, Adobe Fonts kit rwy8ghw, typography.css design tokens

### Community 142 - "Community 142"
Cohesion: 0.67
Nodes (3): Worktree Guard Report (2026-07-15), shared .venv in primary checkout (linked-worktree reuse), worktree alignment guard (scripts/dev/check_worktree_alignment.py)

### Community 143 - "Community 143"
Cohesion: 0.67
Nodes (3): F-B21-21: index hero wordmark ignores the theme (resolved same day), F-B21-22: theme follows system only until toggle first used, F-B21-23: inline marks diverge from design contract on colour

### Community 145 - "Community 145"
Cohesion: 0.67
Nodes (3): clear_cache(), fixture, Clear REQUEST_CACHE before and after each test to prevent state bleed.

## Ambiguous Edges - Review These
- `Listening Heatmap mode` -> `Spotify metadata enrichment`  [AMBIGUOUS]
  PRODUCT.md | relation: conceptually_related_to

## Knowledge Gaps
- **322 isolated node(s):** `ButtonProps`, `AlbumRowProps`, `StatBlockProps`, `TagProps`, `UnmatchedItem` (+317 more)
  These have <=1 connection - possible missing edges or undocumented components.
- **99 thin communities (<3 nodes) omitted from report** -- run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Listening Heatmap mode` and `Spotify metadata enrichment`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `_reach_state()` connect `Community 50` to `Frontend Browser Gate`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `GuardError` connect `Worktree Guard Core` to `Community 41`, `Community 50`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `create_app()` connect `Community 49` to `Frontend Browser Gate`, `Community 59`, `Community 45`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 133 inferred relationships involving `patch` (e.g. with `test_check_container_status_raises_on_timeout()` and `test_check_container_status_raises_on_unexpected_error()`) actually correct?**
  _`patch` has 133 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ButtonProps`, `AlbumRowProps`, `StatBlockProps` to the rest of the system?**
  _322 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Album Results Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.013982050070854983 - nodes in this community are weakly interconnected._