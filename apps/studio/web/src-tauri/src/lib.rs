use std::{
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};

use serde::Serialize;
use tauri::{Emitter, Manager, State, WindowEvent};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

const MAX_LOG_ENTRIES: usize = 120;
const MAX_LOG_CHARS: usize = 2_000;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendLogEntry {
    at_ms: u64,
    stream: String,
    message: String,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendDiagnostics {
    runtime: String,
    state: String,
    pid: Option<u32>,
    exit_code: Option<i32>,
    signal: Option<i32>,
    logs: Vec<BackendLogEntry>,
}

impl Default for BackendDiagnostics {
    fn default() -> Self {
        Self {
            runtime: "native".into(),
            state: "booting".into(),
            pid: None,
            exit_code: None,
            signal: None,
            logs: Vec::new(),
        }
    }
}

#[derive(Default)]
struct StudioBackend {
    child: Mutex<Option<CommandChild>>,
    diagnostics: Mutex<BackendDiagnostics>,
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
        .try_into()
        .unwrap_or(u64::MAX)
}

fn bounded_message(value: impl AsRef<str>) -> String {
    value.as_ref().trim().chars().take(MAX_LOG_CHARS).collect()
}

fn push_log(diagnostics: &mut BackendDiagnostics, stream: &str, message: impl AsRef<str>) {
    let message = bounded_message(message);
    if message.is_empty() {
        return;
    }
    diagnostics.logs.push(BackendLogEntry {
        at_ms: now_ms(),
        stream: stream.into(),
        message,
    });
    if diagnostics.logs.len() > MAX_LOG_ENTRIES {
        diagnostics.logs.remove(0);
    }
}

fn apply_command_event(diagnostics: &mut BackendDiagnostics, event: CommandEvent) -> bool {
    match event {
        CommandEvent::Stdout(bytes) => {
            let message = String::from_utf8_lossy(&bytes);
            push_log(diagnostics, "stdout", &message);
            if message.contains("Uvicorn running on") {
                diagnostics.state = "ready".into();
            }
            false
        }
        CommandEvent::Stderr(bytes) => {
            let message = String::from_utf8_lossy(&bytes);
            push_log(diagnostics, "stderr", &message);
            if message.contains("Uvicorn running on") {
                diagnostics.state = "ready".into();
            }
            false
        }
        CommandEvent::Error(message) => {
            diagnostics.state = "fault".into();
            push_log(diagnostics, "error", message);
            false
        }
        CommandEvent::Terminated(payload) => {
            diagnostics.exit_code = payload.code;
            diagnostics.signal = payload.signal;
            diagnostics.state = if payload.code == Some(0) {
                "stopped".into()
            } else {
                "fault".into()
            };
            push_log(
                diagnostics,
                "system",
                format!(
                    "backend exited with code {:?}, signal {:?}",
                    payload.code, payload.signal
                ),
            );
            true
        }
        _ => false,
    }
}

#[tauri::command]
fn native_diagnostics(state: State<'_, StudioBackend>) -> BackendDiagnostics {
    state.diagnostics.lock().expect("diagnostics lock").clone()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(StudioBackend::default())
        .invoke_handler(tauri::generate_handler![native_diagnostics])
        .setup(|app| {
            let sidecar = app
                .shell()
                .sidecar("studio-backend")?
                .args(["--parent-pid", &std::process::id().to_string()]);
            let (mut events, child) = sidecar.spawn()?;
            let pid = child.pid();
            let state = app.state::<StudioBackend>();
            *state.child.lock().expect("backend lock") = Some(child);
            {
                let mut diagnostics = state.diagnostics.lock().expect("diagnostics lock");
                diagnostics.state = "starting".into();
                diagnostics.pid = Some(pid);
                push_log(
                    &mut diagnostics,
                    "system",
                    format!("sidecar {pid} spawned on 127.0.0.1:8321"),
                );
            }

            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                while let Some(event) = events.recv().await {
                    let state = handle.state::<StudioBackend>();
                    let (terminated, snapshot) = {
                        let mut diagnostics = state.diagnostics.lock().expect("diagnostics lock");
                        let terminated = apply_command_event(&mut diagnostics, event);
                        (terminated, diagnostics.clone())
                    };
                    if terminated {
                        state.child.lock().expect("backend lock").take();
                    }
                    let _ = handle.emit("studio-backend-diagnostics", snapshot);
                }
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                let state = window.app_handle().state::<StudioBackend>();
                if let Ok(mut backend) = state.child.lock() {
                    if let Some(child) = backend.take() {
                        let _ = child.kill();
                    }
                };
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running SceneSmith Studio");
}

#[cfg(test)]
mod tests {
    use super::*;
    use tauri_plugin_shell::process::TerminatedPayload;

    #[test]
    fn lifecycle_events_are_bounded_and_fail_closed() {
        let mut diagnostics = BackendDiagnostics::default();
        diagnostics.state = "starting".into();

        assert!(!apply_command_event(
            &mut diagnostics,
            CommandEvent::Stderr(b"INFO: Uvicorn running on http://127.0.0.1:8321".to_vec())
        ));
        assert_eq!(diagnostics.state, "ready");

        for index in 0..=MAX_LOG_ENTRIES {
            apply_command_event(
                &mut diagnostics,
                CommandEvent::Stdout(format!("line {index}").into_bytes()),
            );
        }
        assert_eq!(diagnostics.logs.len(), MAX_LOG_ENTRIES);

        assert!(apply_command_event(
            &mut diagnostics,
            CommandEvent::Terminated(TerminatedPayload {
                code: Some(1),
                signal: None,
            })
        ));
        assert_eq!(diagnostics.state, "fault");
        assert_eq!(diagnostics.exit_code, Some(1));
    }

    #[test]
    fn log_messages_are_character_bounded() {
        let mut diagnostics = BackendDiagnostics::default();
        apply_command_event(
            &mut diagnostics,
            CommandEvent::Error("x".repeat(MAX_LOG_CHARS + 10)),
        );
        assert_eq!(diagnostics.logs[0].message.chars().count(), MAX_LOG_CHARS);
        assert_eq!(diagnostics.state, "fault");
    }
}
