"""
Popup de gerenciamento de Termos Personalizados.
v3.2: tema central + fontes maiores.
"""
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

import customtkinter as ctk

from custom_terms import CustomTermsManager
from custom_titlebar import apply_custom_titlebar
from theme import get_theme
from assets_helper import set_window_icon, apply_icon_via_win32
from i18n import t

log = logging.getLogger(__name__)

LANGUAGES = {
    "fr": "Français",
    "pt": "Português",
    "en": "English",
    "es": "Español",
}


class CustomTermsPopup:
    def __init__(self, master, custom_terms: CustomTermsManager, settings):
        self.master = master
        self.custom_terms = custom_terms
        self.settings = settings
        self.window: Optional[ctk.CTkToplevel] = None
        self.tree: Optional[ttk.Treeview] = None
        self._edit_widget: Optional[tk.Widget] = None
        self._editing_row: Optional[str] = None
        self._editing_col: Optional[str] = None

    def show(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self._refresh_list()
            return
        self._build()

    def _build(self):
        theme = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))

        self.window = ctk.CTkToplevel(self.master)
        self.window.title(t("title.terms"))
        # Centraliza relativa à main window (em cima dela)
        from monitor_utils import center_window_on_parent
        center_window_on_parent(self.window, self.master, 740, 620)
        self.window.configure(fg_color=theme['bg'])

        self.titlebar_refs = apply_custom_titlebar(
            self.window,
            title=t("terms.title"),
            on_close=self._close,
            keep_taskbar=True,
            show_minimize=False,
            resizable=True,
            bg_color=theme['bg'],
            bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'], accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=600, min_height=400,
        )

        # Re-aplica ícone via Win32 DEPOIS do overrideredirect e do
        # withdraw+deiconify do _force_taskbar_appearance que reseta o ícone.
        self.window.after(300, lambda: apply_icon_via_win32(self.window))
        self.window.after(800, lambda: apply_icon_via_win32(self.window))

        # Style do Treeview pra combinar com tema
        style = ttk.Style(self.window)
        style.theme_use('default')
        style.configure(
            'Custom.Treeview',
            background=theme['bg_input'], foreground=theme['text'],
            fieldbackground=theme['bg_input'],
            borderwidth=0, rowheight=34,
            font=('Segoe UI', 12),
        )
        style.configure(
            'Custom.Treeview.Heading',
            background=theme['bg_pill'], foreground=theme['accent'], relief='flat',
            font=('Segoe UI', 12, 'bold'),
        )
        style.map('Custom.Treeview',
                  background=[('selected', theme['accent'])],
                  foreground=[('selected', theme['text_on_accent'])])

        # ===== Form de adicionar =====
        form_frame = ctk.CTkFrame(self.window, fg_color=theme['bg_panel'], corner_radius=8)
        form_frame.pack(fill='x', padx=15, pady=(10, 8))

        ctk.CTkLabel(
            form_frame, text=t("terms.section.add"),
            text_color=theme['accent'], font=('Segoe UI', 14, 'bold'),
        ).pack(anchor='w', padx=14, pady=(10, 6))

        # Linha 1: origem
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill='x', padx=14, pady=4)

        ctk.CTkLabel(row1, text=t("terms.label.source_lang"), text_color=theme['text'],
                     width=130, anchor='w', font=('Segoe UI', 12)).pack(side='left')
        self.src_lang_var = tk.StringVar(value='fr')
        ctk.CTkComboBox(
            row1, variable=self.src_lang_var, values=list(LANGUAGES.keys()),
            width=100, state='readonly',
            fg_color=theme['bg_input'], button_color=theme['accent'], button_hover_color=theme['accent_hover'],
            text_color=theme['text'], dropdown_fg_color=theme['bg_input'], dropdown_text_color=theme['text'],
            dropdown_hover_color=theme['bg_hover'],
            border_color=theme['border'], font=('Segoe UI', 12), height=36,
        ).pack(side='left', padx=(0, 12))

        ctk.CTkLabel(row1, text=t("terms.label.term"), text_color=theme['text'],
                     font=('Segoe UI', 12)).pack(side='left', padx=(0, 5))
        self.src_term_entry = ctk.CTkEntry(
            row1, fg_color=theme['bg_input'], text_color=theme['text'],
            border_color=theme['border'], placeholder_text="ex: pano",
            font=('Segoe UI', 12), height=36,
        )
        self.src_term_entry.pack(side='left', fill='x', expand=True)

        # Linha 2: destino
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill='x', padx=14, pady=4)

        ctk.CTkLabel(row2, text=t("terms.label.target_lang"), text_color=theme['text'],
                     width=130, anchor='w', font=('Segoe UI', 12)).pack(side='left')
        self.dst_lang_var = tk.StringVar(value='pt')
        ctk.CTkComboBox(
            row2, variable=self.dst_lang_var, values=list(LANGUAGES.keys()),
            width=100, state='readonly',
            fg_color=theme['bg_input'], button_color=theme['accent'], button_hover_color=theme['accent_hover'],
            text_color=theme['text'], dropdown_fg_color=theme['bg_input'], dropdown_text_color=theme['text'],
            dropdown_hover_color=theme['bg_hover'],
            border_color=theme['border'], font=('Segoe UI', 12), height=36,
        ).pack(side='left', padx=(0, 12))

        ctk.CTkLabel(row2, text=t("terms.label.term"), text_color=theme['text'],
                     font=('Segoe UI', 12)).pack(side='left', padx=(0, 5))
        self.dst_term_entry = ctk.CTkEntry(
            row2, fg_color=theme['bg_input'], text_color=theme['text'],
            border_color=theme['border'], placeholder_text="ex: conjunto",
            font=('Segoe UI', 12), height=36,
        )
        self.dst_term_entry.pack(side='left', fill='x', expand=True)

        # Linha 3: reverso + botão
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill='x', padx=14, pady=(8, 14))

        self.add_reverse_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            row3, text=t("terms.add_reverse"),
            variable=self.add_reverse_var,
            text_color=theme['text'], font=('Segoe UI', 12),
            fg_color=theme['accent'], hover_color=theme['bg_hover'],
            checkbox_height=22, checkbox_width=22, corner_radius=4,
        ).pack(side='left')

        ctk.CTkButton(
            row3, text=t("terms.btn.add"),
            command=self._on_add,
            fg_color=theme['accent'], hover_color=theme['accent_hover'],
            text_color=theme['text_on_accent'], font=('Segoe UI', 13, 'bold'),
            corner_radius=6, width=140, height=38,
        ).pack(side='right')

        # ===== Lista =====
        list_frame = ctk.CTkFrame(self.window, fg_color=theme['bg_panel'], corner_radius=8)
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 8))

        ctk.CTkLabel(
            list_frame, text=t("terms.section.list"),
            text_color=theme['accent'], font=('Segoe UI', 14, 'bold'),
        ).pack(anchor='w', padx=14, pady=(10, 6))

        tree_container = tk.Frame(list_frame, bg=theme['bg_panel'])
        tree_container.pack(fill='both', expand=True, padx=14, pady=(0, 14))

        columns = ('src_lang', 'src_term', 'dst_lang', 'dst_term')
        self.tree = ttk.Treeview(
            tree_container, columns=columns, show='headings',
            style='Custom.Treeview', selectmode='browse',
        )
        self.tree.heading('src_lang', text='De')
        self.tree.heading('src_term', text='Termo')
        self.tree.heading('dst_lang', text='Para')
        self.tree.heading('dst_term', text='Equivale a')
        self.tree.column('src_lang', width=70, anchor='center')
        self.tree.column('src_term', width=220, anchor='w')
        self.tree.column('dst_lang', width=70, anchor='center')
        self.tree.column('dst_term', width=220, anchor='w')

        scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self._on_tree_double_click)
        self.tree.bind('<Delete>', lambda e: self._on_remove_selected())

        # ===== Botões inferiores =====
        btn_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        btn_frame.pack(fill='x', padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_frame, text=t("terms.btn.remove"),
            command=self._on_remove_selected,
            fg_color=theme['danger_bg'], hover_color=theme['danger_hover'],
            text_color=theme['text'], font=('Segoe UI', 12, 'bold'),
            corner_radius=6, height=38,
        ).pack(side='left')

        ctk.CTkButton(
            btn_frame, text=t("terms.btn.reload"),
            command=self._on_reload,
            fg_color=theme['bg_pill'], hover_color=theme['bg_hover'],
            text_color=theme['text'], font=('Segoe UI', 12),
            corner_radius=6, height=38,
        ).pack(side='left', padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text=t("btn.close"),
            command=self._close,
            fg_color=theme['accent'], hover_color=theme['accent_hover'],
            text_color=theme['text_on_accent'], font=('Segoe UI', 12, 'bold'),
            corner_radius=6, height=38, width=120,
        ).pack(side='right')

        # Status
        self.status_label = ctk.CTkLabel(
            self.window, text="", text_color=theme['accent'],
            anchor='w', font=('Segoe UI', 12),
        )
        self.status_label.pack(fill='x', padx=15, pady=(0, 10))

        self.window.protocol("WM_DELETE_WINDOW", self._close)
        self._refresh_list()
        self.src_term_entry.focus_set()

    def _refresh_list(self):
        if not self.tree:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, term in enumerate(self.custom_terms.all()):
            self.tree.insert(
                '', tk.END, iid=str(i),
                values=(
                    term['src_lang'].upper(),
                    term['src_term'],
                    term['dst_lang'].upper(),
                    term['dst_term'],
                )
            )

    def _on_add(self):
        src_lang = self.src_lang_var.get().strip()
        dst_lang = self.dst_lang_var.get().strip()
        src_term = self.src_term_entry.get().strip()
        dst_term = self.dst_term_entry.get().strip()
        add_reverse = self.add_reverse_var.get()

        ok, msg = self.custom_terms.add(
            src_lang, src_term, dst_lang, dst_term, add_reverse=add_reverse
        )
        if ok:
            self._refresh_list()
            self.src_term_entry.delete(0, tk.END)
            self.dst_term_entry.delete(0, tk.END)
            self.src_term_entry.focus_set()
            self._set_status(msg, error=False)
        else:
            self._set_status(msg, error=True)
            messagebox.showwarning("Não foi possível adicionar", msg, parent=self.window)

    def _on_remove_selected(self):
        if not self.tree:
            return
        selected = self.tree.selection()
        if not selected:
            self._set_status("Nenhum termo selecionado.", error=True)
            return
        try:
            index = int(selected[0])
        except ValueError:
            return
        terms = self.custom_terms.all()
        if not (0 <= index < len(terms)):
            return
        term = terms[index]

        confirm = messagebox.askyesno(
            "Remover termo",
            f"Remover este termo?\n\n"
            f"{term['src_lang'].upper()} '{term['src_term']}' "
            f"→ {term['dst_lang'].upper()} '{term['dst_term']}'",
            parent=self.window,
        )
        if not confirm:
            return

        if self.custom_terms.remove(index):
            self._refresh_list()
            self._set_status("Termo removido.", error=False)

    def _on_reload(self):
        self.custom_terms.reload()
        self._refresh_list()
        self._set_status(f"Recarregado: {len(self.custom_terms.all())} termos.", error=False)

    def _on_tree_double_click(self, event):
        if not self.tree:
            return
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not row_id or not col_id:
            return

        x, y, w, h = self.tree.bbox(row_id, col_id)
        col_index = int(col_id.replace('#', '')) - 1
        col_names = ['src_lang', 'src_term', 'dst_lang', 'dst_term']
        if not (0 <= col_index < len(col_names)):
            return
        col_name = col_names[col_index]

        current_values = self.tree.item(row_id, 'values')
        current_value = current_values[col_index]

        self._destroy_edit_widget()

        if col_name in ('src_lang', 'dst_lang'):
            var = tk.StringVar(value=current_value.lower())
            widget = ttk.Combobox(
                self.tree, textvariable=var,
                values=list(LANGUAGES.keys()), state='readonly',
            )
        else:
            widget = tk.Entry(self.tree, bg='#fff', fg='#000', relief='solid', bd=1)
            widget.insert(0, current_value)

        widget.place(x=x, y=y, width=w, height=h)
        widget.focus_set()
        if isinstance(widget, tk.Entry):
            widget.select_range(0, tk.END)

        self._edit_widget = widget
        self._editing_row = row_id
        self._editing_col = col_name

        widget.bind('<Return>', lambda e: self._commit_edit())
        widget.bind('<Escape>', lambda e: self._destroy_edit_widget())
        widget.bind('<FocusOut>', lambda e: self._commit_edit())
        if isinstance(widget, ttk.Combobox):
            widget.bind('<<ComboboxSelected>>', lambda e: self._commit_edit())

    def _commit_edit(self):
        if self._edit_widget is None or self._editing_row is None or self._editing_col is None:
            return

        if isinstance(self._edit_widget, ttk.Combobox):
            new_value = self._edit_widget.get().strip().lower()
        elif isinstance(self._edit_widget, tk.Entry):
            new_value = self._edit_widget.get().strip()
        else:
            self._destroy_edit_widget()
            return

        try:
            index = int(self._editing_row)
        except ValueError:
            self._destroy_edit_widget()
            return

        terms = self.custom_terms.all()
        if not (0 <= index < len(terms)):
            self._destroy_edit_widget()
            return

        current = terms[index].copy()
        current[self._editing_col] = new_value

        ok, msg = self.custom_terms.update(
            index,
            src_lang=current['src_lang'],
            src_term=current['src_term'],
            dst_lang=current['dst_lang'],
            dst_term=current['dst_term'],
        )

        self._destroy_edit_widget()
        self._refresh_list()
        self._set_status(msg, error=not ok)

    def _destroy_edit_widget(self):
        if self._edit_widget is not None:
            try:
                self._edit_widget.destroy()
            except Exception:
                pass
        self._edit_widget = None
        self._editing_row = None
        self._editing_col = None

    def _set_status(self, msg: str, error: bool = False):
        if hasattr(self, 'status_label') and self.status_label:
            theme = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))
            color = theme['highlight'] if error else theme['accent']
            self.status_label.configure(text=msg, text_color=color)
        log.info(msg)

    def _close(self):
        self._destroy_edit_widget()
        if self.window:
            self.window.withdraw()
