# Pulse — Terminal System Monitor (TUI)

**Pulse** is a lightweight terminal-based system monitor for Linux, built with `curses`. It displays real-time system stats in a clean three-column layout with optional centered ASCII art.

## 🔧 Features

- 🧠 CPU usage, core temperatures, fan speeds  
- 💾 Memory, swap, and disk usage  
- 🔋 Battery charge, status, and voltage  
- ⚡ Sensor voltages (excluding battery)  
- 🎨 Centered ASCII art background  
- 📊 Color-coded values and intuitive layout

> **Note:** Battery voltage is shown **only in the second column**, other voltages go to the third.

## ▶️ Getting Started

Make sure you have Python 3, `psutil`, and `sensors` (from `lm-sensors`) installed.

### 🛠 Makefile

```bash
make run   # Run the monitor
make clean # Remove .pyc files
```

Use requirements
```
psutil==7.0.0
