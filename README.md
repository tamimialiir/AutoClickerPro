# Auto Clicker Pro (v6.0) 🚀

Auto Clicker Pro is a highly sophisticated, modular, and human-like automation utility designed to simulate complex mouse and keyboard sequences through a user-friendly, dark-themed interface based on the popular **Catppuccin** color palette. 

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-v6.0-orange)

In version **v6.0**, the application has undergone a fundamental architectural re-engineering. By transitioning to a robust **Composition-based Architecture**, introducing centralized theming, structured rotating file logging, and automated unit testing, the codebase is remarkably resilient, maintainable, and extensible.

---

## Features

- **Click, Drag, Scroll, Keyboard & Wait** actions in one sequence
- **Record** real mouse + keyboard actions and convert them into editable points
- **Pause / Resume** — stop mid-sequence, edit the list freely, then continue
- **Speed control** (×0.1 – ×20) with live scaling of all delays, holds and drags
- **Hotkeys** for Start / Pause / Stop / Start Recording / Stop Recording (fully customizable, each can be enabled/disabled)
- **Time Jitter** (±ms) and **Position Jitter** (±px) for more human-like behavior
- **Cycles** + Infinite mode
- **Save / Load** profiles (JSON)
- **Drag & drop** reordering of points
- Copy / Cut / Paste items (Ctrl+C / Ctrl+X / Ctrl+V)
- **Live position preview** when editing — drag the on-screen marker to reposition
- Optional **name** for every action type
- **Color-coded + emoji action list** for instant recognition of each action type
- **Tooltips** on almost every control (English) for clearer usage
- Clickable **GitHub** link in the app footer
- **Check Update** — checks GitHub Releases for a newer version
- Always-on-top option
- Clean dark theme (Catppuccin-inspired)


## Screenshots
![Main Window](screenshots/main_5.2.png)

---

## 🚀 Getting Started

### Prerequisites
*   Python **3.8 or higher**
*   Windows, macOS, or Linux operating system (Keyboard layout switching is optimized for Windows)

### 1. Installation
The application relies on the `pynput` library for system-wide keyboard and mouse capturing/simulation. Install it via pip:
```bash
pip install pynput
```

### 2. Run the Application
Simply execute the main launcher script:
```bash
python main.py
```

---

## Usage Guide

### Adding Actions
| Button          | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| **Add Click**   | Click on screen → settings popup opens to configure the point               |
| **Add Drag**    | Press & hold, then release → settings popup opens                           |
| **Add Scroll**  | Click on screen to set position → settings popup opens                      |
| **Add Key**     | Type or capture a key / combination (`ctrl+c`, `alt+f4`...), set repeats    |
| **Add Wait**    | Insert a delay (in milliseconds)                                            |
| **Record**      | Record live mouse + keyboard actions                                        |

### Editing & Organizing

*   **Reorder Items:** Click and drag any item in the list up or down to change its execution sequence visually. (Alternative: Use the `↑` and `↓` buttons).
*   **Copy Action (`Ctrl + C`):** Copies the selected action to the internal clipboard.
*   **Cut Action (`Ctrl + X`):** Cuts the selected action from the list.
*   **Paste Action (`Ctrl + V`):** Pastes the copied action directly beneath the current selection.
*   **Remove Action (`Delete`):** Instantly deletes the selected action.
*   **Configure Action:** Double-click any row to open its dedicated configuration popup.

The action list is **color-coded with emojis**:
| Action | Emoji | Color   |
|--------|:-------:|---------|
| Click  |  🖱️   | Green   |
| Drag   |  ↔️   | Blue    |
| Scroll |  ↕️   | Purple  |
| Wait   |  ⏱️   | Yellow  |
| Key    |  ⌨️   | Orange  |

### Global Settings
**Speed:** Global playback speed from ×0.1 to ×20 (default ×1.0). Affects waits, holds, drag duration and repeat delays. Can only be changed before Start, while Paused, or after Stop. Use **Reset** to return to ×1.0.  
**Time Jitter:** Add a randomized delay variation of up to `±500ms` on wait actions, preventing rigid, machine-like click intervals. 
**Position Jitter:** Add a random spatial offset of up to `±50px` on your clicks and drag points. This simulates natural, non-static human click distributions. 
**Cycles:** How many times the whole sequence should run.  
**Infinite:** Run forever until stopped.  
**Always on Top:** Keep the window above other windows.

### Hotkeys (default)
| Action              | Default Key |
|---------------------|:-------------:|
| Start               |    `F1`     |
| Pause / Resume      |    `F2`     |
| Stop                |    `F3`     |
| Start Recording     |    `F4`     |
| Stop Recording      |    `F5`     |

You can change all hotkeys from the Hotkeys section.  
Media / system keys (volume, play/pause, brightness, etc.) cannot be assigned as hotkeys.


## Profile System

**Save Profile** → exports current sequence + all settings (including speed) to a `.json` file  
**Load Profile** → restores everything (points, hotkeys, jitter, speed, etc.)

Perfect for sharing macros or switching between different tasks.


## Tips

- Use **Record** for complex sequences, then clean them up with Edit.
- For more natural behavior, enable a small Time Jitter and Position Jitter.
- Name each point for better organization in long sequences.
- Drag the on-screen preview marker when editing to reposition points quickly.
- Use **Speed** above ×1 to run macros faster, or below ×1 for careful debugging.
- The app forces English keyboard layout on Windows when focused (helps with key recording).
- Use **Pause** when you need to adjust the sequence mid-run without losing progress.
- Hover over buttons and controls to see short English tooltips.
- Click **Check Update** in the bottom-right to see if a newer release is available on GitHub.
- Click the **GitHub** link in the bottom-right corner to open the project repository.

---

## ✨ What's New in v6.0

*   **Composition over Inheritance:** Completely replaced the legacy multiple-inheritance God Object with a clean, decoupled Composition architecture. The main controller coordinates specialized engines (`ActionsEngine`, `RecorderEngine`, `ListManager`, `ProfilesManager`, `HotkeyManager`) with clear separation of concerns.
*   **Centralized Theme Engine:** All Catppuccin Mocha color tokens and fonts are unified in `theme.py`, eliminating duplicate hardcoded values.
*   **Structured Logging & Error Handling:** Replaced silent error swallowing (`except: pass`) with comprehensive logging via rotating file handlers (`~/.autoclickerpro/logs/app.log`) and console output.
*   **Type-Safe Action Models:** Actions and macro points are backed by `ActionPoint` Dataclasses with input validation, while maintaining 100% backward compatibility with existing profile JSON formats.
*   **Decoupled Subsystems:** Extracted global hotkey listening (`hotkey_manager.py`), GitHub release checking (`updater.py`), and OS layout handling (`system_utils.py`) into dedicated single-responsibility modules.
*   **Automated Test Suite:** Added a full unit and integration test suite (`tests/`) ensuring regression-free execution loops, jitter math, persistence, and UI dialogs.

---

## 📂 Modular Project Structure

The project comprises the following organized file structure, coupled cleanly via **Composition**:

| File Name | Technical Responsibility |
| :--- | :--- |
| **`main.py`** | Application coordinator (`AutoClickerApp`). Orchestrates subsystem instances, manages window lifecycle, and wires global events. |
| **`theme.py`** | Centralized Catppuccin Mocha theme definitions, color constants, and typography. |
| **`logger.py`** | Application logging infrastructure with rotating file handlers and console stream formatting. |
| **`models.py`** | Data models (`ActionPoint`) with type hints, serialization (`to_dict`, `from_dict`), and dictionary compatibility layers. |
| **`actions_engine.py`** | Simulation engine managing multi-threaded playback loops, speed scaling, jitter offsets, and peripheral dispatching. |
| **`recorder_engine.py`** | Real-time event recording engine tracking mouse clicks, drags, scrolls, and keystrokes with noise filtering. |
| **`list_manager.py`** | Point sequence management, drag-and-drop reordering, copy/cut/paste clipboard operations, and visual list styling. |
| **`profiles_manager.py`** | Profile persistence manager handling JSON serialization, validation, and disk I/O. |
| **`hotkey_manager.py`** | Global background keyboard shortcut listener and dynamic re-binding manager. |
| **`updater.py`** | Asynchronous GitHub release checker comparing SemVer tags. |
| **`system_utils.py`** | Platform-specific utilities including Windows keyboard layout enforcement and screen centering. |
| **`gui_layout.py`** | Main window widget layout, ttk styling, tooltips, and state locking manager (`set_ui_lock_state`). |
| **`gui_components.py`** | Reusable UI components including the delayed `ToolTip` and on-screen draggable crosshair preview markers. |
| **`popups.py`** | Modal dialog windows for adding and editing actions with live coordinate capture and preview handles. |
| **`utils.py`** | Resource path resolution for PyInstaller bundles and physical key mapping translations. |
| **`tests/`** | Automated test suite verifying data models, persistence, jitter math, and popup integration. |

---


## License
This project is licensed under the MIT License.  
Feel free to use, modify and distribute.


## Contributing
Pull requests are welcome!  
If you find a bug or have a feature idea, open an issue.


Made with ❤️ for automation lovers

**Version:** v6.0 | **Theme:** Catppuccin Dark | **Author:** [TamimiAliIR](https://github.com/tamimialiir)