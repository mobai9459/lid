use std::io::Write;
use std::process::{Command, Stdio};
use std::sync::Mutex;

use tauri::State;

/// 会话级授权缓存：密码仅存于本进程内存，应用退出即消失，不落盘、不写日志
struct AuthState {
    password: Mutex<Option<String>>,
}

/// 读取当前状态：true = 合盖不休眠（disablesleep 1）
#[tauri::command]
fn get_lid_sleep_status() -> Result<bool, String> {
    read_disablesleep()
}

/// 是否已缓存授权（本次运行内）
#[tauri::command]
fn has_cached_auth(state: State<AuthState>) -> bool {
    state.password.lock().unwrap().is_some()
}

/// 验证管理员密码；成功则缓存到内存，本次运行内切换不再询问
#[tauri::command]
fn authenticate(password: String, state: State<AuthState>) -> Result<bool, String> {
    if sudo_verify(&password) {
        *state.password.lock().unwrap() = Some(password);
        Ok(true)
    } else {
        Ok(false)
    }
}

/// 清除缓存的授权（重新上锁）
#[tauri::command]
fn clear_auth(state: State<AuthState>) {
    *state.password.lock().unwrap() = None;
}

/// 设置合盖是否睡眠。disable_sleep = true 表示合盖不休眠。
/// 需先通过 authenticate 缓存密码；之后用 sudo -S 从 stdin 传密码，免弹窗执行。
#[tauri::command]
fn set_lid_sleep_status(disable_sleep: bool, state: State<AuthState>) -> Result<(), String> {
    let value = if disable_sleep { 1 } else { 0 };
    let password = state.password.lock().unwrap().clone();
    match password.as_deref() {
        Some(pw) => sudo_run(pw, &["/usr/bin/pmset", "-a", "disablesleep", &value.to_string()])?,
        None => return Err("尚未授权，请先输入管理员密码".into()),
    }
    // 设置成功后回读确认，避免“看起来成功但没生效”
    let actual = read_disablesleep()?;
    if actual != disable_sleep {
        return Err("命令已执行，但回读结果与预期不一致，请重试".into());
    }
    Ok(())
}

/// 用 sudo 执行命令，密码通过 stdin 传入（不出现在 argv，ps 不可见）
fn sudo_run(password: &str, args: &[&str]) -> Result<(), String> {
    let mut child = Command::new("/usr/bin/sudo")
        .arg("-S") // 从 stdin 读密码
        .arg("-p") // 空 prompt，避免污染 stderr
        .arg("")
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("无法启动 sudo: {e}"))?;
    {
        let mut stdin = child.stdin.take().ok_or("无法写入 sudo 输入")?;
        stdin
            .write_all(password.as_bytes())
            .and_then(|_| stdin.write_all(b"\n"))
            .map_err(|e| format!("写入密码失败: {e}"))?;
    } // stdin 在此 drop 关闭，sudo 收到 EOF
    let output = child
        .wait_with_output()
        .map_err(|e| format!("sudo 执行失败: {e}"))?;
    if output.status.success() {
        Ok(())
    } else {
        Err(format!(
            "命令执行失败: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ))
    }
}

/// 仅验证密码是否正确（sudo -v 不执行任何命令）
fn sudo_verify(password: &str) -> bool {
    sudo_run(password, &["-v"]).is_ok()
}

fn read_disablesleep() -> Result<bool, String> {
    let output = Command::new("/usr/bin/pmset")
        .arg("-g")
        .output()
        .map_err(|e| format!("无法执行 pmset: {e}"))?;
    if !output.status.success() {
        return Err(format!(
            "pmset -g 执行失败: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(parse_disablesleep(&String::from_utf8_lossy(&output.stdout)))
}

/// 解析 `pmset -g` 输出。
/// 实测（macOS 26）：执行 `pmset -a disablesleep 1` 后，状态反映在
/// "System-wide power settings:" 段的 `SleepDisabled 1`；"Currently in use:"
/// 段里没有 disablesleep 字段。为兼容不同系统版本，两处都查，任一为 1 即开启。
/// 两者都未出现视为未开启。
fn parse_disablesleep(stdout: &str) -> bool {
    let mut sleep_disabled: Option<bool> = None;
    let mut disable_sleep: Option<bool> = None;
    for line in stdout.lines() {
        let line = line.trim_start();
        let lower = line.to_lowercase();
        if let Some(rest) = lower.strip_prefix("sleepdisabled") {
            if rest.is_empty() || rest.starts_with(char::is_whitespace) {
                sleep_disabled = Some(line["sleepdisabled".len()..].trim() == "1");
            }
        } else if let Some(rest) = lower.strip_prefix("disablesleep") {
            if rest.is_empty() || rest.starts_with(char::is_whitespace) {
                disable_sleep = Some(line["disablesleep".len()..].trim() == "1");
            }
        }
    }
    sleep_disabled.unwrap_or(false) || disable_sleep.unwrap_or(false)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AuthState {
            password: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            get_lid_sleep_status,
            set_lid_sleep_status,
            has_cached_auth,
            authenticate,
            clear_auth
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::parse_disablesleep;

    #[test]
    fn parses_sleep_disabled_system_wide() {
        // 真实输出格式：System-wide 段，tab 分隔
        let sample = "System-wide power settings:\n SleepDisabled\t\t1\nCurrently in use:\n standby  1\n";
        assert!(parse_disablesleep(sample));
    }

    #[test]
    fn parses_disablesleep_fallback() {
        // 兼容在 Currently in use 段出现 disablesleep 的系统版本
        let sample = "Currently in use:\n disablesleep         1\n standby  1\n";
        assert!(parse_disablesleep(sample));
    }

    #[test]
    fn parses_disabled() {
        let sample = "System-wide power settings:\n SleepDisabled 0\nCurrently in use:\n disablesleep 0\n";
        assert!(!parse_disablesleep(sample));
    }

    #[test]
    fn missing_key_means_disabled() {
        let sample = "Currently in use:\n standby  1\n powernap 0\n";
        assert!(!parse_disablesleep(sample));
    }

    #[test]
    fn ignores_keys_with_same_prefix() {
        let sample = " disablesleepx  1\n sleepdisabledy 1\n SleepDisabled 0\n";
        assert!(!parse_disablesleep(sample));
    }

    #[test]
    fn ignores_unrelated_keys() {
        // "Sleep On Power Button 1" 不应被误判
        let sample = "Currently in use:\n Sleep On Power Button 1\n";
        assert!(!parse_disablesleep(sample));
    }
}
