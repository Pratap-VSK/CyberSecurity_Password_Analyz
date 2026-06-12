import customtkinter as ctk
from zxcvbn import zxcvbn
import hashlib
import requests
import threading
import logging
import secrets
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib3.exceptions import InsecureRequestWarning

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ==============================================================================
# SECTION 1: GLOBAL CONFIGURATION & THEME CONSTANTS
# Defines standard color palettes for dynamic state changes.
# ==============================================================================
COLOR_BG_DARK = "#0D0D11"       # Deep black-blue base
COLOR_BG_FRAME = "#16161E"      # Slightly lighter frame background
COLOR_NEON_GREEN = "#00E676"    # Strong / Secure State
COLOR_NEON_YELLOW = "#FFEA00"   # Moderate / Warning State
COLOR_NEON_RED = "#FF1744"      # Weak / Critical Alert State
COLOR_TEXT_DIM = "#94A3B8"      # Subtitle / Muted Text
COLOR_BORDER = "#2E2E3A"        # Default Subtle Border

ctk.set_appearance_mode("Dark")

# ==============================================================================
# SECTION 2: MAIN APPLICATION CLASS INITIALIZATION
# Bootstraps the application window and layout matrix.
# ==============================================================================
class ProfessionalSecurityScanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pinnacle Secure | Advanced Password Intelligence")
        self.geometry("700x720")
        self.configure(fg_color=COLOR_BG_DARK)

        self.api_timer = None
        self.api_thread = None
        self.password_visible = False
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers.update({'User-Agent': 'PinnacleSecureScanner/1.0'})

        # --- Sub-Section 2.1: Header Architecture ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(30, 20), padx=40)

        self.logo_label = ctk.CTkLabel(self.header_frame, text="🛡️", font=("Arial", 35), text_color=COLOR_NEON_GREEN)
        self.logo_label.pack(side="left", padx=(0, 15))

        self.title_label = ctk.CTkLabel(self.header_frame, text="Pinnacle Secure Scanner", font=("Arial", 28, "bold"), text_color="white")
        self.title_label.pack(side="left")

        self.subtitle_label = ctk.CTkLabel(self, text="Real-time Password Entropy & Breach Analysis", font=("Arial", 14), text_color=COLOR_TEXT_DIM)
        self.subtitle_label.pack(pady=(0, 20))

        # --- Sub-Section 2.2: Input Console Integration ---
        self.input_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_FRAME, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
        self.input_frame.pack(fill="x", padx=40, pady=10)

        self.console_title = ctk.CTkLabel(self.input_frame, text="ACTIVE CONSOLE", font=("Consolas", 12), text_color=COLOR_NEON_GREEN)
        self.console_title.pack(pady=(15, 0), padx=20, anchor="w")

        # Nested frame for Entry and Toggle Button alignment
        self.entry_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.entry_container.pack(pady=(5, 15), padx=20, fill="x")

        self.password_var = ctk.StringVar()
        self.password_var.trace_add("write", self.on_type)
        
        self.entry = ctk.CTkEntry(self.entry_container, textvariable=self.password_var, show="*", height=45, font=("Consolas", 18), 
                                   placeholder_text="Enter potential credential...", border_color=COLOR_NEON_GREEN, border_width=2, fg_color="#101014")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # TOGGLE EYE BUTTON
        self.toggle_btn = ctk.CTkButton(self.entry_container, text="👁️", width=45, height=45, fg_color="#101014", 
                                        border_color=COLOR_NEON_GREEN, border_width=2, hover_color=COLOR_BORDER, font=("Arial", 16), command=self.toggle_password)
        self.toggle_btn.pack(side="right")

        # --- Sub-Section 2.3: Central Dashboard & Dynamic Indicators ---
        self.dashboard_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard_frame.pack(fill="both", expand=True, padx=40, pady=10)

        # Primary Strength Panel
        self.strength_panel = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_BG_FRAME, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
        self.strength_panel.pack(fill="x", pady=5)

        self.strength_bar = ctk.CTkProgressBar(self.strength_panel, width=580, height=12)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=(20, 10), padx=20)

        self.status_label = ctk.CTkLabel(self.strength_panel, text="AWAITING CREDENTIAL", font=("Arial", 22, "bold"), text_color="white")
        self.status_label.pack(pady=(0, 10))

        # ** THE DYNAMIC CENTER FRAME **
        self.center_indicators_frame = ctk.CTkFrame(self.strength_panel, fg_color="transparent")
        self.center_indicators_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Initial Placeholder Space
        ctk.CTkLabel(self.center_indicators_frame, text="📡 INITIALIZING SCAN ARCHITECTURE", font=("Arial", 12), text_color=COLOR_TEXT_DIM).pack()

        # --- Sub-Section 2.4: Secondary Analytics Panels ---
        self.details_row = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.details_row.pack(fill="x", pady=10)

        # Left Panel (Metrics)
        self.metrics_panel = ctk.CTkFrame(self.details_row, fg_color=COLOR_BG_FRAME, corner_radius=15, border_width=1, border_color=COLOR_BORDER, width=290, height=180)
        self.metrics_panel.pack(side="left", padx=(0, 10))
        self.metrics_panel.pack_propagate(False)

        self.metrics_title = ctk.CTkLabel(self.metrics_panel, text="ENTROPY METRICS", font=("Arial", 14, "bold"), text_color=COLOR_TEXT_DIM)
        self.metrics_title.pack(pady=10)
        
        self.crack_time_label = ctk.CTkLabel(self.metrics_panel, text="Crack Time: --", font=("Consolas", 14), text_color="white")
        self.crack_time_label.pack(pady=5)
        
        self.warnings_icon = ctk.CTkLabel(self.metrics_panel, text="", font=("Arial", 26))
        self.warnings_icon.pack(pady=0)

        # Right Panel (Breach Intel)
        self.breach_panel = ctk.CTkFrame(self.details_row, fg_color=COLOR_BG_FRAME, corner_radius=15, border_width=1, border_color=COLOR_NEON_RED, width=290, height=180)
        self.breach_panel.pack(side="right", padx=(10, 0))
        self.breach_panel.pack_propagate(False)

        self.breach_title = ctk.CTkLabel(self.breach_panel, text="BREACH INTELLIGENCE", font=("Arial", 14, "bold"), text_color=COLOR_NEON_RED)
        self.breach_title.pack(pady=10)

        self.breach_status_icon = ctk.CTkLabel(self.breach_panel, text="📡", font=("Arial", 35))
        self.breach_status_icon.pack(pady=5)

        self.breach_text_label = ctk.CTkLabel(self.breach_panel, text="Scan status: Initializing...", font=("Arial", 12), text_color="white", wraplength=250)
        self.breach_text_label.pack(pady=5)

    # ==============================================================================
    # SECTION 3: UTILITY METHODS (UI Control)
    # Functions handling direct UI manipulation like toggles and clearing frames.
    # ==============================================================================
    
    def toggle_password(self):
        # Swaps the visibility state and icon
        if self.password_visible:
            self.entry.configure(show="*")
            self.toggle_btn.configure(text="👁️")
            self.password_visible = False
        else:
            self.entry.configure(show="")
            self.toggle_btn.configure(text="👁️‍🗨️") # Icon when text is visible
            self.password_visible = True

    def clear_indicators(self):
        for widget in self.center_indicators_frame.winfo_children():
            widget.destroy()

    def cleanup(self):
        if self.api_timer:
            self.after_cancel(self.api_timer)
        if self.api_thread and self.api_thread.is_alive():
            self.api_thread.join(timeout=2)
        self.session.close()
        logger.info("Application cleanup completed")

    def update_center_status_alerts(self, score):
        self.clear_indicators()
        
        if score <= 1:
            ctk.CTkLabel(self.center_indicators_frame, text="🚨 CRITICAL SECURITY ALARM", font=("Arial", 15, "bold"), text_color=COLOR_NEON_RED).pack(side="top")
            ctk.CTkLabel(self.center_indicators_frame, text="Direct breach vulnerability detected. High probability of compromise.", font=("Arial", 11), text_color="#D04040").pack(side="top")
        elif score == 2:
            ctk.CTkLabel(self.center_indicators_frame, text="🛡️ MEDIUM PROTECTION VULNERABLE", font=("Arial", 14, "bold"), text_color=COLOR_NEON_YELLOW).pack(side="top")
            ctk.CTkLabel(self.center_indicators_frame, text="Resists basic attacks but susceptible to advanced entropy modeling.", font=("Arial", 11), text_color="#D0A040").pack(side="top")
        else:
            ctk.CTkLabel(self.center_indicators_frame, text="✅ SECURE COMPLIANCE: 🔒 ROBUST", font=("Arial", 15, "bold"), text_color=COLOR_NEON_GREEN).pack(side="top")
            ctk.CTkLabel(self.center_indicators_frame, text="Cryptographic strength is optimal. Brute-force feasibility minimized.", font=("Arial", 11), text_color="#40C060").pack(side="top")

    # ==============================================================================
    # SECTION 4: CORE EVENT LOOP & LOCAL ENTROPY CALCULATION
    # Triggers on keystrokes, calculates local score, and manages color variables.
    # ==============================================================================
    def on_type(self, *args):
        pwd = self.password_var.get()
        if self.api_timer:
            self.after_cancel(self.api_timer)

        if not pwd:
            self.strength_bar.set(0)
            self.strength_bar.configure(progress_color="gray")
            self.status_label.configure(text="AWAITING CREDENTIAL", text_color="white")
            self.input_frame.configure(border_color=COLOR_NEON_GREEN)
            self.entry.configure(border_color=COLOR_NEON_GREEN)
            self.toggle_btn.configure(border_color=COLOR_NEON_GREEN)
            self.crack_time_label.configure(text="Crack Time: --")
            self.warnings_icon.configure(text="")
            self.breach_status_icon.configure(text="📡")
            self.breach_text_label.configure(text="Scan status: Initializing...")
            self.breach_panel.configure(border_color=COLOR_BORDER)

            self.clear_indicators()
            ctk.CTkLabel(self.center_indicators_frame, text="📡 INITIALIZING SCAN ARCHITECTURE", font=("Arial", 12), text_color=COLOR_TEXT_DIM).pack()
            return

        if len(pwd) > 128:
            self.breach_text_label.configure(text="⚠️ Password exceeds maximum length (128 chars)")
            return

        try:
            analysis = zxcvbn(pwd)
            score = analysis['score']
            crack_time = analysis['crack_times_display']['offline_fast_hashing_1e10_per_second']
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            self.breach_text_label.configure(text="⚠️ Analysis error occurred")
            return

        colors = [COLOR_NEON_RED, COLOR_NEON_RED, COLOR_NEON_YELLOW, COLOR_NEON_GREEN, COLOR_NEON_GREEN]
        labels = ["CRITICAL WEAK", "WEAK", "MODERATE RISK", "STRONG", "ENTERPRISE GRADE"]
        current_color = colors[score]

        self.strength_bar.set((score + 1) / 5.0)
        self.strength_bar.configure(progress_color=current_color)
        self.status_label.configure(text=labels[score], text_color=current_color)

        self.input_frame.configure(border_color=current_color)
        self.entry.configure(border_color=current_color)
        self.toggle_btn.configure(border_color=current_color)

        self.crack_time_label.configure(text=f"Crack Time:\n{crack_time}", text_color="white")

        if analysis['feedback']['warning']:
            self.warnings_icon.configure(text="⚠️", text_color=COLOR_NEON_YELLOW)
        else:
            self.warnings_icon.configure(text="")

        self.update_center_status_alerts(score)

        self.breach_text_label.configure(text="Checking breach database...⏳")
        self.api_timer = self.after(500, self.start_api_thread, pwd)

    # ==============================================================================
    # SECTION 5: EXTERNAL API MULTITHREADING (HIBP)
    # Secures transmission via SHA-1 and manages asynchronous network requests.
    # ==============================================================================
    
    def check_pwned_api(self, password):
        if not password or len(password) > 128:
            logger.warning("Invalid password length for API check")
            return None, 0

        try:
            sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            first5_char, tail = sha1_password[:5], sha1_password[5:]

            response = self.session.get(
                f'https://api.pwnedpasswords.com/range/{first5_char}',
                timeout=3,
                verify=True
            )
            response.raise_for_status()

            hashes = (line.split(':') for line in response.text.splitlines())
            for h, count in hashes:
                if h == tail:
                    logger.info("Password breach detected via HIBP API")
                    return True, count
            return False, 0
        except Timeout:
            logger.error("API timeout: HIBP service unreachable")
            return None, 0
        except ConnectionError:
            logger.error("Network connection error")
            return None, 0
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            return None, 0
        except Exception as e:
            logger.error(f"Unexpected error in API check: {e}")
            return None, 0 

    def start_api_thread(self, pwd):
        if self.api_thread and self.api_thread.is_alive():
            logger.debug("API thread already running, skipping")
            return

        self.api_thread = threading.Thread(
            target=self.run_api_and_update,
            args=(pwd,),
            daemon=False
        )
        self.api_thread.start()

    def run_api_and_update(self, pwd):
        is_breached, count = self.check_pwned_api(pwd)
        self.after(0, self.update_breach_ui, is_breached, count)

    def update_breach_ui(self, is_breached, count):
        if is_breached is True:
            self.breach_status_icon.configure(text="🚨", text_color=COLOR_NEON_RED)
            self.breach_text_label.configure(text=f"BREACH DETECTED: Found {count} times in public leaks!", text_color=COLOR_NEON_RED)
            self.breach_panel.configure(border_color=COLOR_NEON_RED)
        elif is_breached is False:
            self.breach_status_icon.configure(text="✅", text_color=COLOR_NEON_GREEN)
            self.breach_text_label.configure(text="Pinnacle Safe-Check verified. No public breaches found.", text_color="white")
            self.breach_panel.configure(border_color=COLOR_NEON_GREEN)
        else: 
            self.breach_text_label.configure(text="⚠️ Network Error: Unable to scan breach database.")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app = ProfessionalSecurityScanner()
    try:
        app.mainloop()
    finally:
        app.cleanup()
        logger.info("Application closed")
        logger.info("Application closed")