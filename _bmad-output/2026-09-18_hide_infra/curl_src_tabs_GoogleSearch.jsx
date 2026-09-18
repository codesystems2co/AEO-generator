import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/tabs/GoogleSearch.jsx");import __vite__cjsImport0_react_jsxDevRuntime from "/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=31f60b36"; const Fragment = __vite__cjsImport0_react_jsxDevRuntime["Fragment"]; const jsxDEV = __vite__cjsImport0_react_jsxDevRuntime["jsxDEV"];
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
  window.$RefreshReg$ = RefreshRuntime.getRefreshReg("/app/src/tabs/GoogleSearch.jsx");
  window.$RefreshSig$ = RefreshRuntime.createSignatureFunctionForTransform;
}
var _s = $RefreshSig$();
import __vite__cjsImport3_react from "/node_modules/.vite/deps/react.js?v=31f60b36"; const useEffect = __vite__cjsImport3_react["useEffect"]; const useState = __vite__cjsImport3_react["useState"];
import { api } from "/src/api.js";
import "/src/App.css?t=1789727146190";
export default function GoogleSearch() {
  _s();
  const [siteUrl, setSiteUrl] = useState("https://arkiphere.cloud");
  const [mode, setMode] = useState("oauth");
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [sites, setSites] = useState(null);
  const [saJson, setSaJson] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  async function refreshStatus() {
    try {
      const data = await api.google.status();
      setStatus(data);
      if (data?.mode && data.mode !== "unset") setMode(data.mode);
    } catch (err) {
      setError(err.message);
    }
  }
  useEffect(() => {
    refreshStatus();
  }, []);
  async function runReadiness(e) {
    e?.preventDefault();
    setError(null);
    setInfo(null);
    setLoading(true);
    try {
      const data = await api.google.readiness({ site_url: siteUrl, mode });
      setResult(data);
    } catch (err) {
      setError(err.message || "Readiness check failed");
    } finally {
      setLoading(false);
    }
  }
  async function startConsent() {
    setError(null);
    setInfo(null);
    setLoading(true);
    try {
      const data = await api.google.oauthStart();
      if (data.auth_url) {
        window.location.href = data.auth_url;
        return;
      }
      setError("No consent URL returned");
    } catch (err) {
      setError(err.message || "OAuth start failed");
    } finally {
      setLoading(false);
    }
  }
  async function loadSites() {
    setError(null);
    try {
      const data = await api.google.sites();
      setSites(data);
    } catch (err) {
      setError(err.message);
    }
  }
  async function saveSa(e) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    try {
      const data = await api.google.saSession({ json_key: saJson });
      if (data.ok) {
        setInfo(data.message);
        setMode("service_account");
        await refreshStatus();
      } else {
        setError(data.error || "Invalid service account JSON");
      }
    } catch (err) {
      setError(err.message);
    }
  }
  const oauth = status?.modes?.oauth || {};
  const sa = status?.modes?.service_account || {};
  return /* @__PURE__ */ jsxDEV(Fragment, { children: [
    /* @__PURE__ */ jsxDEV("div", { className: "card", children: [
      /* @__PURE__ */ jsxDEV("h3", { children: "Google Search readiness" }, void 0, false, {
        fileName: "/app/src/tabs/GoogleSearch.jsx",
        lineNumber: 116,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("p", { style: { color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1rem" }, children: [
        "Public crawl checks plus Search Console auth. Choose ",
        /* @__PURE__ */ jsxDEV("strong", { children: "OAuth" }, void 0, false, {
          fileName: "/app/src/tabs/GoogleSearch.jsx",
          lineNumber: 118,
          columnNumber: 64
        }, this),
        " (client consent) or ",
        /* @__PURE__ */ jsxDEV("strong", { children: "Service Account" }, void 0, false, {
          fileName: "/app/src/tabs/GoogleSearch.jsx",
          lineNumber: 119,
          columnNumber: 14
        }, this),
        ". Complete Google Search before publishing your pack."
      ] }, void 0, true, {
        fileName: "/app/src/tabs/GoogleSearch.jsx",
        lineNumber: 117,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("div", { className: "mode-grid", children: [
        /* @__PURE__ */ jsxDEV(
          "button",
          {
            type: "button",
            className: `mode-card ${mode === "oauth" ? "active" : ""}`,
  