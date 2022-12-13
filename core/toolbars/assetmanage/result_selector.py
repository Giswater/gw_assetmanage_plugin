"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QTableView

from ....settings import tools_qt, tools_gw, dialog, tools_db
from .... import global_vars

from ...ui.ui_manager import ResultSelectorUi


class ResultSelector(dialog.GwAction):
    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

    def clicked_event(self):
        self.open_manager()

    def open_manager(self):

        self.dlg_result_selector = ResultSelectorUi()
        dlg = self.dlg_result_selector

        results = tools_db.get_rows(
            """
            select result_id id, result_name idval
            from asset.cat_result
            """
        )

        # Combo result_main
        tools_qt.fill_combo_values(dlg.cmb_result_main, results, 1, sort_by=1)
        selected_main = tools_db.get_row(
            """
            select result_id
            from asset.selector_result_main
            where cur_user = current_user
            """
        )
        if selected_main:
            tools_qt.set_combo_value(
                dlg.cmb_result_main, str(selected_main[0]), 0, add_new=False
            )

        # Combo result_compare
        tools_qt.fill_combo_values(dlg.cmb_result_compare, results, 1, sort_by=1)
        selected_compare = tools_db.get_row(
            """
            select result_id
            from asset.selector_result_compare
            where cur_user = current_user
            """
        )
        if selected_compare:
            tools_qt.set_combo_value(
                dlg.cmb_result_compare, str(selected_compare[0]), 0, add_new=False
            )

        # Open the dialog
        tools_gw.open_dialog(dlg, dlg_name="result_selection")
