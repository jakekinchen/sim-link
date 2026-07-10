#!/usr/bin/env node
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

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

const url = arg("--url");
const outputDir = resolve(arg("--output-dir", "outputs/robot_lab/viewer-proof"));
const policyRequestPath = arg("--policy-request");
const outputPolicyRequestPath = arg("--output-policy-request");
if (!url) {
  console.error("Usage: verify_threejs_viewer.mjs --url <viewer-url> --output-dir <dir>");
  process.exit(2);
}

const { chromium } = await loadPlaywright();
const browser = await chromium.launch({ headless: true });
const desktopPath = resolve(outputDir, "viewer-desktop.png");
const mobilePath = resolve(outputDir, "viewer-mobile.png");
const robotCloseupPath = resolve(outputDir, "viewer-robot-closeup.png");
const reportPath = resolve(outputDir, "viewer-proof.json");
await import("node:fs").then((fs) => fs.mkdirSync(outputDir, { recursive: true }));

try {
  const report = {
    status: "fail",
    url,
    screenshots: { desktop: desktopPath, mobile: mobilePath, robot_closeup: robotCloseupPath },
    checks: {},
    console_errors: [],
  };

  for (const viewport of [
    { name: "desktop", width: 1440, height: 900, path: desktopPath },
    { name: "mobile", width: 390, height: 844, path: mobilePath },
  ]) {
    const page = await browser.newPage({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: viewport.name === "mobile" ? 2 : 1,
    });
    page.on("console", (message) => {
      if (message.type() === "error") report.console_errors.push(message.text());
    });
    await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
    await page.waitForFunction(() => window.__SCENESMITH_VIEWER_READY === true, {
      timeout: 45000,
    });
    await page.screenshot({ path: viewport.path, fullPage: true });
    const canvasStats = await page.evaluate(() => {
      const canvas = document.querySelector("canvas");
      if (!canvas) return { hasCanvas: false };
      const ctx = canvas.getContext("webgl2") || canvas.getContext("webgl");
      const width = canvas.width;
      const height = canvas.height;
      const pixels = new Uint8Array(width * height * 4);
      ctx.readPixels(0, 0, width, height, ctx.RGBA, ctx.UNSIGNED_BYTE, pixels);
      let nonBlack = 0;
      for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] > 8 || pixels[i + 1] > 8 || pixels[i + 2] > 8) nonBlack += 1;
      }
      return {
        hasCanvas: true,
        width,
        height,
        nonBlack,
        sceneId: window.__SCENESMITH_ROBOT_LAB_SCENE__?.scene_id,
        cubeCount: window.__SCENESMITH_ROBOT_LAB_SCENE__?.cubes?.length ?? 0,
        so101UrdfLoaded: window.__SCENESMITH_SO101_URDF_LOADED === true,
        so101UrdfModelAdded: window.__SCENESMITH_SO101_URDF_MODEL_ADDED === true,
        so101UrdfError: window.__SCENESMITH_SO101_URDF_ERROR,
        so101UrdfSummary: window.__SCENESMITH_SO101_URDF_SUMMARY || null,
      };
    });
    const realSo101JointNames = [
      "Rotation",
      "Pitch",
      "Elbow",
      "Wrist_Pitch",
      "Wrist_Roll",
      "Jaw",
    ];
    const loadedJointNames = canvasStats.so101UrdfSummary?.jointNames || [];
    const realJointSetLoaded = realSo101JointNames.every((name) =>
      loadedJointNames.includes(name)
    );
    const detailedMeshLoaded =
      (canvasStats.so101UrdfSummary?.meshObjectCount || 0) >= 10 &&
      (canvasStats.so101UrdfSummary?.triangleCount || 0) >= 1000;
    report.checks[viewport.name] = {
      ready: true,
      canvasStats,
      nonblank: canvasStats.nonBlack > 1000,
      so101UrdfLoaded: canvasStats.so101UrdfLoaded,
      so101UrdfModelAdded: canvasStats.so101UrdfModelAdded,
      realSo101JointSetLoaded: realJointSetLoaded,
      detailedMeshLoaded,
    };
    if (viewport.name === "desktop") {
      await page.evaluate(() => {
        const camera = window.__SCENESMITH_VIEWER_CAMERA;
        const controls = window.__SCENESMITH_VIEWER_CONTROLS;
        if (camera && controls) {
          camera.position.set(0.26, -0.46, 0.58);
          controls.target.set(0.02, 0.0, 0.40);
          controls.update();
        }
      });
      await page.waitForTimeout(300);
      await page.screenshot({ path: robotCloseupPath, fullPage: true });
    }
    await page.close();
  }

  report.status =
    report.console_errors.length === 0 &&
    Object.values(report.checks).every(
      (check) =>
        check.ready &&
        check.nonblank &&
        check.so101UrdfLoaded &&
        check.so101UrdfModelAdded &&
        check.realSo101JointSetLoaded &&
        check.detailedMeshLoaded
    )
      ? "pass"
      : "fail";

  await import("node:fs").then((fs) =>
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + "\n")
  );
  if (policyRequestPath) {
    await writeRenderedPolicyRequest({
      inputPath: resolve(policyRequestPath),
      outputPath: outputPolicyRequestPath
        ? resolve(outputPolicyRequestPath)
        : resolve(dirname(resolve(policyRequestPath)), "policy_request.rendered.json"),
      desktopPath,
      mobilePath,
      reportPath,
    });
  }
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.status === "pass" ? 0 : 1);
} finally {
  await browser.close();
}

async function writeRenderedPolicyRequest({
  inputPath,
  outputPath,
  desktopPath,
  mobilePath,
  reportPath,
}) {
  const fs = await import("node:fs");
  const request = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  request.observation = request.observation || {};
  request.observation.images = request.observation.images || {};
  request.observation.images.cam0 = fs.readFileSync(desktopPath).toString("base64");
  request.observation.images.cam1 = fs.readFileSync(mobilePath).toString("base64");
  request.metadata = {
    ...(request.metadata || {}),
    rendered_observation_source:
      "SceneSmith Three.js verifier screenshots; replace with runtime robot cameras for hardware execution.",
    rendered_cam0_artifact: desktopPath,
    rendered_cam1_artifact: mobilePath,
    viewer_proof_report: reportPath,
  };
  fs.writeFileSync(outputPath, JSON.stringify(request, null, 2) + "\n");
}
