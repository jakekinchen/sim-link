use std::sync::Mutex;

use tauri::{Manager, WindowEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct StudioBackend(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(StudioBackend(Mutex::new(None)))
        .setup(|app| {
            let sidecar = app
                .shell()
                .sidecar("studio-backend")?
                .args(["--parent-pid", &std::process::id().to_string()]);
            let (_events, child) = sidecar.spawn()?;
            *app.state::<StudioBackend>().0.lock().expect("backend lock") = Some(child);
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                if let Ok(mut backend) = window.app_handle().state::<StudioBackend>().0.lock() {
                    if let Some(child) = backend.take() {
                        let _ = child.kill();
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running SceneSmith Studio");
}
