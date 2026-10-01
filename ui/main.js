const tauri = window.__TAURI__;
const hasTauri = !!(tauri && tauri.core && tauri.core.invoke);
const invoke = (cmd, args) => tauri.core.invoke(cmd, args);

// ---- i18n：跟随系统语言，zh* 用中文，其余（含未知语言）一律英文 ----
const I18N = {
  zh: {
    title: "合盖不休眠",
    subtitle: "开启后合盖仍保持运行",
    ariaSwitch: "合盖不休眠",
    reading: "正在读取当前设置…",
    on: "合盖不休眠已开启",
    off: "合盖正常睡眠",
    noTauri: "未检测到 Tauri 环境，请在应用窗口中打开",
    readFailed: "读取失败：",
    applying: "正在应用更改…",
    authTitle: "管理员授权",
    passwordPlaceholder: "开机密码",
    ok: "好",
    cancel: "取消",
    needPassword: "请输入密码",
    authFailed: "授权失败：",
    wrongPassword: "密码不正确，请重试",
    passwordPrompt: "开机密码",
  },
  en: {
    title: "Keep awake on close",
    subtitle: "Your Mac keeps running with the lid closed",
    ariaSwitch: "Keep awake on lid close",
    reading: "Reading current setting…",
    on: "Keep awake on lid close: ON",
    off: "Sleeping normally on lid close",
    noTauri: "Tauri environment not detected. Open in the app window.",
    readFailed: "Failed to read: ",
    applying: "Applying changes…",
    authTitle: "Administrator authorization",
    passwordPlaceholder: "Password",
    ok: "OK",
    cancel: "Cancel",
    needPassword: "Please enter your password",
    authFailed: "Authorization failed: ",
    wrongPassword: "Incorrect password, try again",
    passwordPrompt: "Password",
  },
};

function detectLang() {
  const langs = [
    ...(navigator.languages || []),
    navigator.language || "en",
  ];
  for (const l of langs) {
    const lang = (l || "").toLowerCase();
    if (lang.startsWith("zh")) return "zh";
    // en 及其他任何语言都回落到英文
    if (lang.startsWith("en")) return "en";
  }
  return "en";
}

const LANG = detectLang();
const t = (key) => I18N[LANG][key] ?? I18N.en[key];
document.documentElement.lang = LANG === "zh" ? "zh-CN" : "en";

// ---- 静态文案填充 ----
const switchBtn = document.getElementById("switch");
const statusEl = document.getElementById("status");
const authLayer = document.getElementById("auth-layer");
const authPass = document.getElementById("auth-pass");
const authOk = document.getElementById("auth-ok");
const authCancel = document.getElementById("auth-cancel");
const authError = document.getElementById("auth-error");

document.getElementById("t-title").textContent = t("title");
document.getElementById("t-subtitle").textContent = t("subtitle");
document.getElementById("t-auth-title").textContent = t("authTitle");
authOk.textContent = t("ok");
authCancel.textContent = t("cancel");
authPass.placeholder = t("passwordPlaceholder");
switchBtn.setAttribute("aria-label", t("ariaSwitch"));

let busy = false;
// 授权层挂起期间等待应用的目标状态（null 表示没有挂起的切换）
let pendingTarget = null;

// busy 的变量与按钮样式必须同步变更，避免出现“逻辑可点但样式禁点”的残留
function setBusy(v) {
  busy = v;
  switchBtn.classList.toggle("busy", v);
}

function setSwitch(on) {
  switchBtn.classList.toggle("on", on);
  switchBtn.setAttribute("aria-checked", String(on));
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

async function refresh() {
  if (!hasTauri) {
    setStatus(t("noTauri"));
    return;
  }
  try {
    const disableSleep = await invoke("get_lid_sleep_status");
    setSwitch(disableSleep);
    setStatus(disableSleep ? t("on") : t("off"));
  } catch (e) {
    setStatus(t("readFailed") + e, true);
  }
}

async function doSet(target) {
  try {
    await invoke("set_lid_sleep_status", { disableSleep: target });
  } catch (e) {
    setStatus(String(e), true);
  }
  // 无论成功失败都以真实状态为准回读一次
  await refresh();
}

function showAuthLayer(target) {
  pendingTarget = target;
  authError.textContent = "";
  authPass.value = "";
  authLayer.classList.remove("hidden");
  authPass.focus();
}

function hideAuthLayer() {
  authLayer.classList.add("hidden");
  pendingTarget = null;
}

async function confirmAuth() {
  if (pendingTarget === null) return;
  const pw = authPass.value;
  if (!pw) {
    authError.textContent = t("needPassword");
    return;
  }
  authOk.disabled = true;
  let ok = false;
  try {
    ok = await invoke("authenticate", { password: pw });
  } catch (e) {
    authError.textContent = t("authFailed") + e;
    authOk.disabled = false;
    return;
  }
  authOk.disabled = false;
  if (!ok) {
    authError.textContent = t("wrongPassword");
    authPass.select();
    return;
  }
  const target = pendingTarget;
  hideAuthLayer();
  setStatus(t("applying"));
  await doSet(target);
  setBusy(false);
}

function cancelAuth() {
  hideAuthLayer();
  setBusy(false);
  refresh();
}

switchBtn.addEventListener("click", async () => {
  if (busy || !hasTauri) return;
  setBusy(true);
  const target = !switchBtn.classList.contains("on");
  let authorized = false;
  try {
    authorized = await invoke("has_cached_auth");
  } catch (e) {
    setStatus(t("readFailed") + e, true);
    setBusy(false);
    return;
  }
  if (authorized) {
    setStatus(t("applying"));
    await doSet(target);
    setBusy(false);
  } else {
    // 保持锁定态，直到授权完成或取消
    showAuthLayer(target);
  }
});

authOk.addEventListener("click", confirmAuth);
authCancel.addEventListener("click", cancelAuth);
authPass.addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmAuth();
  if (e.key === "Escape") cancelAuth();
});

// 窗口重新聚焦时刷新（用户可能在终端里手动改过 pmset）
window.addEventListener("focus", refresh);
refresh();
