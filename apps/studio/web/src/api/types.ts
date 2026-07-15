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

export type StudioDocumentKind = 'briefs' | 'reviewer-messages'

export interface StudioDocument {
  kind: StudioDocumentKind
  filename: string
  content: string
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

export type WorkcellColor = 'red' | 'blue' | 'green' | 'yellow' | 'purple' | 'orange'

export interface WorkcellCubeSpec {
  name: string
  color: WorkcellColor
  position_m: [number, number, number]
  side_length_m?: number
  mass_kg?: number
}

export interface WorkcellTraySpec {
  name: string
  color: WorkcellColor
  center_m: [number, number, number]
  size_m?: [number, number, number]
}

export interface WorkcellArrangementSpec {
  schema_version: 'scenesmith.workcell_arrangement_spec.v1'
  scene_id: string
  description?: string
  task_prompt: string
  success_metric?: string
  trays: WorkcellTraySpec[]
  cubes: WorkcellCubeSpec[]
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

export interface RobotArtifactSource {
  artifact: string
  artifact_sha256: string
  identity_sha256: string
  schema_version: string
}

export interface RobotCameraEvidence {
  stable_identity_sha256?: string | null
  capture_identity_sha256?: string | null
  input_mode: {
    width?: number
    height?: number
    framerate_fps?: number
    pixel_format?: string
  }
  frame_count: number
}

export interface RobotServoEvidence {
  servo_id?: number | null
  joint_name?: string | null
  model?: string | null
  model_number?: number | null
  firmware_version?: string | null
}

export interface RobotDiscoveryEvidence extends RobotArtifactSource {
  manifest_name?: string | null
  session_id?: string | null
  evidence_mode?: string | null
  qualification_scope?: string | null
  proof_labels: string[]
  discovery_stability?: string | null
  hardware_opened?: boolean | null
  physical_follower_commanded?: boolean | null
  pre_open_identity_sha256?: string | null
  post_close_identity_sha256?: string | null
  privacy: Record<string, boolean>
  camera_operation_counts?: Record<string, number>
  cameras: RobotCameraEvidence[]
}

export interface RobotCensusContract extends RobotArtifactSource {
  contract_name?: string | null
  proof_label?: string | null
  qualification_scope?: string | null
  expected_servo_count: number
  forbidden_operations: string[]
}

export interface RobotCensusEvidence extends RobotArtifactSource {
  session_id?: string | null
  proof_labels: string[]
  servos: RobotServoEvidence[]
  operation_counts: Record<string, number>
  contract: RobotCensusContract
}

export interface RobotCalibrationJoint {
  servo_id?: number | null
  joint_name?: string | null
  model?: string | null
  firmware_version?: string | null
  drive_mode?: number | null
  homing_offset?: number | null
  range_min?: number | null
  range_max?: number | null
  normalization_mode?: string | null
}

export interface RobotCalibrationEvidence extends RobotArtifactSource {
  profile_name?: string | null
  evidence_mode?: string | null
  qualification_scope?: string | null
  joint_count?: number | null
  joints: RobotCalibrationJoint[]
  normalization_contract: Record<string, unknown>
  accepted_live_manifest: Record<string, unknown>
  hardware_accessed?: boolean | null
  physical_follower_commanded?: boolean | null
  motion_authority_granted?: boolean | null
  training_authority_granted?: boolean | null
  authority_not_granted: string[]
}

export interface RobotResponse {
  mode: 'signed_artifacts_read_only'
  registration: { enabled: false; reason: string }
  discovery: RobotDiscoveryEvidence
  census: RobotCensusEvidence
  calibration: RobotCalibrationEvidence
}
