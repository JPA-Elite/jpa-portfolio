import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import * as sass from "sass";

const repoRoot = process.cwd();
const staticRoot = path.resolve(repoRoot, "app", "static");
const sourceRoot = path.resolve(staticRoot, "scss");
const outputRoot = path.resolve(staticRoot, "css");
const manifestPath = path.resolve(outputRoot, ".scss-manifest.json");

const toPosix = (value) => value.split(path.sep).join("/");

const walkScss = (dir, callback) => {
  if (!fs.existsSync(dir)) {
    return;
  }
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkScss(fullPath, callback);
      continue;
    }
    callback(fullPath);
  }
};

const isEntry = (filePath) => {
  return (
    path.extname(filePath).toLowerCase() === ".scss" &&
    !path.basename(filePath).startsWith("_")
  );
};

export const collectStyleEntries = () => {
  const entries = [];
  walkScss(sourceRoot, (filePath) => {
    if (!isEntry(filePath)) {
      return;
    }
    entries.push(toPosix(path.relative(sourceRoot, filePath)));
  });
  return entries.sort();
};

const readManifest = () => {
  if (!fs.existsSync(manifestPath)) {
    return [];
  }
  try {
    const data = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
};

const removeStaleOutputs = (generated) => {
  const previous = readManifest();
  const current = new Set(generated);
  const removed = [];
  for (const relPath of previous) {
    if (current.has(relPath)) {
      continue;
    }
    const stale = path.resolve(outputRoot, relPath);
    if (!stale.startsWith(outputRoot) || !fs.existsSync(stale)) {
      continue;
    }
    fs.rmSync(stale, { force: true });
    removed.push(relPath);
  }
  return removed;
};

const compileEntry = (relPath, style) => {
  const sourcePath = path.resolve(sourceRoot, relPath);
  const outputRel = relPath.replace(/\.scss$/i, ".css");
  const outputPath = path.resolve(outputRoot, outputRel);
  const result = sass.compile(sourcePath, {
    style,
    loadPaths: [sourceRoot],
    silenceDeprecations: ["import"],
  });
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, result.css, "utf-8");
  return { relPath, outputRel, outputPath };
};

export const compileStyles = ({ style = "expanded", log = true } = {}) => {
  const entries = collectStyleEntries();
  if (!entries.length) {
    throw new Error(`No SCSS entries found in ${sourceRoot}`);
  }
  const outputs = entries.map((relPath) => compileEntry(relPath, style));
  const generated = outputs.map((item) => item.outputRel);
  const removed = removeStaleOutputs(generated);
  fs.writeFileSync(manifestPath, JSON.stringify(generated, null, 2) + "\n", "utf-8");
  if (log) {
    console.log(
      `Compiled ${outputs.length} SCSS entries to ${outputRoot}` +
        (removed.length ? ` (removed=${removed.length})` : "")
    );
  }
  return { outputs, removed };
};

const snapshotMtimes = () => {
  const mtimes = new Map();
  walkScss(sourceRoot, (filePath) => {
    try {
      mtimes.set(filePath, fs.statSync(filePath).mtimeMs);
    } catch {
      mtimes.set(filePath, 0);
    }
  });
  return mtimes;
};

const watchStyles = () => {
  let previous = snapshotMtimes();
  let building = false;
  let queued = false;

  const run = () => {
    if (building) {
      queued = true;
      return;
    }
    building = true;
    try {
      compileStyles();
    } catch (error) {
      console.error(`SCSS build failed: ${error.message}`);
    } finally {
      building = false;
      if (queued) {
        queued = false;
        run();
      }
    }
  };

  run();
  console.log(`Watching ${sourceRoot} for changes...`);
  setInterval(() => {
    const next = snapshotMtimes();
    let changed = next.size !== previous.size;
    if (!changed) {
      for (const [filePath, mtime] of next) {
        if (previous.get(filePath) !== mtime) {
          changed = true;
          break;
        }
      }
    }
    if (changed) {
      previous = next;
      run();
    }
  }, 400);
};

const isMainModule = () => {
  if (!process.argv[1]) {
    return false;
  }
  return path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
};

if (isMainModule()) {
  try {
    if (process.argv.includes("--watch")) {
      watchStyles();
    } else {
      compileStyles({ style: "expanded" });
    }
  } catch (error) {
    console.error(`SCSS build failed: ${error.message}`);
    process.exit(1);
  }
}
