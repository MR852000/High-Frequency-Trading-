"""
ReactPy dashboard UI — the "Barclays HFT" quant dashboard.
Split out of the original single-file main.py so the API/DB layer can
grow independently of the frontend component tree.
"""
import asyncio
import importlib.util
import os
import platform
import random
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from reactpy import component, html, use_effect, use_state

COLORS = {
    "bg": "#1E1E24",
    "panel": "#000000",
    "border": "#2A2A30",
    "accent": "#00AEEF",
    "green": "#00C853",
    "red": "#FF5252",
    "text": "#FFFFFF",
    "muted": "#9AA0A6",
}

QUANT_TOPICS = [
    {"key": "linalg", "label": "Linear Algebra", "icon": "Σ"},
    {"key": "probability", "label": "Probability", "icon": "P"},
    {"key": "statistics", "label": "Statistics", "icon": "σ"},
    {"key": "calculus", "label": "Calculus", "icon": "∫"},
    {"key": "optimization", "label": "Mathematical Optimization", "icon": "∇"},
    {"key": "discrete", "label": "Discrete Maths", "icon": "∀"},
]

# New structural configuration array for the requested HFT metrics
HFT_SIGNALS = [
    {"key": "obi", "label": "Order Book Imbalance (OBI)", "icon": "📊"},
    {"key": "vpin", "label": "Trade Flow Toxicity (VPIN)", "icon": "☠️"},
    {"key": "queue", "label": "Queue Position & Depletion", "icon": "⏳"},
    {"key": "cross_asset", "label": "Cross-Asset Correlation", "icon": "🔄"},
    {"key": "latency_arb", "label": "Cross-Venue (Latency Arb)", "icon": "⚡"},
    {"key": "quote_stuffing", "label": "Quote Stuffing Detection", "icon": "🛑"},
]

COUNTRY_CHANNELS = [
    {"code": "IN", "name": "India (IN)"},
    {"code": "US", "name": "United States (US)"},
    {"code": "UK", "name": "United Kingdom (UK)"},
    {"code": "SG", "name": "Singapore (SG)"},
]

# Supported SQL / in-memory data store backends and their conventional default ports
DB_TYPES = [
    {"key": "postgresql", "label": "PostgreSQL", "icon": "🐘", "default_port": "5432"},
    {"key": "mysql", "label": "MySQL", "icon": "🐬", "default_port": "3306"},
    {"key": "redis", "label": "Redis", "icon": "🟥", "default_port": "6379"},
]

# Supported local IDE / dev-environment integrations.
# which_names: executable names to look up on PATH (via shutil.which) on Windows/Linux.
# mac_apps: .app bundle names to look for under /Applications (and ~/Applications) on macOS.
# module_fallback: a stdlib/py module that can always launch the tool via `python -m <module>`
#                   even if it isn't on PATH (only IDLE ships with every Python install).
IDE_TOOLS = [
    {
        "key": "idle", "label": "IDLE", "icon": "🐍", "desc": "Python's built-in IDE",
        "which_names": ["idle3", "idle", "idle.exe", "idle3.exe"],
        "mac_apps": [],
        "module_fallback": "idlelib.idle",
    },
    {
        "key": "pycharm", "label": "PyCharm", "icon": "🧠", "desc": "JetBrains PyCharm",
        "which_names": ["pycharm64.exe", "pycharm.exe", "pycharm", "charm"],
        "mac_apps": ["PyCharm.app", "PyCharm CE.app"],
        "module_fallback": None,
    },
    {
        "key": "spyder", "label": "Spyder", "icon": "🔬", "desc": "Scientific Python IDE",
        "which_names": ["spyder", "spyder3", "spyder.exe"],
        "mac_apps": ["Spyder.app"],
        "module_fallback": "spyder",
    },
    {
        "key": "vscode", "label": "VS Code", "icon": "🧩", "desc": "Visual Studio Code",
        "which_names": ["code", "code.cmd", "code-insiders"],
        "mac_apps": ["Visual Studio Code.app"],
        "module_fallback": None,
    },
]

async def simulate_channel_stream(country_code: str):
    await asyncio.sleep(0.1)
    return {
        "order_throughput": random.randint(1500, 8500),
        "latency_ms": round(random.uniform(0.8, 4.5), 2),
        "load_percentage": random.randint(40, 95)
    }

def _find_ide_launch_target(tool: dict):
    """Return a launch spec for an installed IDE, or None if not found.
    Checked in order: PATH executables -> macOS /Applications bundles -> python -m module."""
    for cmd in tool.get("which_names", []):
        path = shutil.which(cmd)
        if path:
            return {"kind": "exe", "path": path}

    if platform.system() == "Darwin":
        for app_name in tool.get("mac_apps", []):
            for base in ("/Applications", os.path.expanduser("~/Applications")):
                candidate = os.path.join(base, app_name)
                if os.path.exists(candidate):
                    return {"kind": "mac_app", "path": candidate}

    module_fallback = tool.get("module_fallback")
    if module_fallback and importlib.util.find_spec(module_fallback.split(".")[0]) is not None:
        return {"kind": "module", "path": module_fallback}

    return None

def _launch_target(target: dict):
    """Actually spawn the IDE as a detached local process. Best-effort: failures
    are swallowed so a launch problem doesn't crash the dashboard, but are printed
    to the server console for debugging."""
    try:
        if target["kind"] == "exe":
            subprocess.Popen([target["path"]], close_fds=True)
        elif target["kind"] == "mac_app":
            subprocess.Popen(["open", "-a", target["path"]], close_fds=True)
        elif target["kind"] == "module":
            subprocess.Popen([sys.executable, "-m", target["path"]], close_fds=True)
        return True
    except Exception as exc:
        print(f"[dev-panel] failed to launch {target}: {exc}")
        return False

async def detect_and_launch_ide(ide_key: str):
    """Look for the given IDE on this machine and, if found, actually open it.
    Runs the blocking filesystem/subprocess work off the event loop."""
    tool = next(t for t in IDE_TOOLS if t["key"] == ide_key)

    def work():
        target = _find_ide_launch_target(tool)
        if target is None:
            return False
        return _launch_target(target)

    return await asyncio.to_thread(work)

async def detect_and_launch_local_env():
    """Try every known local IDE in order and open the first one found installed.
    Returns the key of the IDE that was launched, or None if nothing was found."""
    for tool in IDE_TOOLS:
        def work(t=tool):
            target = _find_ide_launch_target(t)
            if target is None:
                return False
            return _launch_target(target)

        launched = await asyncio.to_thread(work)
        if launched:
            return tool["key"]
    return None

@component
def Navbar():
    show_notifications, set_show_notifications = use_state(False)
    show_profile, set_show_profile = use_state(False)
    watchlist, set_watchlist = use_state("NIFTY 50")
    search_query, set_search_query = use_state("")
    current_time, set_current_time = use_state(
        datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    )
    right_open, set_right_open = use_state(True)

    def toggle_right(event):
        set_right_open(not right_open)

    @use_effect(dependencies=[])
    def start_clock():
        loop = asyncio.get_event_loop()
        stopped = False

        async def tick():
            while not stopped:
                await asyncio.sleep(1)
                set_current_time(datetime.now(timezone.utc).strftime("%H:%M:%S UTC"))

        task = loop.create_task(tick())

        def cleanup():
            nonlocal stopped
            stopped = True
            task.cancel()

        return cleanup

    def pill(label, color):
        return html.div(
            {
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "6px",
                    "padding": "4px 10px",
                    "borderRadius": "999px",
                    "border": f"1px solid {COLORS['border']}",
                    "fontSize": "12px",
                    "color": COLORS["muted"],
                    "whiteSpace": "nowrap",
                }
            },
            html.span(
                {
                    "style": {
                        "width": "8px",
                        "height": "8px",
                        "borderRadius": "50%",
                        "backgroundColor": color,
                        "boxShadow": f"0 0 6px {color}",
                    }
                }
            ),
            label,
        )

    return html.header(
        {
            "style": {
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "gap": "16px",
                "padding": "10px 20px",
                "backgroundColor": COLORS["panel"],
                "borderBottom": f"1px solid {COLORS['border']}",
                "color": COLORS["text"],
                "height": "56px",
                "boxSizing": "border-box",
                "flexWrap": "nowrap",
            }
        },
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "16px"}},
            html.span(
                {
                    "style": {
                        "fontSize": "15px",
                        "fontWeight": "700",
                        "color": COLORS["accent"],
                        "letterSpacing": "0.5px",
                    }
                },
                "Barclays HFT",
            ),
            pill("Market Open", COLORS["green"]),
            pill("Feed Live", COLORS["green"]),
        ),
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "10px", "flex": "1",
                       "justifyContent": "center"}},
            html.input(
                {
                    "type": "text",
                    "placeholder": "Search symbol (e.g. RELIANCE)",
                    "value": search_query,
                    "on_change": lambda e: set_search_query(e["target"]["value"]),
                    "style": {
                        "backgroundColor": "#111116",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "6px",
                        "color": COLORS["text"],
                        "padding": "6px 10px",
                        "fontSize": "13px",
                        "width": "220px",
                        "outline": "none",
                    },
                }
            ),
            html.select(
                {
                    "value": watchlist,
                    "on_change": lambda e: set_watchlist(e["target"]["value"]),
                    "style": {
                        "backgroundColor": "#111116",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "6px",
                        "color": COLORS["text"],
                        "padding": "6px 10px",
                        "fontSize": "13px",
                    },
                },
                html.option({"value": "NIFTY 50"}, "NIFTY 50"),
                html.option({"value": "BANK NIFTY"}, "BANK NIFTY"),
                html.option({"value": "SENSEX"}, "SENSEX"),
            ),
        ),
        html.div(
            {
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "14px" if right_open else "8px",
                    "position": "relative",
                    "transition": "gap 0.2s ease-in-out",
                }
            },
            html.button(
                {
                    "on_click": toggle_right,
                    "title": "Collapse" if right_open else "Expand",
                    "style": {
                        "background": "transparent",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "6px",
                        "color": COLORS["muted"],
                        "padding": "6px 8px",
                        "cursor": "pointer",
                        "fontSize": "12px",
                        "lineHeight": "1",
                    },
                },
                "›" if right_open else "‹",
            ),
            html.div(
                {
                    "style": {
                        "textAlign": "right",
                        "fontSize": "12px",
                        "display": "flex" if right_open else "none",
                        "flexDirection": "column",
                    }
                },
                html.div({"style": {"color": COLORS["muted"]}}, "Today's P&L"),
                html.div(
                    {"style": {"color": COLORS["green"], "fontWeight": "700"}},
                    "+₹12,480.50",
                ),
            ),
            html.div(
                {
                    "style": {
                        "fontSize": "12px",
                        "color": COLORS["muted"],
                        "fontVariantNumeric": "tabular-nums",
                        "display": "block" if right_open else "none",
                    }
                },
                current_time,
            ),
            html.div(
                {"style": {"position": "relative"}},
                html.button(
                    {
                        "on_click": lambda e: set_show_notifications(not show_notifications),
                        "style": {
                            "background": "transparent",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "color": COLORS["text"],
                            "padding": "6px 10px",
                            "cursor": "pointer",
                            "fontSize": "13px",
                        },
                    },
                    "🔔",
                ),
                html.div(
                    {
                        "style": {
                            "display": "block" if show_notifications else "none",
                            "position": "absolute",
                            "right": "0",
                            "top": "36px",
                            "backgroundColor": "#111116",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "padding": "10px",
                            "width": "220px",
                            "fontSize": "12px",
                            "color": COLORS["muted"],
                            "zIndex": "20",
                        }
                    },
                    "No new alerts",
                ),
            ),
            html.div(
                {"style": {"position": "relative"}},
                html.button(
                    {
                        "on_click": lambda e: set_show_profile(not show_profile),
                        "style": {
                            "background": "transparent",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "color": COLORS["text"],
                            "padding": "6px 10px",
                            "cursor": "pointer",
                            "fontSize": "13px",
                        },
                    },
                    "👤",
                ),
                html.div(
                    {
                        "style": {
                            "display": "block" if show_profile else "none",
                            "position": "absolute",
                            "right": "0",
                            "top": "36px",
                            "backgroundColor": "#111116",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "padding": "6px",
                            "width": "140px",
                            "fontSize": "12px",
                            "zIndex": "20",
                        }
                    },
                    html.div({"style": {"padding": "6px", "cursor": "pointer"}}, "Settings"),
                    html.div({"style": {"padding": "6px", "cursor": "pointer"}}, "API Keys"),
                    html.div({"style": {"padding": "6px", "cursor": "pointer", "color": COLORS["red"]}}, "Logout"),
                ),
            ),
        ),
    )

@component
def Dashboard():
    is_open, set_is_open = use_state(True)
    sidebar_width = "200px" if is_open else "60px"
    active_topic, set_active_topic = use_state(QUANT_TOPICS[0]["key"])

    # New dedicated tracking state for selected HFT microstructural signal parameters
    active_signal, set_active_signal = use_state(HFT_SIGNALS[0]["key"])

    active_country, set_active_country = use_state("IN")
    channel_metrics, set_channel_metrics = use_state({
        "order_throughput": 0, "latency_ms": 0.0, "load_percentage": 0
    })

    def toggle_sidebar(event):
        set_is_open(not is_open)

    right_is_open, set_right_is_open = use_state(True)
    # Scaled out sidebar slightly to prevent aggressive wrapping of longer labels
    right_sidebar_width = "220px" if right_is_open else "60px"

    def toggle_right_sidebar(event):
        set_right_is_open(not right_is_open)

    # --- SQL Database connection panel state ---
    show_db_panel, set_show_db_panel = use_state(False)
    selected_db_type, set_selected_db_type = use_state(DB_TYPES[0]["key"])
    db_hostname, set_db_hostname = use_state("localhost")
    db_port, set_db_port = use_state(DB_TYPES[0]["default_port"])
    db_name, set_db_name = use_state("")
    db_username, set_db_username = use_state("")
    db_password, set_db_password = use_state("")
    db_disk_location, set_db_disk_location = use_state("")
    db_connection_status, set_db_connection_status = use_state("disconnected")

    def toggle_db_panel(event):
        set_show_db_panel(not show_db_panel)

    def choose_db_type(event, key=None, default_port=None):
        set_selected_db_type(key)
        set_db_port(default_port)
        set_db_connection_status("disconnected")

    def handle_connect(event):
        # Placeholder for wiring up an actual backend connection call
        set_db_connection_status("connected")

    def handle_disconnect(event):
        set_db_connection_status("disconnected")

    # --- Development / IDE connection panel state ---
    show_dev_panel, set_show_dev_panel = use_state(False)
    ide_status, set_ide_status = use_state({t["key"]: "disconnected" for t in IDE_TOOLS})
    local_env_status, set_local_env_status = use_state("idle")  # idle | checking | found | not_found | connected

    def toggle_dev_panel(event):
        set_show_dev_panel(not show_dev_panel)

    def handle_ide_connect(event, key=None):
        loop = asyncio.get_event_loop()

        async def run_launch():
            set_ide_status({**ide_status, key: "checking"})
            launched = await detect_and_launch_ide(key)
            set_ide_status({**ide_status, key: "connected" if launched else "not_found"})

        loop.create_task(run_launch())

    def handle_ide_disconnect(event, key=None):
        set_ide_status({**ide_status, key: "disconnected"})

    def handle_local_env_connect(event):
        loop = asyncio.get_event_loop()

        async def run_launch():
            set_local_env_status("checking")
            launched_key = await detect_and_launch_local_env()
            if launched_key:
                set_local_env_status("connected")
                set_ide_status({**ide_status, launched_key: "connected"})
            else:
                set_local_env_status("not_found")

        loop.create_task(run_launch())

    def handle_local_env_disconnect(event):
        set_local_env_status("idle")

    @use_effect(dependencies=[active_country])
    def handle_channel_stream():
        loop = asyncio.get_event_loop()
        is_stopped = False

        async def active_stream_runner():
            while not is_stopped:
                fresh_data = await simulate_channel_stream(active_country)
                set_channel_metrics(fresh_data)
                await asyncio.sleep(1.5)

        task = loop.create_task(active_stream_runner())

        def cleanup():
            nonlocal is_stopped
            is_stopped = True
            task.cancel()

        return cleanup

    def topic_button(topic, is_open_flag):
        is_active = topic["key"] == active_topic

        def on_click(event, key=topic["key"]):
            set_active_topic(key)

        return html.button(
            {
                "on_click": on_click,
                "title": topic["label"],
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center" if not is_open_flag else "flex-start",
                    "gap": "10px",
                    "width": "100%",
                    "padding": "8px 10px",
                    "backgroundColor": "#111116" if is_active else "transparent",
                    "border": f"1px solid {COLORS['accent'] if is_active else COLORS['border']}",
                    "borderRadius": "6px",
                    "color": COLORS["accent"] if is_active else COLORS["text"],
                    "cursor": "pointer",
                    "fontSize": "12px",
                    "fontWeight": "600" if is_active else "400",
                    "boxSizing": "border-box",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            },
            html.span({"style": {"width": "16px", "textAlign": "center", "flexShrink": "0"}}, topic["icon"]),
            html.span(
                {"style": {"display": "inline" if is_open_flag else "none"}},
                topic["label"],
            ),
        )

    # Reusable button layout handler for generating dynamic HFT signals list items
    def signal_button(signal, is_open_flag):
        is_active = signal["key"] == active_signal

        def on_click(event, key=signal["key"]):
            set_active_signal(key)

        return html.button(
            {
                "on_click": on_click,
                "title": signal["label"],
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center" if not is_open_flag else "flex-start",
                    "gap": "10px",
                    "width": "100%",
                    "padding": "8px 10px",
                    "backgroundColor": "#111116" if is_active else "transparent",
                    "border": f"1px solid {COLORS['accent'] if is_active else COLORS['border']}",
                    "borderRadius": "6px",
                    "color": COLORS["accent"] if is_active else COLORS["text"],
                    "cursor": "pointer",
                    "fontSize": "11px",
                    "fontWeight": "600" if is_active else "400",
                    "boxSizing": "border-box",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            },
            html.span({"style": {"width": "16px", "textAlign": "center", "flexShrink": "0"}}, signal["icon"]),
            html.span(
                {"style": {"display": "inline" if is_open_flag else "none"}},
                signal["label"],
            ),
        )

    # Button that opens the SQL / data-store connection panel
    def db_toggle_button(is_open_flag):
        return html.button(
            {
                "on_click": toggle_db_panel,
                "title": "SQL Database Connections",
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center" if not is_open_flag else "flex-start",
                    "gap": "10px",
                    "width": "100%",
                    "padding": "8px 10px",
                    "backgroundColor": "#111116" if show_db_panel else "transparent",
                    "border": f"1px solid {COLORS['accent'] if show_db_panel else COLORS['border']}",
                    "borderRadius": "6px",
                    "color": COLORS["accent"] if show_db_panel else COLORS["text"],
                    "cursor": "pointer",
                    "fontSize": "11px",
                    "fontWeight": "600" if show_db_panel else "400",
                    "boxSizing": "border-box",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            },
            html.span({"style": {"width": "16px", "textAlign": "center", "flexShrink": "0"}}, "🗄️"),
            html.span(
                {"style": {"display": "inline" if is_open_flag else "none"}},
                "SQL Database",
            ),
        )

    # Button that opens the Development / IDE connection panel
    def dev_toggle_button(is_open_flag):
        return html.button(
            {
                "on_click": toggle_dev_panel,
                "title": "Development",
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center" if not is_open_flag else "flex-start",
                    "gap": "10px",
                    "width": "100%",
                    "padding": "8px 10px",
                    "backgroundColor": "#111116" if show_dev_panel else "transparent",
                    "border": f"1px solid {COLORS['accent'] if show_dev_panel else COLORS['border']}",
                    "borderRadius": "6px",
                    "color": COLORS["accent"] if show_dev_panel else COLORS["text"],
                    "cursor": "pointer",
                    "fontSize": "11px",
                    "fontWeight": "600" if show_dev_panel else "400",
                    "boxSizing": "border-box",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            },
            html.span({"style": {"width": "16px", "textAlign": "center", "flexShrink": "0"}}, "💻"),
            html.span(
                {"style": {"display": "inline" if is_open_flag else "none"}},
                "Development",
            ),
        )

    # One tab per supported backend inside the connection panel
    def db_type_tab(db_type):
        is_active = db_type["key"] == selected_db_type

        def on_click(event, key=db_type["key"], default_port=db_type["default_port"]):
            choose_db_type(event, key=key, default_port=default_port)

        return html.button(
            {
                "on_click": on_click,
                "style": {
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "6px",
                    "flex": "1",
                    "padding": "8px 6px",
                    "justifyContent": "center",
                    "backgroundColor": "#1A1A20" if is_active else "transparent",
                    "border": f"1px solid {COLORS['accent'] if is_active else COLORS['border']}",
                    "borderRadius": "6px",
                    "color": COLORS["accent"] if is_active else COLORS["muted"],
                    "cursor": "pointer",
                    "fontSize": "12px",
                    "fontWeight": "600" if is_active else "400",
                },
            },
            html.span({}, db_type["icon"]),
            html.span({}, db_type["label"]),
        )

    def db_field(label, value, on_change, placeholder="", input_type="text"):
        return html.div(
            {"style": {"display": "flex", "flexDirection": "column", "gap": "4px"}},
            html.label(
                {"style": {"fontSize": "11px", "color": COLORS["muted"], "fontWeight": "600"}},
                label,
            ),
            html.input(
                {
                    "type": input_type,
                    "value": value,
                    "placeholder": placeholder,
                    "on_change": on_change,
                    "style": {
                        "backgroundColor": "#111116",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "6px",
                        "color": COLORS["text"],
                        "padding": "8px 10px",
                        "fontSize": "12px",
                        "outline": "none",
                        "boxSizing": "border-box",
                        "width": "100%",
                    },
                }
            ),
        )

    def db_config_panel():
        active_db_label = next(d["label"] for d in DB_TYPES if d["key"] == selected_db_type)
        is_connected = db_connection_status == "connected"

        return html.div(
            {
                "style": {
                    "position": "fixed",
                    "top": "66px",
                    "right": "20px",
                    "width": "320px",
                    "backgroundColor": COLORS["panel"],
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "10px",
                    "padding": "16px",
                    "boxShadow": "0 8px 24px rgba(0,0,0,0.5)",
                    "zIndex": "50",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "12px",
                }
            },
            html.div(
                {"style": {"display": "flex", "justifyContent": "space-between", "alignItems": "center"}},
                html.span(
                    {"style": {"fontSize": "13px", "fontWeight": "700", "color": COLORS["text"]}},
                    "Database Connection",
                ),
                html.button(
                    {
                        "on_click": toggle_db_panel,
                        "style": {
                            "background": "transparent",
                            "border": "none",
                            "color": COLORS["muted"],
                            "cursor": "pointer",
                            "fontSize": "14px",
                        },
                    },
                    "✕",
                ),
            ),
            html.div(
                {"style": {"display": "flex", "gap": "6px"}},
                *[db_type_tab(db_type) for db_type in DB_TYPES],
            ),
            db_field("Hostname", db_hostname, lambda e: set_db_hostname(e["target"]["value"]), placeholder="localhost"),
            db_field("Port", db_port, lambda e: set_db_port(e["target"]["value"]), placeholder="e.g. 5432"),
            db_field(
                "Database / Index Name" if selected_db_type != "redis" else "Redis DB Index",
                db_name,
                lambda e: set_db_name(e["target"]["value"]),
                placeholder="trading_db",
            ),
            db_field("Username", db_username, lambda e: set_db_username(e["target"]["value"]), placeholder="admin"),
            db_field(
                "Password",
                db_password,
                lambda e: set_db_password(e["target"]["value"]),
                placeholder="••••••••",
                input_type="password",
            ),
            db_field(
                "Local Disk Location",
                db_disk_location,
                lambda e: set_db_disk_location(e["target"]["value"]),
                placeholder="/var/lib/postgresql/data" if selected_db_type != "redis" else "/var/lib/redis/dump.rdb",
            ),
            html.div(
                {"style": {"display": "flex", "alignItems": "center", "gap": "6px", "fontSize": "11px",
                           "color": COLORS["green"] if is_connected else COLORS["muted"]}},
                html.span(
                    {
                        "style": {
                            "width": "8px",
                            "height": "8px",
                            "borderRadius": "50%",
                            "backgroundColor": COLORS["green"] if is_connected else COLORS["muted"],
                        }
                    }
                ),
                f"{active_db_label} — {'Connected' if is_connected else 'Disconnected'}",
            ),
            html.div(
                {"style": {"display": "flex", "gap": "8px"}},
                html.button(
                    {
                        "on_click": handle_connect,
                        "style": {
                            "flex": "1",
                            "padding": "8px 10px",
                            "backgroundColor": COLORS["accent"],
                            "border": "none",
                            "borderRadius": "6px",
                            "color": "#00131A",
                            "fontWeight": "700",
                            "fontSize": "12px",
                            "cursor": "pointer",
                        },
                    },
                    "Connect",
                ),
                html.button(
                    {
                        "on_click": handle_disconnect,
                        "style": {
                            "flex": "1",
                            "padding": "8px 10px",
                            "backgroundColor": "transparent",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "color": COLORS["muted"],
                            "fontWeight": "600",
                            "fontSize": "12px",
                            "cursor": "pointer",
                        },
                    },
                    "Disconnect",
                ),
            ),
        )

    def ide_status_dot(status):
        color_map = {
            "connected": COLORS["green"],
            "checking": COLORS["accent"],
            "not_found": COLORS["red"],
            "disconnected": COLORS["muted"],
            "idle": COLORS["muted"],
        }
        return html.span(
            {
                "style": {
                    "width": "8px",
                    "height": "8px",
                    "borderRadius": "50%",
                    "backgroundColor": color_map.get(status, COLORS["muted"]),
                    "flexShrink": "0",
                }
            }
        )

    def ide_status_label(status):
        return {
            "connected": "Opened ✓",
            "checking": "Searching…",
            "not_found": "Not installed",
            "disconnected": "Disconnected",
            "idle": "Idle",
        }.get(status, status)

    def ide_row(ide):
        status = ide_status.get(ide["key"], "disconnected")
        is_connected = status == "connected"
        is_checking = status == "checking"

        return html.div(
            {
                "style": {
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                    "padding": "10px",
                    "backgroundColor": "#111116",
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "8px",
                }
            },
            html.div(
                {"style": {"display": "flex", "alignItems": "center", "justifyContent": "space-between"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px"}},
                    html.span({"style": {"fontSize": "16px"}}, ide["icon"]),
                    html.div(
                        {"style": {"display": "flex", "flexDirection": "column"}},
                        html.span({"style": {"fontSize": "12px", "fontWeight": "700", "color": COLORS["text"]}},
                                  ide["label"]),
                        html.span({"style": {"fontSize": "10px", "color": COLORS["muted"]}}, ide["desc"]),
                    ),
                ),
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "6px"}},
                    ide_status_dot(status),
                    html.span({"style": {"fontSize": "10px", "color": COLORS["muted"]}}, ide_status_label(status)),
                ),
            ),
            html.div(
                {"style": {"display": "flex", "gap": "6px"}},
                html.button(
                    {
                        "on_click": lambda e, key=ide["key"]: handle_ide_connect(e, key=key),
                        "disabled": is_checking,
                        "style": {
                            "flex": "1",
                            "padding": "6px 8px",
                            "backgroundColor": COLORS["accent"] if not is_connected else "transparent",
                            "border": f"1px solid {COLORS['accent']}" if is_connected else "none",
                            "borderRadius": "6px",
                            "color": "#00131A" if not is_connected else COLORS["accent"],
                            "fontWeight": "700",
                            "fontSize": "11px",
                            "cursor": "pointer" if not is_checking else "default",
                        },
                    },
                    "Searching…" if is_checking else ("Reconnect" if is_connected else "Connect"),
                ),
                html.button(
                    {
                        "on_click": lambda e, key=ide["key"]: handle_ide_disconnect(e, key=key),
                        "style": {
                            "flex": "1",
                            "padding": "6px 8px",
                            "backgroundColor": "transparent",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "color": COLORS["muted"],
                            "fontWeight": "600",
                            "fontSize": "11px",
                            "cursor": "pointer",
                        },
                    },
                    "Disconnect",
                ),
            ),
        )

    def local_env_panel():
        is_checking = local_env_status == "checking"
        is_connected = local_env_status == "connected"

        return html.div(
            {
                "style": {
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                    "padding": "10px",
                    "backgroundColor": "#111116",
                    "border": f"1px solid {COLORS['accent']}",
                    "borderRadius": "8px",
                }
            },
            html.div(
                {"style": {"display": "flex", "alignItems": "center", "justifyContent": "space-between"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px"}},
                    html.span({"style": {"fontSize": "16px"}}, "🖥️"),
                    html.div(
                        {"style": {"display": "flex", "flexDirection": "column"}},
                        html.span({"style": {"fontSize": "12px", "fontWeight": "700", "color": COLORS["text"]}},
                                  "Local Desktop Environment"),
                        html.span({"style": {"fontSize": "10px", "color": COLORS["muted"]}},
                                  "Auto-detect & connect if installed"),
                    ),
                ),
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "6px"}},
                    ide_status_dot(local_env_status),
                    html.span({"style": {"fontSize": "10px", "color": COLORS["muted"]}},
                              ide_status_label(local_env_status)),
                ),
            ),
            html.div(
                {"style": {"display": "flex", "gap": "6px"}},
                html.button(
                    {
                        "on_click": handle_local_env_connect,
                        "disabled": is_checking,
                        "style": {
                            "flex": "1",
                            "padding": "6px 8px",
                            "backgroundColor": COLORS["accent"] if not is_connected else "transparent",
                            "border": f"1px solid {COLORS['accent']}" if is_connected else "none",
                            "borderRadius": "6px",
                            "color": "#00131A" if not is_connected else COLORS["accent"],
                            "fontWeight": "700",
                            "fontSize": "11px",
                            "cursor": "pointer" if not is_checking else "default",
                        },
                    },
                    "Detecting…" if is_checking else ("Reconnect" if is_connected else "Detect & Connect"),
                ),
                html.button(
                    {
                        "on_click": handle_local_env_disconnect,
                        "style": {
                            "flex": "1",
                            "padding": "6px 8px",
                            "backgroundColor": "transparent",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "6px",
                            "color": COLORS["muted"],
                            "fontWeight": "600",
                            "fontSize": "11px",
                            "cursor": "pointer",
                        },
                    },
                    "Disconnect",
                ),
            ),
        )

    def dev_config_panel():
        return html.div(
            {
                "style": {
                    "position": "fixed",
                    "top": "66px",
                    "left": "20px",
                    "width": "320px",
                    "backgroundColor": COLORS["panel"],
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "10px",
                    "padding": "16px",
                    "boxShadow": "0 8px 24px rgba(0,0,0,0.5)",
                    "zIndex": "50",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "12px",
                    "maxHeight": "80vh",
                    "overflowY": "auto",
                }
            },
            html.div(
                {"style": {"display": "flex", "justifyContent": "space-between", "alignItems": "center"}},
                html.span(
                    {"style": {"fontSize": "13px", "fontWeight": "700", "color": COLORS["text"]}},
                    "Development Environment",
                ),
                html.button(
                    {
                        "on_click": toggle_dev_panel,
                        "style": {
                            "background": "transparent",
                            "border": "none",
                            "color": COLORS["muted"],
                            "cursor": "pointer",
                            "fontSize": "14px",
                        },
                    },
                    "✕",
                ),
            ),
            html.div(
                {
                    "style": {
                        "fontSize": "11px",
                        "color": COLORS["muted"],
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.4px",
                    }
                },
                "Local Environment",
            ),
            local_env_panel(),
            html.div(
                {
                    "style": {
                        "fontSize": "11px",
                        "color": COLORS["muted"],
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.4px",
                        "marginTop": "4px",
                    }
                },
                "IDE Connections",
            ),
            *[ide_row(ide) for ide in IDE_TOOLS],
        )

    def sidebar_nav(is_open_flag, toggle_fn, width, border_side, title, show_topics=False, show_signals=False,
                     show_db_button=False, show_dev_button=False):
        children = [
            html.div(
                {
                    "on_click": toggle_fn,
                    "title": title,
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "center",
                        "gap": "6px",
                        "textAlign": "center",
                        "cursor": "pointer",
                        "userSelect": "none",
                        "width": "100%"
                    },
                },
                html.img(
                    {
                        "src": "/static/BarclaysHFT.png",
                        "style": {"width": "40px", "height": "38px"},
                    }
                ),
            )
        ]

        if show_topics:
            children.append(
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "6px",
                            "width": "100%",
                        }
                    },
                    *[topic_button(topic, is_open_flag) for topic in QUANT_TOPICS],
                )
            )

        # Development / IDE connectivity section on the left sidebar
        if show_dev_button:
            children.append(
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "6px",
                            "width": "100%",
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "fontSize": "11px",
                                "color": COLORS["muted"],
                                "fontWeight": "700",
                                "marginBottom": "4px",
                                "textAlign": "left",
                                "paddingLeft": "4px",
                                "display": "block" if is_open_flag else "none"
                            }
                        },
                        "DEVELOPMENT"
                    ),
                    dev_toggle_button(is_open_flag),
                )
            )

        # Append execution items when right-hand navigation configuration is true
        if show_signals:
            children.append(
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "6px",
                            "width": "100%",
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "fontSize": "11px",
                                "color": COLORS["muted"],
                                "fontWeight": "700",
                                "marginBottom": "4px",
                                "textAlign": "left",
                                "paddingLeft": "4px",
                                "display": "block" if is_open_flag else "none"
                            }
                        },
                        "HFT FEED SIGNALS"
                    ),
                    *[signal_button(sig, is_open_flag) for sig in HFT_SIGNALS],
                )
            )

        # Data-store connectivity section: opens the SQL Database connection panel
        if show_db_button:
            children.append(
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "6px",
                            "width": "100%",
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "fontSize": "11px",
                                "color": COLORS["muted"],
                                "fontWeight": "700",
                                "marginBottom": "4px",
                                "textAlign": "left",
                                "paddingLeft": "4px",
                                "display": "block" if is_open_flag else "none"
                            }
                        },
                        "DATA STORE"
                    ),
                    db_toggle_button(is_open_flag),
                )
            )

        return html.nav(
            {
                "style": {
                    "width": width,
                    "backgroundColor": COLORS["panel"],
                    "minHeight": "100%",
                    "padding": "20px 10px",
                    "boxSizing": "border-box",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "gap": "20px",
                    border_side: f"1px solid {COLORS['border']}",
                    "transition": "width 0.2s ease-in-out",
                }
            },
            *children,
        )

    return html.div(
        {
            "style": {
                "backgroundColor": COLORS["bg"],
                "minHeight": "100vh",
                "width": "100%",
                "margin": "0",
                "padding": "0",
                "boxSizing": "border-box",
                "display": "flex",
                "flexDirection": "column",
            }
        },
        html.style(
            """
            html, body {
                margin: 0;
                padding: 0;
                height: 100%;
                background-color: #1E1E24;
            }
            """
        ),
        Navbar(),
        html.div(
            {"style": {"display": "flex", "flex": "1", "minHeight": "0"}},
            sidebar_nav(
                is_open,
                toggle_sidebar,
                sidebar_width,
                "borderRight",
                "Collapse sidebar" if is_open else "Expand sidebar",
                show_topics=True,
                show_dev_button=True,
            ),

            html.main(
                {"style": {"flex": "1", "padding": "30px", "color": COLORS["text"], "fontFamily": "sans-serif"}},
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "justifyContent": "between",
                            "alignItems": "center",
                            "marginBottom": "20px"
                        }
                    },
                    html.div(
                        {"style": {"flex": "1"}},
                        html.h2({"style": {"margin": "0"}}, "HFT Quant Engine Status"),
                        html.p(
                            {"style": {"color": COLORS["muted"], "margin": "4px 0 0 0", "fontSize": "13px"}},
                            f"Focus Field: {next(t['label'] for t in QUANT_TOPICS if t['key'] == active_topic)} | Active Metric: {next(s['label'] for s in HFT_SIGNALS if s['key'] == active_signal)}",
                        ),
                    ),

                    html.div(
                        {"style": {"display": "flex", "alignItems": "center", "gap": "10px"}},
                        html.span({"style": {"fontSize": "13px", "color": COLORS["muted"]}}, "Active Feed Channel:"),
                        html.select(
                            {
                                "value": active_country,
                                "on_change": lambda e: set_active_country(e["target"]["value"]),
                                "style": {
                                    "backgroundColor": COLORS["panel"],
                                    "border": f"1px solid {COLORS['border']}",
                                    "borderRadius": "6px",
                                    "color": COLORS["accent"],
                                    "padding": "8px 12px",
                                    "fontSize": "13px",
                                    "fontWeight": "600",
                                    "outline": "none",
                                    "cursor": "pointer"
                                }
                            },
                            *[html.option({"value": item["code"]}, item["name"]) for item in COUNTRY_CHANNELS]
                        )
                    )
                ),

                html.hr({"style": {"border": f"0.5px solid {COLORS['border']}", "margin": "20px 0"}}),

                html.div(
                    {
                        "style": {
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                            "gap": "20px",
                            "marginTop": "20px"
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "backgroundColor": COLORS["panel"],
                                "border": f"1px solid {COLORS['border']}",
                                "padding": "20px",
                                "borderRadius": "8px"
                            }
                        },
                        html.div({"style": {"color": COLORS["muted"], "fontSize": "12px", "fontWeight": "600"}},
                                 "ORDER THROUGHPUT"),
                        html.div({"style": {"fontSize": "28px", "fontWeight": "700", "color": COLORS["text"],
                                            "marginTop": "8px", "fontVariantNumeric": "tabular-nums"}},
                                 f"{channel_metrics['order_throughput']} msg/s"),
                        html.div({"style": {"color": COLORS["green"], "fontSize": "11px", "marginTop": "6px"}},
                                 f"● Channel {active_country} Live Stream Active")
                    ),
                    html.div(
                        {
                            "style": {
                                "backgroundColor": COLORS["panel"],
                                "border": f"1px solid {COLORS['border']}",
                                "padding": "20px",
                                "borderRadius": "8px"
                            }
                        },
                        html.div({"style": {"color": COLORS["muted"], "fontSize": "12px", "fontWeight": "600"}},
                                 "TICK INGESTION LATENCY"),
                        html.div({"style": {"fontSize": "28px", "fontWeight": "700", "color": COLORS["accent"],
                                            "marginTop": "8px", "fontVariantNumeric": "tabular-nums"}},
                                 f"{channel_metrics['latency_ms']} ms"),
                        html.div({"style": {"color": COLORS["muted"], "fontSize": "11px", "marginTop": "6px"}},
                                 "Sub-millisecond Kernel Mode Optimized")
                    ),
                    html.div(
                        {
                            "style": {
                                "backgroundColor": COLORS["panel"],
                                "border": f"1px solid {COLORS['border']}",
                                "padding": "20px",
                                "borderRadius": "8px"
                            }
                        },
                        html.div({"style": {"color": COLORS["muted"], "fontSize": "12px", "fontWeight": "600"}},
                                 "GATEWAY LOAD CAPACITY"),
                        html.div({"style": {"fontSize": "28px", "fontWeight": "700",
                                            "color": COLORS["red"] if channel_metrics['load_percentage'] > 85 else
                                            COLORS["text"], "marginTop": "8px", "fontVariantNumeric": "tabular-nums"}},
                                 f"{channel_metrics['load_percentage']}%"),
                        html.div({"style": {"color": COLORS["muted"], "fontSize": "11px", "marginTop": "6px"}},
                                 "Broker cluster assignment nodes")
                    )
                )
            ),

            # Updated Right Sidebar Nav containing the HFT metric parameters buttons array
            # and the SQL Database connection entry point
            sidebar_nav(
                right_is_open,
                toggle_right_sidebar,
                right_sidebar_width,
                "borderLeft",
                "Collapse sidebar" if right_is_open else "Expand sidebar",
                show_signals=True,
                show_db_button=True,
            ),
            db_config_panel() if show_db_panel else html.div({"style": {"display": "none"}}),
            dev_config_panel() if show_dev_panel else html.div({"style": {"display": "none"}}),
        ),
)
