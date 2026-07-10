#!/usr/bin/env node
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    const fallback =
      process.env.PLAYWRIGHT_NODE_MODULE_DIR ||
      "/Users/kelly/Developer/so-101-sim/node_modules/playwright";
    return require(fallback);
  }
}

function arg(name, fallback = null) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) return fallback;
  return process.argv[index + 1];
}

const url = arg("--url", "http://127.0.0.1:8822/");
const outputDir = resolve(arg("--output-dir", "outputs/robot_lab/so101_desk_cube_sort/action-server-proof"));
const episodeTimeoutMs = Number(arg("--episode-timeout-ms", "300000"));
const mode = arg("--mode", "normal");
const graspAssistMode = arg("--grasp-assist-mode", "policy_gripper");

const { chromium } = await loadPlaywright();
const browser = await chromium.launch({ headless: true });
const fs = await import("node:fs");
fs.mkdirSync(outputDir, { recursive: true });

const screenshotPath = resolve(outputDir, "action-server-after-episode.png");
const reportPath = resolve(outputDir, "action-server-proof.json");

try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForFunction(
    () => window.__SCENESMITH_ACTION_SERVER_READY === true,
    undefined,
    { timeout: 45000 }
  );
  if (mode === "randomized") {
    await page.fill("#randomSeed", "2601");
    await page.fill("#batchSize", "2");
    await page.selectOption("#policySource", "scripted");
    await page.selectOption("#correctionSource", "simulated_leader");
    await page.check("#forceFailure");
    await page.click("#runRandomized");
    await page.waitForFunction(
      () =>
        window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE === true &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.status === "pass" &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.intervention?.enabled === true,
      undefined,
      { timeout: episodeTimeoutMs }
    );
  } else if (mode === "neural") {
    await page.fill("#randomSeed", "4301");
    await page.fill("#batchSize", "1");
    await page.fill("#maxPolicySteps", "3");
    await page.selectOption("#policySource", "http");
    await page.selectOption("#graspAssistMode", graspAssistMode);
    await page.selectOption("#correctionSource", "none");
    await page.uncheck("#armIntervention");
    await page.click("#runRandomized");
    await page.waitForFunction(
      () =>
        window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE === true &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.status === "fail" &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.policy_runtime?.kind ===
          "persistent_lerobot_http",
      undefined,
      { timeout: episodeTimeoutMs }
    );
  } else {
    await page.fill("#randomSeed", "6302");
    await page.fill("#batchSize", "1");
    await page.fill("#maxPolicySteps", "1600");
    await page.selectOption("#policySource", "http");
    await page.selectOption("#graspAssistMode", graspAssistMode);
    await page.selectOption("#correctionSource", "none");
    await page.uncheck("#armIntervention");
    await page.click("#runEpisode");
    await page.waitForFunction(
      () =>
        window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE === true &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.status === "pass" &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.final_score?.success === true &&
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE?.summary?.policy_runtime?.kind ===
          "persistent_lerobot_http",
      undefined,
      { timeout: episodeTimeoutMs }
    );
  }
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const result = await page.evaluate(() => {
    const episode = window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE;
    const robotSummary = window.__SCENESMITH_SO101_URDF_SUMMARY;
    const wristCameraVisual = window.__SCENESMITH_WRIST_CAMERA_VISUAL;
    const apriltagVisuals = window.__SCENESMITH_APRILTAG_VISUALS || [];
    return {
      ready: window.__SCENESMITH_ACTION_SERVER_READY === true,
      animationDone: window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE === true,
      episodeId: episode?.episode_id,
      mode: episode?.mode,
      sortedCount: episode?.summary?.final_score?.sorted_count,
      totalCount: episode?.summary?.final_score?.total_count,
      success: episode?.summary?.final_score?.success,
      policyProbeStatus: episode?.policy_probe?.status,
      neuralPolicyStatus: episode?.summary?.neural_policy?.status,
      selectedPolicy: episode?.summary?.neural_policy?.selected_policy?.repo_id,
      meshObjectCount: robotSummary?.meshObjectCount,
      triangleCount: robotSummary?.triangleCount,
      cameraThumbnailCount: document.querySelectorAll('img[data-camera-thumb="true"]').length,
      finalWristRender: episode?.summary?.artifacts?.final_wrist_render,
      wristCameraVisualAdded: wristCameraVisual?.added === true,
      wristCameraVisualParent: wristCameraVisual?.parent,
      apriltagVisualCount: apriltagVisuals.length,
      randomizedSeed: episode?.randomization?.seed,
      interventionEnabled: episode?.summary?.intervention?.enabled,
      interventionFrames: episode?.summary?.intervention?.frames,
      physicalFollowerCommanded: episode?.summary?.intervention?.physical_follower_commanded,
      failureReason: episode?.summary?.failure_reason,
      episodeStatus: episode?.summary?.status,
      runnerExitCode: episode?.runner_exit_code,
      taskSuccess: episode?.task_success,
      policyRuntimeKind: episode?.summary?.policy_runtime?.kind,
      neuralClosedLoop: episode?.summary?.policy_runtime?.neural_closed_loop,
      policyDevice: episode?.summary?.policy_runtime?.server_status?.device,
      peftAdapter: episode?.summary?.policy_runtime?.server_status?.peft_adapter,
      neuralActionsApplied: episode?.summary?.proof_scope?.neural_policy_actions_applied_to_simulation,
      scriptedObjectMotion: episode?.summary?.proof_scope?.scripted_object_motion,
      policyGripperContactFrames:
        episode?.summary?.proof_scope?.policy_gripper_contact_frames,
      graspAssistActivations: episode?.summary?.proof_scope?.grasp_assist?.activation_count,
      graspAssistMode: episode?.summary?.proof_scope?.grasp_assist?.mode,
      allGraspActivationsContactGated:
        episode?.summary?.proof_scope?.grasp_assist?.all_activations_contact_gated,
      graspAssistActiveAtSuccess:
        episode?.summary?.proof_scope?.grasp_assist?.active_at_success,
      correctionSource: episode?.summary?.intervention?.source,
      batchEpisodeCount: episode?.episodes?.length,
      episodeSchema: episode?.summary?.schema_version,
      controlStepArbitration: episode?.summary?.intervention?.control_step_arbitration,
      synchronizedObservations: episode?.summary?.proof_scope?.synchronized_observations,
      observationFrames: episode?.summary?.observation_frames,
      interventionControlPresent: !!document.querySelector('#holdTakeover'),
      interventionArmPresent: !!document.querySelector('#armIntervention'),
      policySourceControlPresent: !!document.querySelector('#policySource'),
      studioLeaderOptionPresent: [...document.querySelectorAll('#correctionSource option')]
        .some((option) => option.value === 'studio_leader'),
      noCorrectionOptionPresent: [...document.querySelectorAll('#correctionSource option')]
        .some((option) => option.value === 'none'),
      selectedPolicySource: document.querySelector('#policySource')?.value,
      selectedGraspAssistMode: document.querySelector('#graspAssistMode')?.value,
      selectedCorrectionSource: document.querySelector('#correctionSource')?.value,
      forceFailureDisabled: document.querySelector('#forceFailure')?.disabled,
      forceFailureChecked: document.querySelector('#forceFailure')?.checked,
      interventionStatusSeen: !!window.__SCENESMITH_INTERVENTION_STATUS,
      deadmanTakeoverAfterRun: window.__SCENESMITH_INTERVENTION_STATUS?.deadman?.takeover,
    };
  });
  const normalPass =
    result.mode === "domain_randomized_intervention" &&
    result.randomizedSeed === 6302 &&
    result.taskSuccess === true &&
    result.policyRuntimeKind === "persistent_lerobot_http" &&
    result.neuralClosedLoop === true &&
    result.policyDevice === "mps" &&
    result.peftAdapter === true &&
    result.neuralActionsApplied === true &&
    result.scriptedObjectMotion === false &&
    result.policyGripperContactFrames >= 4 &&
    result.graspAssistActivations >= 4 &&
    result.allGraspActivationsContactGated === true &&
    result.graspAssistActiveAtSuccess === false &&
    result.selectedPolicySource === "http" &&
    result.selectedGraspAssistMode === graspAssistMode &&
    result.graspAssistMode ===
      (graspAssistMode === "contact_reflex"
        ? "contact_gated_jaw_reflex_to_matching_tray"
        : graspAssistMode === "policy_gripper_tray_release"
          ? "policy_gripper_contact_to_low_matching_tray_release"
          : "contact_gated_mujoco_weld") &&
    result.selectedCorrectionSource === "none" &&
    result.noCorrectionOptionPresent === true &&
    result.forceFailureDisabled === true &&
    result.forceFailureChecked === false;
  const randomizedPass =
    result.mode === "domain_randomized_intervention" &&
    result.randomizedSeed === 2601 &&
    result.interventionEnabled === true &&
    result.interventionFrames > 0 &&
    result.physicalFollowerCommanded === false &&
    result.failureReason === "forced_wrong_tray_for_intervention_proof";
  const randomizedControlPass =
    result.batchEpisodeCount === 2 &&
    result.episodeSchema === "scenesmith.intervention_episode.v2" &&
    result.controlStepArbitration === true &&
    result.synchronizedObservations === true &&
    result.observationFrames > 0 &&
    result.interventionControlPresent === true &&
    result.interventionArmPresent === true &&
    result.policySourceControlPresent === true &&
    result.studioLeaderOptionPresent === true &&
    result.interventionStatusSeen === true &&
    result.deadmanTakeoverAfterRun !== true;
  const neuralPass =
    result.mode === "domain_randomized_intervention" &&
    result.randomizedSeed === 4301 &&
    result.episodeStatus === "fail" &&
    result.taskSuccess === false &&
    result.runnerExitCode === 1 &&
    ["neural_policy_stalled", "neural_policy_timeout"].includes(result.failureReason) &&
    result.policyRuntimeKind === "persistent_lerobot_http" &&
    result.neuralClosedLoop === true &&
    result.policyDevice === "mps" &&
    result.neuralActionsApplied === true &&
    result.scriptedObjectMotion === false &&
    result.correctionSource === "none" &&
    result.physicalFollowerCommanded === false &&
    result.selectedPolicySource === "http" &&
    result.selectedCorrectionSource === "none" &&
    result.forceFailureDisabled === true &&
    result.forceFailureChecked === false &&
    result.interventionControlPresent === true &&
    result.interventionArmPresent === true &&
    result.interventionStatusSeen === true &&
    result.deadmanTakeoverAfterRun !== true;
  const episodeOutcomePass =
    mode === "randomized"
      ? result.success && result.sortedCount === result.totalCount && randomizedPass && randomizedControlPass
      : mode === "neural"
        ? neuralPass
        : result.success && result.sortedCount === result.totalCount && normalPass;
  const report = {
    status:
      consoleErrors.length === 0 &&
      result.ready &&
      result.animationDone &&
      episodeOutcomePass &&
      result.meshObjectCount >= 10 &&
      result.cameraThumbnailCount >= 3 &&
      result.wristCameraVisualAdded === true &&
      result.apriltagVisualCount >= 1
        ? "pass"
        : "fail",
    url,
    mode,
    episode_timeout_ms: episodeTimeoutMs,
    screenshot: screenshotPath,
    result,
    console_errors: consoleErrors,
  };
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
  await page.close();
  process.exit(report.status === "pass" ? 0 : 1);
} finally {
  await browser.close();
}
