import crypto from "crypto";
import fs from "fs";
import path from "path";
import { build as viteBuild } from "vite";
import { minify as terserMinify } from "terser";
import { minify as cssoMinify } from "csso";

const repoRoot = process.cwd();
const staticRoot = path.resolve(repoRoot, "app", "static");
const distRoot = path.resolve(repoRoot, "app", "dist", "frontend");
const outDir = path.resolve(distRoot, "static");

const HASH_EXTENSIONS = new Set([".css", ".js"]);
const TEXT_EXTENSIONS = new Set([".css", ".js", ".html", ".json", ".svg", ".xml"]);
const SKIP_EXTENSIONS = new Set([".map"]);
const BUNDLE_ENTRY_ROOT = path.resolve(staticRoot, "js", "pages");
const ALREADY_MINIFIED = /\.min\.\w+$/;

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

const minifyFile = async (filePath) => {
  const ext = path.extname(filePath).toLowerCase();
  if (!TEXT_EXTENSIONS.has(ext)) return;
  if (ALREADY_MINIFIED.test(filePath)) return;
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    if (!raw.trim()) return;
    let result;
    if (ext === ".js") {
      const output = await terserMinify(raw, {
        compress: { drop_console: false },
        mangle: true,
        output: { comments: false },
      });
      result = output.code;
    } else if (ext === ".css") {
      result = cssoMinify(raw, { restructure: true }).css;
    } else {
      return;
    }
    if (result && result.length > 0) {
      fs.writeFileSync(filePath, result, "utf-8");
    }
  } catch (err) {
    console.error(`  minify error: ${filePath} — ${err.message}`);
  }
};

cleanDir(outDir);
fs.mkdirSync(outDir, { recursive: true });

const bundleEntries = collectBundleEntries();
const bundleEntrySet = new Set(bundleEntries);
const bundleManifest = await buildBundles(bundleEntries);

const manifest = { ...bundleManifest };
let copied = 0;
let minified = 0;
let hashed = 0;

walkFiles(staticRoot, (filePath) => {
  const ext = path.extname(filePath).toLowerCase();
  if (SKIP_EXTENSIONS.has(ext)) {
    return;
  }
  const relPath = path.relative(staticRoot, filePath);
  const outPath = path.join(outDir, relPath);

  ensureDir(outPath);
  if (ext === ".json") {
    const raw = fs.readFileSync(filePath, "utf-8").replace(/^\uFEFF/, "");
    const data = JSON.parse(raw);
    fs.writeFileSync(outPath, JSON.stringify(data, null, 0), "utf-8");
  } else {
    fs.copyFileSync(filePath, outPath);
  }
  copied += 1;
});

const minifyTargets = [];
walkFiles(outDir, (filePath) => {
  const ext = path.extname(filePath).toLowerCase();
  if (!TEXT_EXTENSIONS.has(ext)) return;
  if (SKIP_EXTENSIONS.has(ext)) return;
  if (ALREADY_MINIFIED.test(filePath)) return;
  const relPath = path.relative(outDir, filePath);
  if (bundleEntrySet.has(toPosix(relPath))) return;
  minifyTargets.push(filePath);
});

for (const target of minifyTargets) {
  await minifyFile(target);
  minified += 1;
}

walkFiles(outDir, (filePath) => {
  const ext = path.extname(filePath).toLowerCase();
  if (!HASH_EXTENSIONS.has(ext)) return;
  if (ALREADY_MINIFIED.test(filePath)) return;
  const relPath = path.relative(outDir, filePath);
  const relPosix = toPosix(relPath);
  if (bundleEntrySet.has(relPosix)) return;
  if (manifest[relPosix]) return;

  const buffer = fs.readFileSync(filePath);
  const hash = hashFile(buffer);
  const base = path.basename(relPath, ext);
  const hashedName = `${base}.${hash}${ext}`;
  const hashedRel = path.join(path.dirname(relPath), hashedName);
  const hashedOut = path.join(outDir, hashedRel);

  fs.copyFileSync(filePath, hashedOut);
  manifest[relPosix] = toPosix(hashedRel);
  hashed += 1;
});

const manifestPath = path.join(outDir, "manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify(manifest), "utf-8");

console.log(
  `Built frontend assets to ${outDir} (copied=${copied}, minified=${minified}, hashed=${hashed}, bundled=${bundleEntries.length}).`
);
