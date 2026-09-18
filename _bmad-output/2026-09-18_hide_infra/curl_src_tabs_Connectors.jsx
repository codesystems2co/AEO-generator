import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/tabs/Connectors.jsx");import __vite__cjsImport0_react_jsxDevRuntime from "/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=31f60b36"; const Fragment = __vite__cjsImport0_react_jsxDevRuntime["Fragment"]; const jsxDEV = __vite__cjsImport0_react_jsxDevRuntime["jsxDEV"];
import * as RefreshRuntime from "/@react-refresh";
const inWebWorker = typeof WorkerGlobalScope !== "undefined" && self instanceof WorkerGlobalScope;
let prevRefreshReg;
let prevRefreshSig;
if (import.meta.hot && !inWebWorker) {
  if (!window.$RefreshReg$) {
    throw new Error(
      "@vitejs/plugin-react can't detect preamble. Something is wrong."
    );
  }
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = RefreshRuntime.getRefreshReg("/app/src/tabs/Connectors.jsx");
  window.$RefreshSig$ = RefreshRuntime.createSignatureFunctionForTransform;
}
var _s = $RefreshSig$();
import __vite__cjsImport3_react from "/node_modules/.vite/deps/react.js?v=31f60b36"; const useEffect = __vite__cjsImport3_react["useEffect"]; const useState = __vite__cjsImport3_react["useState"];
import { api } from "/src/api.js";
import "/src/App.css?t=1789727146190";
const PLATFORMS = [
  { id: "odoo", label: "Odoo", hint: "website.page / product.template SEO fields" },
  { id: "prestashop", label: "PrestaShop", hint: "meta_title / meta_description / link_rewrite" },
  { id: "woocommerce", label: "WooCommerce", hint: "Yoast / rank math / product or post meta" }
];
export default function Connectors() {
  _s();
  const [platform, setPlatform] = useState("odoo");
  const [health, setHealth] = useState(null);
  const [url, setUrl] = useState("");
  const [database, setDatabase] = useState("");
  const [username, setUsername] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [target, setTarget] = useState("");
  const [title, setTitle] = useState("");
  const [meta, setMeta] = useState("");
  const [keywords, setKeywords] = useState("");
  const [canonical, setCanonical] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState(null);
  async function refreshHealth() {
    try {
      setHealth(await api.connectors.health());
    } catch (err) {
      setHealth({ reachable: false, message: err.message });
    }
  }
  useEffect(() => {
    refreshHealth();
  }, []);
  function payload() {
    return {
      platform,
      target: target || void 0,
      connection: {
        url,
        database: database || void 0,
        username: username || void 0,
        api_key: apiKey || void 0
      },
      seo: {
        title,
        meta_description: meta,
        keywords: keywords.split(",").map((s) => s.trim()).filter(Boolean),
        canonical: canonical || void 0
      }
    };
  }
  async function run(action) {
    setError(null);
    setResult(null);
    setLoading(action);
    try {
      const data = action === "write" ? await api.connectors.write(payload()) : await api.connectors.verify(payload());
      setResult(data);
      if (data.core) setHealth(data.core);
    } catch (err) {
      setError(err.message || "Connection request failed");
    } finally {
      setLoading(null);
    }
  }
  return /* @__PURE__ */ jsxDEV(Fragment, { children: [
    /* @__PURE__ */ jsxDEV("div", { className: "card", children: [
      /* @__PURE__ */ jsxDEV("h3", { children: "Conexión — publicar / verificar en la tienda" }, void 0, false, {
        fileName: "/app/src/tabs/Connectors.jsx",
        lineNumber: 97,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("p", { style: { color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1rem" }, children: "Connect your shop to publish SEO fields (title, description, keywords) and verify write-back. Supported platforms: Odoo, PrestaShop, WooCommerce." }, void 0, false, {
        fileName: "/app/src/tabs/Connectors.jsx",
        lineNumber: 98,
        columnNumber: 9
      }, this),
      health && /* @__PURE__ */ jsxDEV("p", { children: /* @__PURE__ */ jsxDEV("span", { className: `badge ${health.reachable ? "badge-success" : "badge-warn"}`, children: [
        "Shop API ",
        health.reachable ? "ready" : "offline"
      ] }, void 0, true, {
        fileName: "/app/src/tabs/Connectors.jsx",
        lineNumber: 104,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "/app/src/tabs/Connectors.jsx",
        lineNumber: 103,
        columnNumber: 9
      }, this),
      health?.message && /* @__PURE__ */ jsxDEV("p", { style: { color: "var(--text-muted)", fontSize: "0.85rem" }, children: health.message }, void 0, false, {
        fileName: "/app/src/tabs/Connectors.jsx",
        lineNumber: 111,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("button", { type: "button", className: "bt