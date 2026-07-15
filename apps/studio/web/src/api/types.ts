/** Typed mirror of the SceneSmith Studio server (apps/studio/server/main.py). */

export interface RunWindow {
  actual_start: string
  total_duration_hours?: number
  no_new_major_slice_after: string
  hard_closeout: string
  owner_extension_recorded_at?: string
  scope?: string
  simulation_only?: boolean
  hardware_authority?: string
  external_compute_authority?: string
  brev_authority?: string
}

export interface LedgerFrontMatter {
  training_lock?: string
  run_window?: string
  run_state?: string
  current_milestone?: string
  current_task?: string
  completed?: string
  evidence?: string
  remaining?: string
  owner_authority?: string
  blockers?: string
  next_step?: string
}

export interface VerifiedBoundary {
  brief_id?: string
  commit?: string
  reviewer_decision_id?: string
  summary?: string
}

export interface StatusResponse {
  data_root: string
  run_window: RunWindow | null
  current_task: string | null
  current_milestone: string | null
  latest_verified_boundary: VerifiedBoundary | null
  ledger: LedgerFrontMatter
  recent_reviewer_decisions: string[]
  recent_briefs: string[]
}

export type EpisodeSource = 'expert' | 'policy_trace'

export interface EpisodeSummary {
  id: string
  source: EpisodeSource
  seed: number | null
  seed_role?: string | null
  adapter_id?: string | null
  frame_count: number | null
  strict_success?: boolean | null
  maximum_anchor_lift_m?: number | null
  identity_sha256?: string | null
  outcome?: { strict_success?: boolean; result?: string; grade?: string }
  artifact: string
  mirror_video: string | null
}

export interface EpisodesResponse {
  count: number
  episodes: EpisodeSummary[]
}

export interface TimelineFrame {
  frame_index: number
  /** policy traces */
  phase?: string | null
  candidate_strict_contact?: boolean | null
  anchor_z_m?: number | null
  /** expert episodes */
  task_phase?: string | null
  control_mode?: string | null
}

export interface ExpertOutcome {
  strict_success?: boolean
  failed_gate_margins?: string[]
  gate_margins?: Record<
    string,
    { comparison: string; margin: number; measured: number; passed: boolean; threshold: number }
  >
  [key: string]: unknown
}

export interface EpisodeDetail {
  id: string
  source: EpisodeSource
  timeline: TimelineFrame[]
  /** expert */
  episode_spec?: { seed?: number; planar_offset_m?: number[]; yaw_offset_rad?: number } | null
  outcome?: ExpertOutcome | null
  frame_count?: number
  camera_views?: string[]
  /** policy trace — flat signed-trace fields (hashes, flags, diagnostics…) */
  mirror_video?: string | null
  adapter_id?: string
  task_id?: string
  schema_version?: string
  seed?: number
  seed_role?: string
  [key: string]: unknown
}

export interface WorkcellManifest {
  scene_id: string
  schema_version?: string
  task_prompt?: string
  cube_count?: number
  tray_count?: number
  all_cubes_stable?: boolean
  cube_stability?: Record<string, { settle_displacement_m: number; stable: boolean }>
  previews: Record<string, string>
  spec_path?: string
  spec_sha256?: string
  scene_xml?: string
  scene_xml_sha256?: string
  settle_steps?: number
  stability_tolerance_m?: number
  authority?: string
  [key: string]: unknown
}

export interface WorkcellsResponse {
  count: number
  workcells: WorkcellManifest[]
}

export interface ResultGate {
  schema_version: string
  decision?: string
  gate_b_one_batch_memorization_passed?: boolean
  final_to_baseline_objective_ratio?: number
  strict_success_count?: number
  held_out_seed_count?: number
  optimizer_update_count?: number
  artifact: string
}

export interface TasksResponse {
  count: number
  result_gates: ResultGate[]
}
