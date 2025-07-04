import curses
import time
import subprocess
import re
import psutil
from collections import defaultdict

def color_temp(temp_c):
    try:
        temp = float(temp_c)
        if temp < 50:
            return curses.color_pair(1)
        elif temp < 70:
            return curses.color_pair(2)
        else:
            return curses.color_pair(3)
    except:
        return curses.A_NORMAL

def color_rpm(rpm):
    try:
        rpm_val = int(rpm)
        if rpm_val < 1000:
            return curses.color_pair(3)
        elif rpm_val < 2000:
            return curses.color_pair(2)
        else:
            return curses.color_pair(1)
    except:
        return curses.A_NORMAL

def friendly_chip_name(chip):
    mapping = {
        'coretemp': '🧠 CPU',
        'k10temp': '🧠 CPU (AMD)',
        'amdgpu': '🎮 GPU (AMD)',
        'nvidia': '🎮 GPU (NVIDIA)',
        'nvme': '💾 NVMe',
        'iwlwifi': '📶 Wi-Fi',
        'acpitz': '🌡️ ACPI Sensor',
        'pch': '🔧 PCH',
        'battery': '🔋 Battery',
        'bat': '🔋 Battery',
        'sensor': '🔍 Sensor',
        'spd': '🧠 RAM',
    }
    chip = chip.lower()
    for key, name in mapping.items():
        if key in chip:
            return name
    return f'📦 {chip}'

def parse_sensors_cli():
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True)
        output = result.stdout
        general = defaultdict(list)
        current_chip = None
        seen = set()

        for line in output.splitlines():
            line = line.strip()
            if not line:
                current_chip = None
                continue
            if ':' not in line and not line.startswith('Adapter:'):
                current_chip = line.split()[0]
                continue

            chip_lc = current_chip.lower() if current_chip else ""

            m_temp = re.search(r'([^:]+):\s+\+?([\d.]+)°C', line)
            m_fan = re.search(r'(fan\d+):\s+(\d+)\s*RPM', line)
            m_volt = re.search(r'([^:]+):\s+([\d.]+)\s*V', line)

            if current_chip:
                chip_name = friendly_chip_name(current_chip)

                if m_temp:
                    label, temp = m_temp.group(1).strip(), m_temp.group(2)
                    key = f"{chip_name}-{label}-{temp}"
                    if key not in seen:
                        seen.add(key)
                        general[chip_name].append(('temp', label, temp))

                elif m_fan:
                    fan_label, rpm = m_fan.group(1), m_fan.group(2)
                    key = f"{chip_name}-{fan_label}-{rpm}"
                    if key not in seen:
                        seen.add(key)
                        general[chip_name].append(('fan', fan_label, rpm))

                elif m_volt:
                    volt_label, volt_val = m_volt.group(1).strip(), m_volt.group(2)
                    key = f"{chip_name}-{volt_label}-{volt_val}"
                    if key not in seen:
                        seen.add(key)
                        general[chip_name].append(('volt', volt_label, volt_val))

        return general
    except Exception as e:
        return defaultdict(list, {"Error": [(str(e),)]})

def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "free": mem.available,
        "percent": mem.percent
    }

def get_swap_info():
    swap = psutil.swap_memory()
    return {
        "total": swap.total,
        "used": swap.used,
        "free": swap.free,
        "percent": swap.percent
    }

def get_disk_info(path="/"):
    disk = psutil.disk_usage(path)
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }

def get_battery_info():
    try:
        batt = psutil.sensors_battery()
        if batt is None:
            return None
        return {
            "percent": batt.percent,
            "secsleft": batt.secsleft,
            "plugged": batt.power_plugged
        }
    except Exception:
        return None

def format_bytes(n):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}P"

def draw_ascii_background(stdscr, art_lines, max_y, max_x):
    art_height = len(art_lines)
    art_width = max(len(line) for line in art_lines) if art_lines else 0

    start_y = max((max_y - art_height) // 2, 0)
    start_x = max((max_x - art_width) // 2, 0)

    for i, line in enumerate(art_lines):
        if start_y + i >= max_y:
            break
        display_line = line[:max_x - start_x]
        try:
            stdscr.addstr(start_y + i, start_x, display_line, curses.color_pair(4) | curses.A_DIM)
        except curses.error:
            pass


def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)   # для температур і CPU load
    curses.init_pair(2, curses.COLOR_YELLOW, -1) # для пам'яті, батареї
    curses.init_pair(3, curses.COLOR_RED, -1)    # для попереджень
    curses.init_pair(4, 8, -1)                    # для фону

    stdscr.nodelay(True)
    
    try:
        with open("bg.txt", "r", encoding="utf-8") as f:
            ascii_art = [line.rstrip('\n') for line in f.readlines()]
    except Exception as e:
        ascii_art = [f"Failed to load background: {str(e)}"]

    class Column:
        def __init__(self, col_start):
            self.col = col_start
            self.row = 0

        def add(self, text, attr=curses.A_NORMAL):
            max_y, max_x = stdscr.getmaxyx()
            if self.row < max_y:
                try:
                    stdscr.addstr(self.row, self.col, text[:max_x - self.col], attr)
                except curses.error:
                    pass
            self.row += 1

        def add_space(self, n=1):
            self.row += n

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        draw_ascii_background(stdscr, ascii_art, max_y, max_x)

        col_width = max_x // 2 if max_x < 100 else max_x // 3
        col1 = Column(0)
        col2 = Column(col_width)
        col3 = Column(col_width * 2)

        temps = parse_sensors_cli()
        cpu_percent = psutil.cpu_percent(interval=0.5)

        # Колонка 1 - CPU load і сенсори (окрім вольтажів і батареї)
        col1.add(f"⚡ CPU Load: {cpu_percent:.1f}%", curses.A_BOLD | curses.color_pair(1))
        col1.add_space()

        for chip, readings in temps.items():
            # Пропускаємо батарею в першій колонці
            if 'battery' in chip.lower() or 'bat' in chip.lower():
                continue
            col1.add(f"{chip}:", curses.A_BOLD)
            for typ, label, val in readings:
                if typ == 'temp':
                    color = color_temp(val)
                    col1.add(f"  {label}: {val}°C", color)
                elif typ == 'fan':
                    color = color_rpm(val)
                    col1.add(f"  {label}: {val} RPM", color)
                # Вольтажі в першій колонці не показуємо
            col1.add_space()

        # Колонка 2 - пам'ять, своп, диск, батарея
        mem = get_memory_info()
        swap = get_swap_info()
        disk = get_disk_info()

        col2.add("🧠 Memory:", curses.A_BOLD | curses.color_pair(2))
        col2.add(f"  Used: {format_bytes(mem['used'])} / {format_bytes(mem['total'])}")
        col2.add(f"  Usage: {mem['percent']}%", 
                curses.color_pair(1) if mem['percent'] < 70 else 
                curses.color_pair(2) if mem['percent'] < 90 else 
                curses.color_pair(3))
        col2.add_space()

        col2.add("🔃 Swap:", curses.A_BOLD | curses.color_pair(2))
        col2.add(f"  Used: {format_bytes(swap['used'])} / {format_bytes(swap['total'])}")
        col2.add(f"  Usage: {swap['percent']}%", 
                curses.color_pair(1) if swap['percent'] < 70 else 
                curses.color_pair(2) if swap['percent'] < 90 else 
                curses.color_pair(3))
        col2.add_space()

        col2.add("💾 Disk (/):", curses.A_BOLD | curses.color_pair(3))
        col2.add(f"  Used: {format_bytes(disk['used'])} / {format_bytes(disk['total'])}")
        col2.add(f"  Usage: {disk['percent']}%", 
                curses.color_pair(1) if disk['percent'] < 70 else 
                curses.color_pair(2) if disk['percent'] < 90 else 
                curses.color_pair(3))
        col2.add_space()

        # Батарея
        batt = get_battery_info()
        if batt:
            col2.add("🔋 Battery:", curses.A_BOLD | curses.color_pair(2))
            status = "Charging" if batt["plugged"] else "Discharging"
            col2.add(f"  Charge: {int(batt['percent'])}% ({status})")  # Округлення до цілого

            # Вольтаж батареї з temps (де є "battery" в назві)
            batt_voltages = []
            for chip, readings in temps.items():
                if 'battery' in chip.lower() or 'bat' in chip.lower():
                    for typ, label, val in readings:
                        if typ == 'volt':
                            batt_voltages.append((label, val))
            for label, val in batt_voltages:
                col2.add(f"  {label}: {val} V", curses.color_pair(1))
            
            col2.add_space()

        # Колонка 3 - вольтажі інших сенсорів (окрім батареї)
        for chip, readings in temps.items():
            if 'battery' in chip.lower() or 'bat' in chip.lower():
                continue
            for typ, label, val in readings:
                if typ == 'volt':
                    col3.add(f"{chip} - {label}: {val} V", curses.color_pair(1))
        col3.add_space()

        footer = " Press 'q' to quit "
        stdscr.addstr(max_y-1, max_x//2 - len(footer)//2, footer, curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(1)

        try:
            if stdscr.getch() == ord('q'):
                break
        except:
            pass

if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_ALL, '')
    curses.wrapper(main)

