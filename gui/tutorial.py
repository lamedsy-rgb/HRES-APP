# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk

class TutorialDialog(ctk.CTkToplevel):
    """
    Step-by-step interactive floating tutorial dialog.
    Coordinates with the main application to switch tabs, focus, and highlight target elements.
    """
    def __init__(self, parent, steps):
        super().__init__(parent)
        self.parent = parent
        self.steps = steps
        self.current_step = 0
        self.highlighted_widget = None
        
        # Configure window
        self.title(self.parent.get_text("tut_title"))
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Add a subtle grab/focus
        self.focus()
        
        # Closing handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Build UI
        self.create_widgets()
        
        # Show first step
        self.show_step(0)
        
    def create_widgets(self):
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1) # Title & Text area
        self.grid_rowconfigure(1, weight=0) # Button panel
        self.grid_columnconfigure(0, weight=1)
        
        # Inner Frame
        self.content_frame = ctk.CTkFrame(self, corner_radius=12)
        self.content_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0) # Step indicator
        self.content_frame.grid_rowconfigure(1, weight=0) # Step Title
        self.content_frame.grid_rowconfigure(2, weight=1) # Step Desc
        
        # Step counter/indicator
        self.step_indicator_lbl = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#888888"
        )
        self.step_indicator_lbl.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Step Title
        self.step_title_lbl = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.step_title_lbl.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        # Step Description
        self.step_desc_lbl = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=360,
            anchor="nw"
        )
        self.step_desc_lbl.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Actions Panel (Prev, Skip/Exit, Next)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="ew")
        
        # Grid layout for buttons
        self.actions_frame.grid_columnconfigure(0, weight=1) # Prev
        self.actions_frame.grid_columnconfigure(1, weight=1) # Quit
        self.actions_frame.grid_columnconfigure(2, weight=1) # Next
        
        self.prev_btn = ctk.CTkButton(
            self.actions_frame,
            text=self.parent.get_text("tut_prev"),
            width=90,
            height=32,
            command=self.on_prev
        )
        self.prev_btn.grid(row=0, column=0, padx=5, sticky="w")
        
        self.quit_btn = ctk.CTkButton(
            self.actions_frame,
            text=self.parent.get_text("tut_exit"),
            width=90,
            height=32,
            fg_color="#7b1c1c",
            hover_color="#5a1414",
            command=self.on_close
        )
        self.quit_btn.grid(row=0, column=1, padx=5, sticky="")
        
        self.next_btn = ctk.CTkButton(
            self.actions_frame,
            text=self.parent.get_text("tut_next"),
            width=90,
            height=32,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.on_next
        )
        self.next_btn.grid(row=0, column=2, padx=5, sticky="e")
        
    def show_step(self, step_idx):
        if step_idx < 0 or step_idx >= len(self.steps):
            return
            
        # Clean up current highlight
        self.clear_highlight()
        
        self.current_step = step_idx
        step = self.steps[self.current_step]
        
        # 1. Switch Tab
        target_tab = step["tab"]
        self.parent.select_tab(target_tab)
        
        # 2. Trigger setup function if defined
        if "setup_func" in step and step["setup_func"]:
            try:
                step["setup_func"](self.parent)
            except Exception:
                pass
                
        # 3. Update Text
        total_steps = len(self.steps)
        self.step_indicator_lbl.configure(text=f"Étape {step_idx + 1} / {total_steps}" if self.parent.current_language == "fr" else f"Step {step_idx + 1} / {total_steps}" if self.parent.current_language == "en" else f"الخطوة {step_idx + 1} / {total_steps}")
        self.step_title_lbl.configure(text=self.parent.get_text(step["title_key"]))
        self.step_desc_lbl.configure(text=self.parent.get_text(step["desc_key"]))
        
        # Adjust buttons
        if step_idx == 0:
            self.prev_btn.configure(state="disabled")
        else:
            self.prev_btn.configure(state="normal")
            
        if step_idx == total_steps - 1:
            self.next_btn.configure(text=self.parent.get_text("tut_finish"), fg_color="#2ca02c", hover_color="#228022")
        else:
            self.next_btn.configure(text=self.parent.get_text("tut_next"), fg_color="#1f538d", hover_color="#14375e")
            
        # 4. Highlight target widget & Position Dialog (using a delay to let layout refresh after tab change)
        self.parent.update_idletasks()
        self.after(150, lambda: self._position_and_highlight(step))
        
    def _position_and_highlight(self, step):
        widget_attr = step["widget_attr"]
        target_widget = None
        if widget_attr and hasattr(self.parent, widget_attr):
            target_widget = getattr(self.parent, widget_attr)
            
        # Highlight
        if target_widget:
            self.highlight_widget(target_widget, active=True)
            self.highlighted_widget = target_widget
            
            # Position dialog relative to target widget
            try:
                target_widget.update_idletasks()
                
                wx = target_widget.winfo_rootx()
                wy = target_widget.winfo_rooty()
                ww = target_widget.winfo_width()
                wh = target_widget.winfo_height()
                
                if wx <= 0 or wy <= 0:
                    raise ValueError("Widget coordinates not mapped/visible")
                    
                dialog_w = 420
                dialog_h = 260
                self.geometry(f"{dialog_w}x{dialog_h}")
                
                screen_w = self.winfo_screenwidth()
                screen_h = self.winfo_screenheight()
                
                # Position dialog next to widget
                pos_x = wx + ww + 15
                pos_y = wy + (wh - dialog_h) // 2
                
                if pos_x + dialog_w > screen_w:
                    pos_x = wx - dialog_w - 15
                if pos_x < 0:
                    pos_x = wx + (ww - dialog_w) // 2
                    pos_y = wy + wh + 15
                    if pos_y + dialog_h > screen_h:
                        pos_y = wy - dialog_h - 15
                        
                pos_x = max(10, min(pos_x, screen_w - dialog_w - 10))
                pos_y = max(10, min(pos_y, screen_h - dialog_h - 10))
                
                self.geometry(f"{dialog_w}x{dialog_h}+{int(pos_x)}+{int(pos_y)}")
            except Exception:
                self._center_on_parent()
        else:
            self._center_on_parent()
            
    def _center_on_parent(self):
        dialog_w = 420
        dialog_h = 260
        self.geometry(f"{dialog_w}x{dialog_h}")
        
        try:
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            
            pos_x = px + (pw - dialog_w) // 2
            pos_y = py + (ph - dialog_h) // 2
            self.geometry(f"{dialog_w}x{dialog_h}+{int(pos_x)}+{int(pos_y)}")
        except Exception:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            pos_x = (screen_w - dialog_w) // 2
            pos_y = (screen_h - dialog_h) // 2
            self.geometry(f"{dialog_w}x{dialog_h}+{int(pos_x)}+{int(pos_y)}")
            
    def highlight_widget(self, widget, active=True):
        if not hasattr(widget, "_orig_border_width"):
            try:
                widget._orig_border_width = widget.cget("border_width")
                widget._orig_border_color = widget.cget("border_color")
            except Exception:
                widget._orig_border_width = 0
                widget._orig_border_color = None
                
        if active:
            try:
                widget.configure(border_width=3, border_color="#ff9800")
                if hasattr(widget, "slider"):
                    if not hasattr(widget.slider, "_orig_border_width"):
                        widget.slider._orig_border_width = widget.slider.cget("border_width")
                        widget.slider._orig_border_color = widget.slider.cget("border_color")
                    widget.slider.configure(border_width=3, border_color="#ff9800")
                if hasattr(widget, "entry"):
                    if not hasattr(widget.entry, "_orig_border_width"):
                        widget.entry._orig_border_width = widget.entry.cget("border_width")
                        widget.entry._orig_border_color = widget.entry.cget("border_color")
                    widget.entry.configure(border_width=3, border_color="#ff9800")
            except Exception:
                pass
        else:
            try:
                widget.configure(border_width=widget._orig_border_width, border_color=widget._orig_border_color)
                if hasattr(widget, "slider") and hasattr(widget.slider, "_orig_border_width"):
                    widget.slider.configure(border_width=widget.slider._orig_border_width, border_color=widget.slider._orig_border_color)
                if hasattr(widget, "entry") and hasattr(widget.entry, "_orig_border_width"):
                    widget.entry.configure(border_width=widget.entry._orig_border_width, border_color=widget.entry._orig_border_color)
            except Exception:
                pass
                
    def clear_highlight(self):
        if self.highlighted_widget:
            self.highlight_widget(self.highlighted_widget, active=False)
            self.highlighted_widget = None
            
    def on_prev(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
            
    def on_next(self):
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)
        else:
            self.on_finish()
            
    def on_finish(self):
        self.clear_highlight()
        if hasattr(self.parent, "on_tutorial_finished"):
            self.parent.on_tutorial_finished()
        self.destroy()
        
    def on_close(self):
        self.clear_highlight()
        if hasattr(self.parent, "on_tutorial_cancelled"):
            self.parent.on_tutorial_cancelled()
        self.destroy()
