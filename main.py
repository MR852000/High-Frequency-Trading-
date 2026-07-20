import asyncio
import concurrent.futures
import os
import random
import re
import shutil
import subprocess
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from reactpy import component, html, use_effect, use_state
from reactpy.backend.fastapi import configure

app = FastAPI()

# Mount static directory for local images (creates directory if missing)
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Dedicated Background Thread Pool for Instant Non-Blocking IDE Launches
ide_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Shared Styles & Themes
LOGO_BTN_STYLE = {
    "background": "transparent",
    "border": "none",
    "cursor": "pointer",
    "padding": "0",
    "display": "block",
    "margin": "0 auto 16px auto",
    "outline": "none"
}

LOGO_IMG_STYLE = {
    "width": "42px",
    "height": "42px",
    "objectFit": "contain",
    "mixBlendMode": "screen",
    "transition": "transform 0.2s ease"
}

SIDEBAR_BTN_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "10px",
    "width": "100%",
    "padding": "10px 14px",
    "marginBottom": "8px",
    "backgroundColor": "#0F172A",
    "border": "1px solid #1E293B",
    "borderRadius": "8px",
    "color": "#94A3B8",
    "fontSize": "13px",
    "fontWeight": "500",
    "cursor": "pointer",
    "textAlign": "left",
    "boxSizing": "border-box",
    "whiteSpace": "nowrap"
}

SIDEBAR_BTN_ACTIVE = {
    **SIDEBAR_BTN_STYLE,
    "backgroundColor": "#1E293B",
    "borderColor": "#38BDF8",
    "color": "#38BDF8"
}

SUB_LINK_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "10px",
    "width": "100%",
    "padding": "8px 14px 8px 32px",
    "marginBottom": "6px",
    "backgroundColor": "#090D16",
    "border": "1px solid #1E293B",
    "borderRadius": "6px",
    "color": "#94A3B8",
    "fontSize": "12px",
    "fontWeight": "500",
    "cursor": "pointer",
    "textDecoration": "none",
    "boxSizing": "border-box",
    "whiteSpace": "nowrap",
    "transition": "all 0.2s ease"
}

SUB_LINK_ACTIVE = {
    **SUB_LINK_STYLE,
    "backgroundColor": "#1E293B",
    "borderColor": "#38BDF8",
    "color": "#38BDF8"
}

CLOUD_ICON_STYLE = {
    "width": "18px",
    "height": "18px",
    "objectFit": "contain",
    "borderRadius": "2px"
}

SECTION_LABEL = {
    "fontSize": "11px",
    "fontWeight": "bold",
    "color": "#64748B",
    "letterSpacing": "1px",
    "marginTop": "20px",
    "marginBottom": "10px",
    "paddingLeft": "4px",
    "whiteSpace": "nowrap"
}

INPUT_STYLE = {
    "width": "100%",
    "backgroundColor": "#0F172A",
    "border": "1px solid #1E293B",
    "borderRadius": "6px",
    "padding": "10px 14px",
    "color": "#F8FAFC",
    "fontSize": "13px",
    "boxSizing": "border-box",
    "outline": "none"
}


# Direct execution worker for thread pool
def _spawn_process(executable: str, filepath: str = None):
    """Spawns process completely hidden without launching a cmd window."""
    try:
        args = [executable]
        if filepath:
            args.append(filepath)

        if os.name == "nt":
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            creation_flags = DETACHED_PROCESS | CREATE_NO_WINDOW

            subprocess.Popen(
                args,
                shell=False,
                creationflags=creation_flags,
                close_fds=True
            )
        else:
            subprocess.Popen(
                args,
                start_new_session=True,
                close_fds=True
            )
        print(f"[IDE Launcher]: Process spawned cleanly -> {executable} {filepath or ''}")
    except Exception as err:
        print(f"[IDE Launcher Error]: Failed spawning process '{executable}': {err}")


# Ultra-low latency asynchronous launcher
def launch_ide(ide_key: str, filepath: str = None):
    """Instantly locates and launches IDEs on local desktop with target script."""
    # Ensure script file exists if a path is provided
    if filepath and not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        filename = os.path.basename(filepath)
        with open(filepath, "w") as f:
            if "reconciliation" in filename:
                f.write("# Real-Time Reconciliation Engine\n")
                f.write("# Auto-generated module for Barclays Ledger Engine\n\n")
                f.write("def reconcile_accounts(internal_ledger: dict, external_bank_feed: dict):\n")
                f.write("    \"\"\"Compares internal ledger entries against external bank statements.\"\"\"\n")
                f.write("    discrepancies = []\n")
                f.write("    for tx_id, amount in internal_ledger.items():\n")
                f.write("        if tx_id not in external_bank_feed:\n")
                f.write("            discrepancies.append((tx_id, 'Missing in Bank Feed'))\n")
                f.write("        elif external_bank_feed[tx_id] != amount:\n")
                f.write("            discrepancies.append((tx_id, 'Amount Mismatch'))\n")
                f.write("    return discrepancies\n")
            else:
                f.write("# Double-Entry Accounting Logic Script\n")
                f.write("# Auto-generated module for Barclays Ledger Engine\n\n")
                f.write("def record_transaction(debit_acct: str, credit_acct: str, amount: float):\n")
                f.write("    if amount <= 0:\n")
                f.write("        raise ValueError('Transaction amount must be positive')\n")
                f.write("    print(f'Debited {amount} from {debit_acct}, Credited to {credit_acct}')\n")

    fast_paths = {
        "vscode": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe"
        ],
        "pycharm": [
            r"C:\Program Files\JetBrains\PyCharm Community Edition\bin\pycharm64.exe",
            r"C:\Program Files\JetBrains\PyCharm Professional\bin\pycharm64.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\PyCharm Community\bin\pycharm64.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\JetBrains\Toolbox\apps\PyCharm-C\ch-0\bin\pycharm64.exe")
        ],
        "spyder": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\Scripts\spyder.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\Scripts\spyder.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\anaconda3\Scripts\spyder.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\anaconda3\pythonw.exe")
        ]
    }

    candidates = fast_paths.get(ide_key, [])

    for candidate in candidates:
        if os.path.isfile(candidate):
            ide_executor.submit(_spawn_process, candidate, filepath)
            print(f"[Fast Launch Triggered]: {ide_key.upper()} via '{candidate}'")
            return

    fallback_names = {
        "vscode": "Code.exe",
        "pycharm": "pycharm64.exe",
        "spyder": "spyder.exe"
    }

    path_exe = shutil.which(fallback_names.get(ide_key, ""))
    if path_exe:
        ide_executor.submit(_spawn_process, path_exe, filepath)
        print(f"[PATH Launch Triggered]: {ide_key.upper()} via '{path_exe}'")
        return

    print(f"[IDE Launcher Warning]: Could not resolve executable for {ide_key.upper()}. Check installation path.")


# ------------------------------------------------------------------
# COMPONENT 1: Top Navigation Bar
# ------------------------------------------------------------------
@component
def TopHeader(settlement_vol, utc_time):
    return html.header(
        {"style": {
            "height": "56px",
            "backgroundColor": "#090D16",
            "borderBottom": "1px solid #1E293B",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "0 20px",
            "zIndex": "10"
        }},
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "12px"}},
            html.span({"style": {"color": "#38BDF8", "fontWeight": "bold", "fontSize": "16px"}}, "Barclays Ledger"),
            html.span({"style": {"backgroundColor": "#064E3B", "color": "#34D399", "padding": "2px 8px",
                                 "borderRadius": "12px", "fontSize": "11px", "fontWeight": "600"}}, "● Engine Active"),
            html.span({"style": {"backgroundColor": "#064E3B", "color": "#34D399", "padding": "2px 8px",
                                 "borderRadius": "12px", "fontSize": "11px", "fontWeight": "600"}}, "● Sync Live")
        ),
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "12px"}},
            html.input({
                "type": "text",
                "placeholder": "Search Ledger TX Hash / Account...",
                "style": {
                    "backgroundColor": "#0F172A",
                    "border": "1px solid #1E293B",
                    "borderRadius": "6px",
                    "padding": "6px 12px",
                    "color": "#F8FAFC",
                    "width": "260px",
                    "fontSize": "13px"
                }
            }),
            html.select(
                {"style": {"backgroundColor": "#0F172A", "border": "1px solid #1E293B", "color": "#F8FAFC",
                           "padding": "6px 12px", "borderRadius": "6px", "fontSize": "13px"}},
                html.option("Region: UK Main Ledger"),
                html.option("Region: US Core Ledger"),
                html.option("Region: APAC Sync")
            )
        ),
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "16px", "fontSize": "12px"}},
            html.div(
                html.span({"style": {"color": "#94A3B8"}}, "Settlement Volume: "),
                html.span(
                    {"style": {"color": "#4ADE80", "fontWeight": "bold", "fontSize": "13px"}},
                    f"£{settlement_vol:,.2f}M"
                )
            ),
            html.span({"style": {"color": "#94A3B8"}}, f"{utc_time} UTC"),
            html.span({"style": {"cursor": "pointer"}}, "🔔"),
            html.span({"style": {"cursor": "pointer"}}, "👤")
        )
    )


# ------------------------------------------------------------------
# COMPONENT 2: Left Navigation Sidebar
# ------------------------------------------------------------------
@component
def LeftSidebar(active_item, set_active_item, is_open, toggle_open):
    is_cloud_open, set_cloud_open = use_state(True)
    is_health_open, set_health_open = use_state(False)

    items = [
        ("double_entry", "∑", "Double-Entry Accounting"),
        ("reconciliation", "P", "Real-Time Reconciliation"),
        ("balance_validation", "σ", "Balance Integrity"),
        ("audit_trail", "∫", "Immutable Audit Logs"),
        ("queue_mgmt", "∇", "Transaction Queueing"),
        ("settlement", "∀", "Settlement Engine"),
    ]

    def make_handler(item_id):
        def handler(e):
            set_active_item(item_id)

            # 1. Launch Spyder for Double-Entry Accounting
            if item_id == "double_entry":
                script_path = os.path.abspath("scripts/double_entry_logic.py")
                launch_ide("spyder", script_path)

            # 2. Launch Spyder for Real-Time Reconciliation
            elif item_id == "reconciliation":
                script_path = os.path.abspath("scripts/reconciliation_engine.py")
                launch_ide("spyder", script_path)

        return handler

    def toggle_cloud(e):
        set_cloud_open(not is_cloud_open)

    def toggle_health(e):
        set_health_open(not is_health_open)

    return html.aside(
        {"style": {
            "width": "230px" if is_open else "60px",
            "backgroundColor": "#05080E",
            "borderRight": "1px solid #1E293B",
            "padding": "16px 12px",
            "boxSizing": "border-box",
            "transition": "width 0.3s ease",
            "overflowY": "auto",
            "overflowX": "hidden"
        }},
        html.button(
            {
                "style": LOGO_BTN_STYLE,
                "onClick": toggle_open,
                "title": "Collapse Left Menu" if is_open else "Expand Left Menu"
            },
            html.img({
                "src": "/static/Barclays.png",
                "style": LOGO_IMG_STYLE,
                "alt": "Toggle Left Sidebar"
            })
        ),
        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "CORE LEDGER LOGIC"),
        *[
            html.button(
                {
                    "style": SIDEBAR_BTN_ACTIVE if active_item == item_id else SIDEBAR_BTN_STYLE,
                    "onClick": make_handler(item_id)
                },
                html.span({"style": {"fontWeight": "bold", "minWidth": "16px"}}, symbol),
                html.span({"style": {"display": "inline" if is_open else "none"}}, label)
            ) for item_id, symbol, label in items
        ],

        html.button(
            {
                "style": SIDEBAR_BTN_ACTIVE if active_item.startswith("cloud_") else SIDEBAR_BTN_STYLE,
                "onClick": toggle_cloud
            },
            html.span({"style": {"minWidth": "16px"}}, "☁️"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "Cloud Providers"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_cloud_open else "▼")
        ),

        html.div(
            {"style": {"display": "block" if (is_cloud_open and is_open) else "none"}},
            html.a(
                {
                    "href": "https://cloud.ibm.com/login",
                    "target": "_blank",
                    "rel": "noopener noreferrer",
                    "style": SUB_LINK_STYLE,
                    "onClick": lambda e: set_active_item("cloud_ibm"),
                    "title": "Open IBM Cloud Login Portal"
                },
                html.img({"src": "/static/IBM.jpg", "style": CLOUD_ICON_STYLE, "alt": "IBM"}),
                html.span("IBM Cloud Login ↗")
            ),
            html.a(
                {
                    "href": "https://cloud.oracle.com",
                    "target": "_blank",
                    "rel": "noopener noreferrer",
                    "style": SUB_LINK_STYLE,
                    "onClick": lambda e: set_active_item("cloud_oracle"),
                    "title": "Open Oracle Cloud Login Portal"
                },
                html.img({"src": "/static/Oracle.jpg", "style": CLOUD_ICON_STYLE, "alt": "Oracle"}),
                html.span("Oracle Cloud Login ↗")
            ),
            html.a(
                {
                    "href": "https://aws.amazon.com/console/",
                    "target": "_blank",
                    "rel": "noopener noreferrer",
                    "style": SUB_LINK_STYLE,
                    "onClick": lambda e: set_active_item("cloud_aws"),
                    "title": "Open AWS Console Login Portal"
                },
                html.img({"src": "/static/aws.jpg", "style": CLOUD_ICON_STYLE, "alt": "AWS"}),
                html.span("AWS Console Login ↗")
            )
        ),

        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "INFRASTRUCTURE"),

        html.button(
            {
                "style": SIDEBAR_BTN_STYLE,
                "onClick": toggle_health
            },
            html.span({"style": {"minWidth": "16px"}}, "🖥️"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "Microservices Health"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_health_open else "▼")
        ),

        html.div(
            {"style": {"display": "block" if (is_health_open and is_open) else "none"}},
            html.button(
                {"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("pycharm"), "title": "Launch PyCharm"},
                html.span("💻"), html.span("PyCharm")
            ),
            html.button(
                {"style": SUB_LINK_STYLE,
                 "onClick": lambda e: launch_ide("spyder", os.path.abspath("scripts/reconciliation_engine.py")),
                 "title": "Launch Spyder IDE"},
                html.span("🕷️"), html.span("Spyder")
            ),
            html.button(
                {"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("vscode"), "title": "Launch VS Code"},
                html.span("💙"), html.span("VS Code")
            )
        )
    )


# ------------------------------------------------------------------
# COMPONENT 3: Right Sidebar
# ------------------------------------------------------------------
@component
def RightSidebar(active_signal, set_active_signal, active_db, set_active_db, is_open, toggle_open):
    is_db_open, set_db_open = use_state(True)

    signals = [
        ("throughput_spike", "📊", "High Throughput Alerts"),
        ("anomaly_detect", "☠️", "Transaction Anomaly"),
        ("sequence_gap", "⌛", "Sequence Gap Detector"),
        ("cross_ledger", "🔄", "Cross-Ledger Sync"),
        ("latency_lag", "⚡", "Reconciliation Lag"),
        ("duplicate_tx", "🛑", "Duplicate Prevention")
    ]

    databases = [
        ("postgres", "🐘", "PostgreSQL Core"),
        ("mysql", "🐬", "MySQL Replica"),
        ("redis", "⚡", "Redis Cache Engine")
    ]

    def make_signal_handler(signal_id):
        return lambda e: set_active_signal(signal_id)

    def toggle_db(e):
        set_db_open(not is_db_open)

    return html.aside(
        {"style": {
            "width": "240px" if is_open else "60px",
            "backgroundColor": "#05080E",
            "borderLeft": "1px solid #1E293B",
            "padding": "16px 12px",
            "boxSizing": "border-box",
            "transition": "width 0.3s ease",
            "overflowY": "auto",
            "overflowX": "hidden"
        }},
        html.button(
            {
                "style": LOGO_BTN_STYLE,
                "onClick": toggle_open,
                "title": "Collapse Right Menu" if is_open else "Expand Right Menu"
            },
            html.img({
                "src": "/static/Barclays.png",
                "style": LOGO_IMG_STYLE,
                "alt": "Toggle Right Sidebar"
            })
        ),
        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "TRANSACTION SIGNALS"),
        *[
            html.button(
                {
                    "style": SIDEBAR_BTN_ACTIVE if active_signal == signal_id else SIDEBAR_BTN_STYLE,
                    "onClick": make_signal_handler(signal_id)
                },
                html.span({"style": {"minWidth": "16px"}}, icon),
                html.span({"style": {"display": "inline" if is_open else "none"}}, label)
            ) for signal_id, icon, label in signals
        ],

        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "DATABASE CONTROLS"),
        html.button(
            {
                "style": SIDEBAR_BTN_ACTIVE if active_db else SIDEBAR_BTN_STYLE,
                "onClick": toggle_db
            },
            html.span({"style": {"minWidth": "16px"}}, "🗄️"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "Database Connections"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_db_open else "▼")
        ),
        html.div(
            {"style": {"display": "block" if (is_db_open and is_open) else "none"}},
            *[
                html.button(
                    {
                        "style": SUB_LINK_ACTIVE if active_db == db_id else SUB_LINK_STYLE,
                        "onClick": lambda e, id=db_id: set_active_db(id)
                    },
                    html.span(icon),
                    html.span(label)
                ) for db_id, icon, label in databases
            ]
        )
    )


# ------------------------------------------------------------------
# COMPONENT 4: Center Main Content Dashboard
# ------------------------------------------------------------------
@component
def MainDashboard(active_left, active_right, active_db, set_active_db, throughput, latency, lag):
    db_name, set_db_name = use_state("")
    server_host, set_server_host = use_state("localhost")
    port_number, set_port_number = use_state(
        "5432" if active_db == "postgres" else "3306" if active_db == "mysql" else "6379")
    password, set_password = use_state("")
    connection_status, set_connection_status = use_state(None)

    def handle_connect(e):
        # 1. Check for Required / Empty Fields
        if not db_name.strip():
            set_connection_status({"success": False, "msg": "Validation Error: Database Name is required."})
            return
        if not server_host.strip():
            set_connection_status({"success": False, "msg": "Validation Error: Server Host is required."})
            return
        if not port_number.strip():
            set_connection_status({"success": False, "msg": "Validation Error: Port Number is required."})
            return
        if not password:
            set_connection_status({"success": False, "msg": "Validation Error: Password is required."})
            return

        # 2. Port Validation
        if not port_number.isdigit() or not (1 <= int(port_number) <= 65535):
            set_connection_status(
                {"success": False, "msg": "Validation Error: Port must be an integer between 1 and 65535."})
            return

        # 3. Server Host Syntax Validation
        host = server_host.strip().lower()
        ip_regex = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        domain_regex = r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z0-9-]{1,63})*$"

        if host != "localhost" and not re.match(ip_regex, host) and not re.match(domain_regex, host):
            set_connection_status({"success": False, "msg": "Validation Error: Invalid Host / IP address format."})
            return

        # 4. Password Minimum Length Check
        if len(password) < 8:
            set_connection_status(
                {"success": False, "msg": "Validation Error: Password must be at least 8 characters long."})
            return

        # Success Handshake Response
        set_connection_status({
            "success": True,
            "msg": f"Successfully initialized secure handshake to {active_db.upper()} ({db_name.strip()}) at {host}:{port_number.strip()}"
        })

    if active_db:
        db_titles = {
            "postgres": "PostgreSQL Core Bank Ledger Connection",
            "mysql": "MySQL Analytics Replica Connection",
            "redis": "Redis Real-Time Cache Connection"
        }

        default_ports = {"postgres": "5432", "mysql": "3306", "redis": "6379"}

        return html.main(
            {"style": {"padding": "24px", "backgroundColor": "#090D16", "overflowY": "auto", "flex": "1"}},
            html.div(
                {"style": {"marginBottom": "24px", "borderBottom": "1px solid #1E293B", "paddingBottom": "16px",
                           "display": "flex", "justifyContent": "space-between", "alignItems": "center"}},
                html.div(
                    html.h1({"style": {"margin": "0 0 6px 0", "fontSize": "22px", "color": "#F8FAFC"}},
                            db_titles.get(active_db, "Database Connection")),
                    html.p({"style": {"margin": 0, "color": "#64748B", "fontSize": "13px"}},
                           "Configure connection settings for bank transaction storage.")
                ),
                html.button(
                    {
                        "style": {"backgroundColor": "#1E293B", "border": "1px solid #334155", "color": "#94A3B8",
                                  "padding": "6px 12px", "borderRadius": "6px", "cursor": "pointer",
                                  "fontSize": "12px"},
                        "onClick": lambda e: set_active_db(None)
                    },
                    "✕ Close DB Panel"
                )
            ),
            html.div(
                {"style": {"maxWidth": "600px", "backgroundColor": "#05080E", "border": "1px solid #1E293B",
                           "borderRadius": "12px", "padding": "28px", "margin": "0 auto"}},
                html.div(
                    {"style": {"marginBottom": "20px"}},
                    html.label({"style": {"display": "block", "fontSize": "12px", "color": "#94A3B8",
                                          "marginBottom": "6px", "fontWeight": "bold"}}, "BANK DATABASE NAME"),
                    html.input({
                        "type": "text",
                        "placeholder": "e.g., Barclays_Main_Ledger_DB",
                        "style": INPUT_STYLE,
                        "value": db_name,
                        "onChange": lambda e: set_db_name(e["target"]["value"])
                    })
                ),
                html.div(
                    {"style": {"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "16px",
                               "marginBottom": "20px"}},
                    html.div(
                        html.label({"style": {"display": "block", "fontSize": "12px", "color": "#94A3B8",
                                              "marginBottom": "6px", "fontWeight": "bold"}}, "SERVER HOST / IP"),
                        html.input({
                            "type": "text",
                            "placeholder": "127.0.0.1 or db.internal.bank",
                            "style": INPUT_STYLE,
                            "value": server_host,
                            "onChange": lambda e: set_server_host(e["target"]["value"])
                        })
                    ),
                    html.div(
                        html.label({"style": {"display": "block", "fontSize": "12px", "color": "#94A3B8",
                                              "marginBottom": "6px", "fontWeight": "bold"}}, "PORT NUMBER"),
                        html.input({
                            "type": "text",
                            "placeholder": default_ports.get(active_db, "5432"),
                            "style": INPUT_STYLE,
                            "value": port_number,
                            "onChange": lambda e: set_port_number(e["target"]["value"])
                        })
                    )
                ),
                html.div(
                    {"style": {"marginBottom": "24px"}},
                    html.label({"style": {"display": "block", "fontSize": "12px", "color": "#94A3B8",
                                          "marginBottom": "6px", "fontWeight": "bold"}}, "PASSWORD"),
                    html.input({
                        "type": "password",
                        "placeholder": "••••••••••••••••",
                        "style": INPUT_STYLE,
                        "value": password,
                        "onChange": lambda e: set_password(e["target"]["value"])
                    })
                ),
                html.button(
                    {
                        "style": {
                            "width": "100%",
                            "backgroundColor": "#0284C7",
                            "color": "#FFFFFF",
                            "border": "none",
                            "borderRadius": "6px",
                            "padding": "12px",
                            "fontWeight": "bold",
                            "fontSize": "14px",
                            "cursor": "pointer"
                        },
                        "onClick": handle_connect
                    },
                    f"Connect to {active_db.upper()} Database"
                ),
                html.div(
                    {"style": {"display": "block" if connection_status else "none", "marginTop": "20px",
                               "padding": "12px", "borderRadius": "6px", "fontSize": "13px",
                               "backgroundColor": "#064E3B" if connection_status and connection_status[
                                   "success"] else "#7F1D1D",
                               "color": "#34D399" if connection_status and connection_status[
                                   "success"] else "#FCA5A5"}},
                    connection_status["msg"] if connection_status else ""
                )
            )
        )

    return html.main(
        {"style": {
            "padding": "24px",
            "backgroundColor": "#090D16",
            "overflowY": "auto",
            "flex": "1"
        }},
        html.div(
            {"style": {"marginBottom": "24px", "borderBottom": "1px solid #1E293B", "paddingBottom": "16px"}},
            html.h1({"style": {"margin": "0 0 6px 0", "fontSize": "22px", "color": "#F8FAFC"}},
                    f"Ledger Core: {active_left.replace('_', ' ').title()}"),
            html.p({"style": {"margin": 0, "color": "#64748B", "fontSize": "13px"}},
                   f"Active Signal Monitor: {active_right.replace('_', ' ').title()} | Engine: Ultra-Low Latency Kernel")
        ),
        html.div(
            {"style": {"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))", "gap": "16px",
                       "marginBottom": "24px"}},
            html.div(
                {"style": {"backgroundColor": "#05080E", "border": "1px solid #1E293B", "borderRadius": "8px",
                           "padding": "20px"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold",
                                    "textTransform": "uppercase"}}, "TRANSACTION THROUGHPUT"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "bold", "color": "#F8FAFC", "margin": "8px 0"}},
                         f"{throughput:,} tx/s"),
                html.div({"style": {"color": "#34D399", "fontSize": "12px"}}, "● Parallel Processing Enabled")
            ),
            html.div(
                {"style": {"backgroundColor": "#05080E", "border": "1px solid #1E293B", "borderRadius": "8px",
                           "padding": "20px"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold",
                                    "textTransform": "uppercase"}}, "INGESTION LATENCY"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "bold", "color": "#38BDF8", "margin": "8px 0"}},
                         f"{latency:.2f} ms"),
                html.div({"style": {"color": "#94A3B8", "fontSize": "12px"}}, "Zero-Copy In-Memory Engine")
            ),
            html.div(
                {"style": {"backgroundColor": "#05080E", "border": "1px solid #1E293B", "borderRadius": "8px",
                           "padding": "20px"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold",
                                    "textTransform": "uppercase"}}, "RECONCILIATION QUEUE"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "bold",
                                    "color": "#F8FAFC" if lag == 0 else "#F59E0B", "margin": "8px 0"}},
                         f"{lag:.2f}% Lag"),
                html.div({"style": {"color": "#94A3B8", "fontSize": "12px"}}, "Synchronous Ledger Lock")
            )
        )
    )


# ------------------------------------------------------------------
# ROOT COMPONENT
# ------------------------------------------------------------------
@component
def Ledger_Transection():
    active_left, set_active_left = use_state("double_entry")
    active_right, set_active_right = use_state("throughput_spike")
    active_db, set_active_db = use_state(None)

    is_left_open, set_left_open = use_state(True)
    is_right_open, set_right_open = use_state(True)

    settlement_vol, set_settlement_vol = use_state(142.80)
    throughput, set_throughput = use_state(12450)
    latency, set_latency = use_state(1.12)
    lag, set_lag = use_state(0.00)
    utc_time, set_utc_time = use_state(datetime.now(timezone.utc).strftime("%H:%M:%S"))

    @use_effect(dependencies=[])
    async def start_live_stream():
        vol = 142.80
        while True:
            await asyncio.sleep(1)
            set_utc_time(datetime.now(timezone.utc).strftime("%H:%M:%S"))
            vol += round(random.uniform(0.01, 0.08), 2)
            set_settlement_vol(vol)
            set_throughput(random.randint(11800, 13200))
            set_latency(round(random.uniform(0.85, 1.45), 2))
            set_lag(round(random.uniform(0.00, 0.05), 2))

    def toggle_left_sidebar(e):
        set_left_open(not is_left_open)

    def toggle_right_sidebar(e):
        set_right_open(not is_right_open)

    global_css = """
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        background-color: #05080E !important;
        color: #F8FAFC;
        font-family: system-ui, -apple-system, sans-serif;
        height: 100vh;
        overflow: hidden;
    }
    """

    return html.div(
        html.style(global_css),
        html.div(
            {"style": {"display": "flex", "flexDirection": "column", "height": "100vh", "width": "100vw"}},
            TopHeader(settlement_vol, utc_time),
            html.div(
                {"style": {"display": "flex", "flex": "1", "overflow": "hidden"}},
                LeftSidebar(active_left, set_active_left, is_left_open, toggle_left_sidebar),
                MainDashboard(active_left, active_right, active_db, set_active_db, throughput, latency, lag),
                RightSidebar(active_right, set_active_right, active_db, set_active_db, is_right_open,
                             toggle_right_sidebar)
            )
        )
    )


# Configure FastAPI application with ReactPy root component
configure(app, Ledger_Transection)