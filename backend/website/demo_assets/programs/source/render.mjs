// Render each <slug>.html in DIR to OUT/<slug>.png at 1200x750 with headless Chrome (DevTools protocol).
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const [DIR, OUT] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn("google-chrome", ["--headless=new", "--remote-debugging-port=9335", `--user-data-dir=${DIR}/chrome`, "--no-first-run", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
let t;
for (let i = 0; i < 40; i++) { try { t = await (await fetch("http://127.0.0.1:9335/json")).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(t.find((x) => x.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0; const P = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id) P.get(m.id)?.(m); });
const send = (method, params = {}) => new Promise((r) => { const i = ++id; P.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1200, height: 750, deviceScaleFactor: 1, mobile: false });
for (const f of fs.readdirSync(DIR).filter((f) => f.endsWith(".html"))) {
  await send("Page.navigate", { url: "file://" + path.join(DIR, f) });
  await sleep(1500);
  const r = await send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family).join(','))", awaitPromise: true, returnByValue: true });
  await sleep(300);
  const s = await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 0, width: 1200, height: 750, scale: 1 } });
  fs.writeFileSync(path.join(OUT, f.replace(".html", ".png")), Buffer.from(s.result.data, "base64"));
  console.log(f, "fonts:", r.result?.result?.value);
}
chrome.kill();
process.exit(0);
