import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/tabs/Wizard.jsx");import __vite__cjsImport0_react_jsxDevRuntime from "/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=31f60b36"; const Fragment = __vite__cjsImport0_react_jsxDevRuntime["Fragment"]; const jsxDEV = __vite__cjsImport0_react_jsxDevRuntime["jsxDEV"];
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
  window.$RefreshReg$ = RefreshRuntime.getRefreshReg("/app/src/tabs/Wizard.jsx");
  window.$RefreshSig$ = RefreshRuntime.createSignatureFunctionForTransform;
}
var _s = $RefreshSig$();
import __vite__cjsImport3_react from "/node_modules/.vite/deps/react.js?v=31f60b36"; const useEffect = __vite__cjsImport3_react["useEffect"]; const useMemo = __vite__cjsImport3_react["useMemo"]; const useRef = __vite__cjsImport3_react["useRef"]; const useState = __vite__cjsImport3_react["useState"];
import { api, setLicense } from "/src/api.js";
import Accordion, { AccordionPanel } from "/src/components/Accordion.jsx";
import JobProgress from "/src/components/JobProgress.jsx?t=1789726100295";
import TreeList from "/src/components/TreeList.jsx";
import {
  assistantLine,
  buildClientTree,
  buildJobPayload,
  buildProgress
} from "/src/wizard/jobDossier.js?t=1789727146186";
import { copyFor, localeOf } from "/src/i18n/copy.js?t=1789727144288";
import "/src/App.css?t=1789727146190";
function stepsFor(t) {
  return [
    { id: 1, key: "connect", label: t.step.connect },
    { id: 2, key: "google", label: t.step.google },
    { id: 3, key: "aeo", label: t.step.aeo },
    { id: 4, key: "seo", label: t.step.seo }
  ];
}
function stepTitles(t) {
  return { 1: t.step.title1, 2: t.step.title2, 3: t.step.title3, 4: t.step.title4 };
}
function platformsFor(t) {
  return [
    { id: "odoo", label: "Odoo", hint: t.connect.odooHint },
    { id: "prestashop", label: "PrestaShop", hint: t.connect.prestaHint },
    { id: "woocommerce", label: "WooCommerce", hint: t.connect.wooHint }
  ];
}
const PRODUCT_PAGE_URL = "https://arkiphere.cloud/shop/aeo-optimizator-ia-search-optimizator-pack-aeo-seo-and-google-search-109";
const BLOCKED_COPY = {
  message: "Si ya tienes una clave, pégala aquí. Si no, adquiere el pack en la ficha del producto.",
  cta_url: PRODUCT_PAGE_URL,
  cta_label: "Adquirir el pack"
};
const GAP_LABELS = {
  "Live URL fetch": "Página accesible",
  "Title tag": "Título",
  "Meta description": "Descripción",
  "H1 present": "Encabezado principal",
  "robots.txt": "Archivo robots",
  "sitemap.xml": "Mapa del sitio",
  "OAuth client configured": "Search Console listo",
  "Client consent": "Acceso a Search Console",
  "GSC property visible": "Propiedad en Search Console",
  "Service account key": "Cuenta de servicio",
  "GSC property share": "Propiedad compartida",
  "Auth mode selected": "Modo de acceso",
  "Commerce signals": "Señales de tienda",
  "Structured data": "Datos estructurados"
};
function readQuery() {
  if (typeof window === "undefined") {
    return { license: "", site: "", githubLogin: "", gscHint: false };
  }
  try {
    const q = new URLSearchParams(window.location.search);
    return {
      license: (q.get("license") || q.get("key") || "").trim(),
      site: (q.get("site") || "").trim(),
      githubLogin: (q.get("user") || "").trim(),
      gscHint: q.get("gsc") === "connected"
    };
  } catch {
    return { license: "", site: "", githubLogin: "", gscHint: false };
  }
}
function keepHttps(value) {
  const v = (value || "").trim();
  if (!v) return "";
  if (/^https:\/\//i.test(v)) return v;
  if (/^http:\/\//i.test(v)) return `https://${v.slice(7)}`;
  return `https://${v.replace(/^\/+/, "")}`;
}
function hostLabel(url) {
  try {
    return new URL(keepHttps(url)).host || url;
  } catch {
    return url;
  }
}
function businessFromHost(url) {
  const host = hostLabel(url).replace(/^www\./i, "");
  const stem = (host.split(".")[0] || host).replace(/[-_]+/g, " ");
  if (!stem) return "";
  return stem.charAt(0).toUpperCase() + stem.slice(1);
}
function friendlyGapMessage(name, message, connected, t) {
  if (name === "Client consent") {
    return connected ? t.gaps.consentOn : t.gaps.consentOff;
  }
  if (name === "OAuth client configured") {
    return t.gaps.done;
  }
  if (!message) return "";
  const map = [
    [/User must grant/i, t.gaps.consentOff],
    [/Access token present/i, t.gaps.consentOn],
    [/GOOGLE_CLIENT_ID|SECRET/i, t.gaps.done],
    [/Missing meta description/i, t.gaps.missingMeta],
    [/0 H1 tag/i, t.gaps.missingH1],
    [/No JSON-LD/i, t.gaps.missingSchema],
    