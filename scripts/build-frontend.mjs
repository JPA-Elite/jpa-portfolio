import crypto from "crypto";
import fs from "fs";
import os from "os";
import path from "path";
import { execFileSync } from "child_process";
import { build as viteBuild } from "vite";
import { minify as terserMinify } from "terser";
import { minify as cssoMinify } from "csso";

const repoRoot = process.cwd();
const staticRoot = path.resolve(repoRoot, "app", "static");
const distRoot = path.resolve(repoRoot, "app", "dist", "frontend");
const outDir = path.resolve(distRoot, "static");
const pageBundleConfigPath = path.resolve(repoRoot, "scripts", "page-bundles.json");

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

const readSource = (relPath) => {
  const fullPath = path.join(staticRoot, relPath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Page bundle references a missing file: ${relPath}`);
  }
  return fs.readFileSync(fullPath, "utf-8");
};

const collectImportPaths = (source) => {
  const paths = [];
  const pattern = /^\s*import\s+(?:[^'"]*?\sfrom\s+)?["']([^"']+)["']\s*;?\s*$/gm;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    paths.push(match[1]);
  }
  return paths;
};

const resolveImportPath = (fromRelPath, specifier) => {
  if (!specifier.startsWith(".")) {
    return null;
  }
  return toPosix(path.normalize(path.join(path.dirname(fromRelPath), specifier)));
};

const collectModuleDependencies = (relPath, collected, visiting = new Set()) => {
  if (collected.includes(relPath) || visiting.has(relPath)) {
    return;
  }
  const source = readSource(relPath);
  visiting.add(relPath);
  for (const specifier of collectImportPaths(source)) {
    const dependency = resolveImportPath(relPath, specifier);
    if (dependency) {
      collectModuleDependencies(dependency, collected, visiting);
    }
  }
  visiting.delete(relPath);
  collected.push(relPath);
};

const stripModuleSyntax = (source) => {
  return source
    .replace(/^\s*import\s+(?:[^'"]*?\sfrom\s+)?["'][^"']+["']\s*;?\s*$/gm, "")
    .replace(/^\s*export\s+(?=(?:class|function|const|let|var)\b)/gm, "")
    .replace(/^\s*export\s*\{[^}]*\}\s*;?\s*$/gm, "")
    .replace(/^\s*export\s+default\s+/gm, "");
};

const normalizeJsEntry = (entry) => {
  if (typeof entry === "string") {
    return { src: entry, module: false };
  }
  return { src: entry.src, module: Boolean(entry.module) };
};

const assemblePageJs = (sources) => {
  const chunks = [];
  const files = [];
  for (const entry of sources) {
    const { src, module } = normalizeJsEntry(entry);
    if (module) {
      const dependencies = [];
      collectModuleDependencies(src, dependencies);
      for (const dependency of dependencies) {
        if (files.includes(dependency)) {
          continue;
        }
        files.push(dependency);
        chunks.push(`/* ${dependency} */\n${stripModuleSyntax(readSource(dependency))}`);
      }
      continue;
    }
    if (files.includes(src)) {
      continue;
    }
    files.push(src);
    chunks.push(`/* ${src} */\n${readSource(src)}`);
  }
  return { code: chunks.join("\n;\n"), files };
};

const validateClassicJs = (label, code) => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "page-bundle-"));
  const tempFile = path.join(tempDir, `${label}.js`);
  try {
    fs.writeFileSync(tempFile, code, "utf-8");
    execFileSync(process.execPath, ["--check", tempFile], { stdio: "pipe" });
  } catch (err) {
    const details = err.stderr ? err.stderr.toString() : err.message;
    throw new Error(`Page bundle JS failed syntax validation for "${label}":\n${details}`);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
};

const assemblePageCss = (sources) => {
  const chunks = [];
  for (const src of sources) {
    chunks.push(`/* ${src} */\n${readSource(src)}`);
  }
  return { code: chunks.join("\n") };
};

const loadPageBundleConfig = () => {
  if (!fs.existsSync(pageBundleConfigPath)) {
    return { routes: {}, common: {}, pages: {} };
  }
  return JSON.parse(fs.readFileSync(pageBundleConfigPath, "utf-8"));
};

const pageCssSources = (config, page) => {
  if (page.standalone) {
    return [...(page.css || [])];
  }
  const common = (page.admin ? config.admin_common : config.common) || {};
  return [
    ...(common.head_css || []),
    ...(page.css || []),
    ...(common.tail_css || []),
  ];
};

const pageJsSources = (config, page) => {
  if (page.standalone) {
    return [...(page.js || [])];
  }
  const common = (page.admin ? config.admin_common : config.common) || {};
  return [...(common.js || []), ...(page.js || [])];
};

const writePageBundles = async (manifest, config) => {
  const pages = config.pages || {};
  const written = [];
  for (const [key, page] of Object.entries(pages)) {
    const css = assemblePageCss(pageCssSources(config, page));
    const cssMinified = cssoMinify(css.code, { restructure: true }).css;
    const cssBuffer = Buffer.from(cssMinified, "utf-8");
    const cssRel = toPosix(path.join("assets", "pages", `${key}.${hashFile(cssBuffer)}.css`));
    ensureDir(path.join(outDir, cssRel));
    fs.writeFileSync(path.join(outDir, cssRel), cssBuffer);
    manifest[`pages/${key}.css`] = cssRel;

    const js = assemblePageJs(pageJsSources(config, page));
    validateClassicJs(key, js.code);
    const jsMinified = await terserMinify(js.code, {
      compress: { drop_console: false },
      mangle: true,
      format: { comments: false },
    });
    if (!jsMinified.code) {
      throw new Error(`Page bundle JS minification produced no output for "${key}"`);
    }
    const jsBuffer = Buffer.from(jsMinified.code, "utf-8");
    const jsRel = toPosix(path.join("assets", "pages", `${key}.${hashFile(jsBuffer)}.js`));
    ensureDir(path.join(outDir, jsRel));
    fs.writeFileSync(path.join(outDir, jsRel), jsBuffer);
    manifest[`pages/${key}.js`] = jsRel;

    written.push(`${key}(css=${cssBuffer.length}B, js=${jsBuffer.length}B)`);
  }
  return written;
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

const pageBundleConfig = loadPageBundleConfig();
const pageBundles = await writePageBundles(manifest, pageBundleConfig);

const manifestPath = path.join(outDir, "manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify(manifest), "utf-8");
fs.writeFileSync(
  path.join(distRoot, "page-bundles.json"),
  JSON.stringify(pageBundleConfig, null, 2),
  "utf-8"
);

console.log(
  `Built frontend assets to ${outDir} (copied=${copied}, minified=${minified}, hashed=${hashed}, bundled=${bundleEntries.length}, pages=${pageBundles.length}).`
);
