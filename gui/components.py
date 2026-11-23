import tkinter as tk
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class PlotCanvas(ctk.CTkFrame):
    """
    A helper widget that embeds a Matplotlib figure within a CustomTkinter frame.
    Supports dynamic dark/light mode color updates.
    """
    def __init__(self, master, dpi=100, toolbar=False, **kwargs):
        super().__init__(master, **kwargs)
        self.dpi = dpi
        self.show_toolbar = toolbar
        
        # Configure layout to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create figure and canvas
        self.fig = Figure(dpi=self.dpi, tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        self.toolbar = None
        if self.show_toolbar:
            self.grid_rowconfigure(1, weight=0)
            self.toolbar_frame = ctk.CTkFrame(self)
            self.toolbar_frame.grid(row=1, column=0, sticky="ew")
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
            self.toolbar.update()
            
        self.apply_theme()
        
    def apply_theme(self):
        """Adjusts the figure and axes colors to match CustomTkinter's current appearance mode."""
        appearance_mode = ctk.get_appearance_mode().lower()
        
        if appearance_mode == "dark":
            self.bg_color = "#2b2b2b"      # CustomTkinter frame dark background
            self.fg_color = "#ffffff"      # Text color
            self.grid_color = "#444444"    # Grid color
            self.ax_bg_color = "#1e1e1e"   # Subplot background
        else:
            self.bg_color = "#ebebeb"      # CustomTkinter frame light background
            self.fg_color = "#000000"      # Text color
            self.grid_color = "#cccccc"    # Grid color
            self.ax_bg_color = "#ffffff"   # Subplot background

        self.fig.set_facecolor(self.bg_color)
        
        # We check axes in the figure
        for i, ax in enumerate(self.fig.axes):
            # Only set background color for the primary axis (to keep twin axes transparent)
            if i == 0:
                ax.set_facecolor(self.ax_bg_color)
            else:
                ax.set_facecolor('none')
                
            # Check if this axis has a custom y-axis label color (like green for SOC)
            y_label_color = ax.yaxis.label.get_color()
            has_custom_y_color = y_label_color not in ["#000000", "#ffffff", "black", "white", self.fg_color]
            
            # Apply color to spines
            ax.spines['bottom'].set_color(self.fg_color)
            ax.spines['top'].set_color(self.fg_color)
            
            if has_custom_y_color:
                # For twin axis, color the right spine with the custom color, left spine is hidden/unused
                ax.spines['right'].set_color(y_label_color)
                ax.spines['left'].set_color('none')
                ax.tick_params(axis='y', colors=y_label_color, which='both')
                ax.tick_params(axis='x', colors=self.fg_color, which='both')
                ax.yaxis.label.set_color(y_label_color)
            else:
                ax.spines['left'].set_color(self.fg_color)
                ax.spines['right'].set_color(self.fg_color)
                ax.tick_params(colors=self.fg_color, which='both')
                ax.yaxis.label.set_color(self.fg_color)
                
            ax.xaxis.label.set_color(self.fg_color)
            ax.title.set_color(self.fg_color)
            
            if ax.legend_:
                legend = ax.legend_
                legend.get_frame().set_facecolor(self.ax_bg_color)
                legend.get_frame().set_edgecolor(self.grid_color)
                for text in legend.get_texts():
                    text.set_color(self.fg_color)
                    
            for child in ax.get_children():
                if isinstance(child, matplotlib.spines.Spine):
                    if has_custom_y_color and child.spine_type == 'right':
                        child.set_color(y_label_color)
                    elif child.spine_type in ['bottom', 'top', 'left', 'right']:
                        if not (has_custom_y_color and child.spine_type == 'left'):
                            child.set_color(self.fg_color)
                            
        self.canvas.draw_idle()

    def clear(self):
        """Clears the figure's subplots."""
        self.fig.clear()
        self.apply_theme()
        
    def draw(self):
        """Redraws the canvas."""
        self.apply_theme()


class LabeledSlider(ctk.CTkFrame):
    """
    A compound widget combining a label, a slider, and a value display.
    """
    def __init__(self, master, label_text, from_, to, default_value, resolution=1.0, value_suffix="", command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.resolution = resolution
        self.value_suffix = value_suffix
        self.command = command
        
        # Check active language in master hierarchy for Arabic RTL alignment
        app = self.winfo_toplevel()
        is_rtl = hasattr(app, "current_language") and app.current_language == "ar"
        
        # Two-row layout: Label + Value on row 0 (no horizontal clipping), full-width Slider on row 1
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        anchor = "e" if is_rtl else "w"
        self.label = ctk.CTkLabel(self, text=label_text, anchor=anchor)
        self.slider = ctk.CTkSlider(self, from_=from_, to=to, number_of_steps=max(1, int((to - from_) / resolution)))
        self.slider.set(default_value)
        self.slider.configure(command=self._on_slider_move)
        
        val_anchor = "w" if is_rtl else "e"
        self.value_label = ctk.CTkLabel(
            self,
            text=f"{default_value}{value_suffix}",
            width=64,
            anchor=val_anchor,
            font=ctk.CTkFont(weight="bold")
        )
        
        # Grid layout based on LTR/RTL
        if is_rtl:
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
            self.value_label.grid(row=0, column=0, padx=(5, 8), pady=(0, 4), sticky="w")
            self.label.grid(row=0, column=1, padx=(8, 5), pady=(0, 4), sticky="ew")
        else:
            self.label.grid(row=0, column=0, padx=(5, 8), pady=(0, 4), sticky="ew")
            self.value_label.grid(row=0, column=1, padx=(8, 5), pady=(0, 4), sticky="e")
        self.slider.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 2), sticky="ew")
        
    def _on_slider_move(self, val):
        rounded_val = round(float(val) / self.resolution) * self.resolution
        if self.resolution >= 1.0:
            formatted_val = int(rounded_val)
        else:
            formatted_val = round(rounded_val, len(str(self.resolution).split(".")[1]))
        
        self.slider.set(formatted_val)
        self.value_label.configure(text=f"{formatted_val}{self.value_suffix}")
        
        if self.command:
            self.command(formatted_val)
        
    def get(self):
        return self.slider.get()
        
    def set(self, val):
        self.slider.set(val)
        self._on_slider_move(val)


class LabeledEntry(ctk.CTkFrame):
    """
    A compound widget combining a label and a numeric entry box.
    """
    def __init__(self, master, label_text, default_value, placeholder_text="", width=120, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        app = self.winfo_toplevel()
        is_rtl = hasattr(app, "current_language") and app.current_language == "ar"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        anchor = "e" if is_rtl else "w"
        self.label = ctk.CTkLabel(self, text=label_text, anchor=anchor)
        self.entry = ctk.CTkEntry(self, width=width, placeholder_text=placeholder_text)
        self.entry.insert(0, str(default_value))
        
        if is_rtl:
            self.entry.grid(row=0, column=0, padx=5, sticky="w")
            self.label.grid(row=0, column=1, padx=(10, 5), sticky="ew")
        else:
            self.label.grid(row=0, column=0, padx=(5, 10), sticky="ew")
            self.entry.grid(row=0, column=1, padx=5, sticky="e")
        
    def get(self):
        return self.entry.get()
        
    def get_float(self, default=0.0):
        try:
            return float(self.entry.get())
        except ValueError:
            return default

    def get_int(self, default=0):
        try:
            return int(float(self.entry.get()))
        except ValueError:
            return default
            
    def set(self, val):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(val))
