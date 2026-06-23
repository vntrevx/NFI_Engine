import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const ARTIFACTS = [
  "action-log.json",
  "cleanup.json",
  "console-summary.json",
  "failure.json",
  "network-summary.json",
  "security.json",
  "server.log",
  "summary.json",
  "login-empty-desktop.png",
  "home-desktop.png",
  "settings-ko-desktop.png",
  "settings-el-desktop.png",
  "logs-ko-desktop.png",
  "logs-el-desktop.png",
  "home-mobile.png",
  "settings-ko-mobile.png",
  "settings-el-mobile.png",
  "logs-ko-mobile.png",
  "logs-el-mobile.png",
];

export function removePriorArtifacts(evidenceDir) {
  for (const name of ARTIFACTS) {
    rmSync(join(evidenceDir, name), { force: true });
  }
}

export function writeJson(evidenceDir, name, value) {
  writeFileSync(join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

export function writeExtraJson(extraEvidenceDir, name, value) {
  if (!extraEvidenceDir) {
    return;
  }
  mkdirSync(extraEvidenceDir, { recursive: true });
  writeFileSync(join(extraEvidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

export function writeExtraText(extraEvidenceDir, name, value) {
  if (!extraEvidenceDir) {
    return;
  }
  mkdirSync(extraEvidenceDir, { recursive: true });
  writeFileSync(join(extraEvidenceDir, name), value);
}

export function writeFinalExtraArtifacts(extraEvidenceDir, cleanup, reports) {
  if (reports.security) {
    writeExtraJson(extraEvidenceDir, "task-14-security-redaction.json", {
      ...reports.security,
      cleanup,
    });
  }
  if (reports.failureProbes) {
    writeExtraJson(extraEvidenceDir, "task-11-browser-failure.json", {
      ...reports.failureProbes,
      cleanup,
    });
  }
  if (!reports.liveGate) {
    return;
  }
  writeExtraText(
    extraEvidenceDir,
    "task-14-live-gate.txt",
    [
      `passed=${reports.liveGate.passed}`,
      `dryRunDefault=${reports.liveGate.dryRunDefault}`,
      `livePreviewBlocked=${reports.liveGate.livePreviewBlocked}`,
      `liveWarning=${reports.liveGate.liveWarningText}`,
      `livePreview=${reports.liveGate.livePreviewText}`,
      `cleanup=${cleanup.join("; ")}`,
      "",
    ].join("\n"),
  );
}
