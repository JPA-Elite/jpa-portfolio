import fs from "fs";
import path from "path";
import { defineConfig } from "vite";

const repoRoot = process.cwd();
const staticRoot = path.resolve(repoRoot, "backend", "static");
const outDir = path.resolve(repoRoot, "backend", "dist", "frontend", "static");

const TEXT_EXTENSIONS = new Set([".js", ".css"]);
const SKIP_EXTENSIONS = new Set([".map"]);
const BUNDLE_SKIP_PREFIXES = ["js/bootstrap/", "css/bootstrap/"];

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

const shouldBundle = (relPath) => {
  return !BUNDLE_SKIP_PREFIXES.some((prefix) => relPath.startsWith(prefix));
};

const collectEntries = () => {
  const entries = {};
  walkFiles(staticRoot, (filePath) => {
    const ext = path.extname(filePath).toLowerCase();
    if (!TEXT_EXTENSIONS.has(ext) || SKIP_EXTENSIONS.has(ext)) {
      return;
    }
    const relPath = toPosix(path.relative(staticRoot, filePath));
    if (!shouldBundle(relPath)) {
      return;
    }
    entries[relPath] = filePath;
  });
  return entries;
};

const copyStaticAssets = (bundledSet) => ({
  name: "copy-static-assets",
  closeBundle() {
    walkFiles(staticRoot, (filePath) => {
      const relPath = path.relative(staticRoot, filePath);
      const relPosix = toPosix(relPath);
      const ext = path.extname(filePath).toLowerCase();
      if (SKIP_EXTENSIONS.has(ext)) {
        return;
      }
      if (bundledSet.has(relPosix)) {
        return;
      }
      const targetPath = path.join(outDir, relPath);
      fs.mkdirSync(path.dirname(targetPath), { recursive: true });
      if (ext === ".json") {
        const raw = fs.readFileSync(filePath, "utf-8").replace(/^\uFEFF/, "");
        const data = JSON.parse(raw);
        fs.writeFileSync(targetPath, JSON.stringify(data), "utf-8");
      } else {
        fs.copyFileSync(filePath, targetPath);
      }
    });
  },
});

const entries = collectEntries();
const bundledSet = new Set(Object.keys(entries));

export default defineConfig({
  root: staticRoot,
  build: {
    outDir,
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: entries,
      output: {
        format: "es",
        entryFileNames: "assets/[name].[hash].js",
        chunkFileNames: "assets/[name].[hash].js",
        assetFileNames: "assets/[name].[hash][extname]",
      },
    },
  },
  plugins: [copyStaticAssets(bundledSet)],
});
