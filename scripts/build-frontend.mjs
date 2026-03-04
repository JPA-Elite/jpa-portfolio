import crypto from "crypto";
import fs from "fs";
import path from "path";
import { build as viteBuild } from "vite";

const repoRoot = process.cwd();
const staticRoot = path.resolve(repoRoot, "backend", "static");
const distRoot = path.resolve(repoRoot, "backend", "dist", "frontend");
const outDir = path.resolve(distRoot, "static");

const HASH_EXTENSIONS = new Set([".css", ".js"]);
const SKIP_EXTENSIONS = new Set([".map"]);
const BUNDLE_ENTRY_ROOT = path.resolve(staticRoot, "js", "pages");

const toPosix = (value) => value.split(path.sep).join("/");

const walkFiles = (dir, callback) => {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkFiles(fullPath, callback);
      continue;
    }
    callback(fullPath);
  }
};

const ensureDir = (filePath) => {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
};

const cleanDir = (dir) => {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
};

const copyFile = (src, dst) => {
  ensureDir(dst);
  fs.copyFileSync(src, dst);
};

const hashFile = (buffer) => {
  return crypto.createHash("sha256").update(buffer).digest("hex").slice(0, 10);
};

const hasImportStatements = (filePath) => {
  const content = fs.readFileSync(filePath, "utf-8");
  return /^\s*import\s+/m.test(content);
};

const collectBundleEntries = () => {
  if (!fs.existsSync(BUNDLE_ENTRY_ROOT)) {
    return [];
  }
  const entries = [];
  walkFiles(BUNDLE_ENTRY_ROOT, (filePath) => {
    if (path.extname(filePath).toLowerCase() !== ".js") {
      return;
    }
    if (!hasImportStatements(filePath)) {
      return;
    }
    entries.push(toPosix(path.relative(staticRoot, filePath)));
  });
  return entries;
};

const loadViteManifest = () => {
  const legacyManifest = path.join(outDir, "manifest.json");
  const viteManifest = path.join(outDir, ".vite", "manifest.json");
  let manifestPath = null;
  if (fs.existsSync(viteManifest)) {
    manifestPath = viteManifest;
  } else if (fs.existsSync(legacyManifest)) {
    manifestPath = legacyManifest;
  }
  if (!manifestPath) {
    return {};
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
  if (manifestPath === viteManifest) {
    fs.rmSync(path.join(outDir, ".vite"), { recursive: true, force: true });
  } else {
    fs.rmSync(manifestPath, { force: true });
  }
  return manifest;
};

const buildBundles = async (entries) => {
  if (!entries.length) {
    return {};
  }
  const input = {};
  for (const relPath of entries) {
    input[relPath] = path.join(staticRoot, relPath);
  }
  await viteBuild({
    configFile: false,
    root: staticRoot,
    publicDir: false,
    logLevel: "error",
    clearScreen: false,
    build: {
      outDir,
      emptyOutDir: false,
      manifest: true,
      rollupOptions: {
        input,
        output: {
          format: "es",
          entryFileNames: "[name].[hash].js",
          chunkFileNames: "assets/[name].[hash].js",
          assetFileNames: "assets/[name].[hash][extname]",
        },
      },
    },
  });
  return loadViteManifest();
};

cleanDir(outDir);
fs.mkdirSync(outDir, { recursive: true });

const bundleEntries = collectBundleEntries();
const bundleEntrySet = new Set(bundleEntries);
const bundleManifest = await buildBundles(bundleEntries);

const manifest = { ...bundleManifest };
let copied = 0;
let hashed = 0;

walkFiles(staticRoot, (filePath) => {
  const ext = path.extname(filePath).toLowerCase();
  if (SKIP_EXTENSIONS.has(ext)) {
    return;
  }
  const relPath = path.relative(staticRoot, filePath);
  const relPosix = toPosix(relPath);
  const outPath = path.join(outDir, relPath);

  copyFile(filePath, outPath);
  copied += 1;

  if (!HASH_EXTENSIONS.has(ext)) {
    return;
  }
  if (bundleEntrySet.has(relPosix)) {
    return;
  }
  if (manifest[relPosix]) {
    return;
  }

  const buffer = fs.readFileSync(filePath);
  const hash = hashFile(buffer);
  const base = path.basename(relPath, ext);
  const hashedName = `${base}.${hash}${ext}`;
  const hashedRel = path.join(path.dirname(relPath), hashedName);
  const hashedOut = path.join(outDir, hashedRel);

  copyFile(filePath, hashedOut);
  manifest[relPosix] = toPosix(hashedRel);
  hashed += 1;
});

const manifestPath = path.join(outDir, "manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");

console.log(
  `Built frontend assets to ${outDir} (copied=${copied}, hashed=${hashed}, bundled=${bundleEntries.length}).`
);
