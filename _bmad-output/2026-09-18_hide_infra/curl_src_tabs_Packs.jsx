import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/tabs/Packs.jsx");import __vite__cjsImport0_react_jsxDevRuntime from "/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=31f60b36"; const Fragment = __vite__cjsImport0_react_jsxDevRuntime["Fragment"]; const jsxDEV = __vite__cjsImport0_react_jsxDevRuntime["jsxDEV"];
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
  window.$RefreshReg$ = RefreshRuntime.getRefreshReg("/app/src/tabs/Packs.jsx");
  window.$RefreshSig$ = RefreshRuntime.createSignatureFunctionForTransform;
}
var _s = $RefreshSig$();
import __vite__cjsImport3_react from "/node_modules/.vite/deps/react.js?v=31f60b36"; const useEffect = __vite__cjsImport3_react["useEffect"]; const useState = __vite__cjsImport3_react["useState"];
import { api } from "/src/api.js";
import TreeList from "/src/components/TreeList.jsx";
import "/src/App.css?t=1789727146190";
export default function Packs() {
  _s();
  const [topic, setTopic] = useState("Arkiphere Cloud");
  const [url, setUrl] = useState("https://arkiphere.cloud");
  const [businessName, setBusinessName] = useState("Arkiphere Cloud");
  const [context, setContext] = useState("Odoo PaaS, Community and Enterprise, free trial, AI billing.");
  const [health, setHealth] = useState(null);
  const [pack, setPack] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  useEffect(() => {
    api.packs.health().then(setHealth).catch((err) => setHealth({ status: "error", error: err.message }));
  }, []);
  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.packs.generate({
        topic,
        url: url || void 0,
        business_name: businessName || void 0,
        context: context || void 0,
        locale: "en"
      });
      setPack(data);
    } catch (err) {
      setError(err.message || "Pack generation failed");
    } finally {
      setLoading(false);
    }
  }
  function copyResume() {
    if (pack?.resume) navigator.clipboard.writeText(pack.resume);
  }
  return /* @__PURE__ */ jsxDEV(Fragment, { children: [
    /* @__PURE__ */ jsxDEV("div", { className: "card", children: [
      /* @__PURE__ */ jsxDEV("h3", { children: "AEO + SEO pack" }, void 0, false, {
        fileName: "/app/src/tabs/Packs.jsx",
        lineNumber: 66,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("p", { style: { color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1rem" }, children: "Generate a publish pack and a human-readable tree resume for your site." }, void 0, false, {
        fileName: "/app/src/tabs/Packs.jsx",
        lineNumber: 67,
        columnNumber: 9
      }, this),
      health && /* @__PURE__ */ jsxDEV("p", { style: { marginBottom: "1rem" }, children: /* @__PURE__ */ jsxDEV("span", { className: `badge ${health.status === "ok" ? "badge-success" : "badge-warn"}`, children: [
        "Pack service ",
        health.status
      ] }, void 0, true, {
        fileName: "/app/src/tabs/Packs.jsx",
        lineNumber: 72,
        columnNumber: 13
      }, this) }, void 0, false, {
        fileName: "/app/src/tabs/Packs.jsx",
        lineNumber: 71,
        columnNumber: 9
      }, this),
      /* @__PURE__ */ jsxDEV("form", { onSubmit: handleSubmit, children: [
        /* @__PURE__ */ jsxDEV("div", { className: "form-row", children: [
          /* @__PURE__ */ jsxDEV("label", { children: "Topic / brand *" }, void 0, false, {
            fileName: "/app/src/tabs/Packs.jsx",
            lineNumber: 80,
            columnNumber: 13
          }, this),
          /* @__PURE__ */ jsxDEV("input", { value: topic, onChange: (e) => setTopic(e.target.value), required: true }, void 0, false, {
            fileName: "/app/src/tabs/Packs.jsx",
            lineNumber: 81,
            columnNumber: 13
          }, this)
        ] }, void 0, true, {
          fileName: "/app/src/tabs/Packs.jsx",
          lineNumber: 79,
          columnNumber: 11
        }, this),
        /* @__PURE__ */ jsxDEV("div", { className: "form-row", children: [
          /* @__PURE__ */ jsxDEV("label", { children: "Business name" }, void 0, false, {
            fileName: "/app/src/tabs/Packs.jsx",
            lineNumber: 84,
            columnNumber: 13
          }, this),
          /* @__PURE__ */ jsxDEV("input", { value: businessName, onChange: (e) => setBusinessName(e.target.value) }, void 0, false, {
            fileName: "/app/src/tabs/Packs.jsx",
            lineNumber