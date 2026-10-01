const tauri = window.__TAURI__;
const hasTauri = !!(tauri && tauri.core && tauri.core.invoke);
const invoke = (cmd, args) => tauri.core.invoke(cmd, args);

const switchBtn = document.getElementById("switch");
const statusEl = document.getElementById("status");
const authLayer = document.getElementById("auth-layer");
const authPass = document.getElementById("auth-pass");
const authOk = document.getElementById("auth-ok");
const authCancel = document.getElementById("auth-cancel");
const authError = document.getElementById("auth-error");

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
    setStatus("未检测到 Tauri 环境，请在应用窗口中打开");
    return;
  }
  try {
    const disableSleep = await invoke("get_lid_sleep_status");
    setSwitch(disableSleep);
    setStatus(disableSleep ? "合盖不休眠已开启" : "合盖正常睡眠");
  } catch (e) {
    setStatus("读取设置失败：" + e, true);
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
    authError.textContent = "请输入密码";
    return;
  }
  authOk.disabled = true;
  let ok = false;
  try {
    ok = await invoke("authenticate", { password: pw });
  } catch (e) {
    authError.textContent = "授权失败：" + e;
    authOk.disabled = false;
    return;
  }
  authOk.disabled = false;
  if (!ok) {
    authError.textContent = "密码不正确，请重试";
    authPass.select();
    return;
  }
  const target = pendingTarget;
  hideAuthLayer();
  setStatus("正在应用更改…");
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
    setStatus("读取失败：" + e, true);
    setBusy(false);
    return;
  }
  if (authorized) {
    setStatus("正在应用更改…");
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
