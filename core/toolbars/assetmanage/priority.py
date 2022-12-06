"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial
import configparser
import os
import json

from qgis.PyQt.QtWidgets import QMenu, QAbstractItemView, QAction, QActionGroup, QTableView
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtSql import QSqlTableModel

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_global_vars
from .... import global_vars

from ...ui.ui_manager import PriorityUi, PriorityManagerUi


class AmPriority(dialog.GwAction):
    """ Button 2: Selection & priority calculation button
    Select features and calculate priorities """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

    def clicked_event(self):
        calculate_priority = CalculatePriority(type="SELECTION")
        calculate_priority.clicked_event()

class CalculatePriority:
    def __init__(self, type="GLOBAL"):
        self.type = type
        self.layer_to_work = 'v_asset_arc_output'
        self.layers = {}
        self.layers["arc"] = []
        self.list_ids = {}

        # Priority variables
        self.dlg_priority = None

    def clicked_event(self):

        self.dlg_priority = PriorityUi()
        dlg = self.dlg_priority
        dlg.setWindowTitle(dlg.windowTitle() + f" ({self.type})")

        tools_gw.disable_tab_log(self.dlg_priority)

        icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}20x20")
        icon_path = os.path.join(icons_folder, str(137) + ".png")
        if os.path.exists(icon_path):
            self.dlg_priority.btn_snapping.setIcon(QIcon(icon_path))

        # Manage form

        # Hidden widgets
        self._manage_hidden_form()

        # Manage selection group
        self._manage_selection()

        # Manage attributes group
        self._manage_attr()

        # Define tableviews
        self.qtbl_diameter = self.dlg_priority.findChild(QTableView, "tbl_diameter")
        self.qtbl_diameter.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_material = self.dlg_priority.findChild(QTableView, "tbl_material")
        self.qtbl_material.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_engine = self.dlg_priority.findChild(QTableView, "tbl_engine")
        self.qtbl_engine.setSelectionBehavior(QAbstractItemView.SelectRows)


        # Triggers
        self._fill_table(self.dlg_priority, self.qtbl_diameter, "asset.config_diameter",
                         set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority, self.qtbl_diameter, "config_diameter", schema_name='asset')
        self._fill_table(self.dlg_priority, self.qtbl_material, "asset.config_material",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority, self.qtbl_material, "config_material", schema_name='asset')
        self._fill_table(self.dlg_priority, self.qtbl_engine, "asset.config_engine",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority, self.qtbl_engine, "config_engine", schema_name='asset')

        self.dlg_priority.btn_calc.clicked.connect(self._manage_calculate)
        self.dlg_priority.btn_cancel.clicked.connect(partial(tools_gw.close_dialog, self.dlg_priority))
        self.dlg_priority.rejected.connect(partial(tools_gw.close_dialog, self.dlg_priority))


        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority, dlg_name='priority')


    def _manage_hidden_form(self):
        status = True
        try:
            if self.type == "GLOBAL":
                dialog_type = "dialog_priority_global"
            elif self.type == "SELECTION":
                dialog_type = "dialog_priority_selection"
            else:
                raise ValueError(f"Type of priority dialog shoud be 'GLOBAL' or 'SELECTION'. Value passed: '{self.type}'.")

            # Read the config file
            config = configparser.ConfigParser()
            config_path = os.path.join(global_vars.plugin_dir, f"config{os.sep}config.config")
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                return

            config.read(config_path)

            # Get configuration parameters
            if tools_os.set_boolean(config.get(dialog_type, "show_selection")) is not True:
                self.dlg_priority.grb_selection.setVisible(False)
            else:
                if tools_os.set_boolean(config.get(dialog_type, "show_maptool")) is not True:
                    self.dlg_priority.btn_snapping.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_diameter")) is not True:
                    self.dlg_priority.lbl_dnom.setVisible(False)
                    self.dlg_priority.cmb_dnom.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_material")) is not True:
                    self.dlg_priority.lbl_material.setVisible(False)
                    self.dlg_priority.cmb_material.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_exploitation")) is not True:
                    self.dlg_priority.lbl_expl_selection.setVisible(False)
                    self.dlg_priority.cmb_expl_selection.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_presszone")) is not True:
                    self.dlg_priority.lbl_presszone.setVisible(False)
                    self.dlg_priority.cmb_presszone.setVisible(False)
            if tools_os.set_boolean(config.get(dialog_type, "show_ivi_button")) is not True:
                #TODO: next approach
                pass
            if tools_os.set_boolean(config.get(dialog_type, "show_config")) is not True:
                self.dlg_priority.grb_global.setVisible(False)
            else:
                if tools_os.set_boolean(config.get(dialog_type, "show_config_diameter")) is not True:
                    self.dlg_priority.tab_widget.tab_diameter.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_config_arc")) is not True:
                    self.dlg_priority.tab_widget.tab_diameter.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_config_material")) is not True:
                    self.dlg_priority.tab_widget.tab_material.setVisible(False)
                if tools_os.set_boolean(config.get(dialog_type, "show_config_engine")) is not True:
                    self.dlg_priority.tab_widget.tab_engine.setVisible(False)

        except Exception as e:
            print('read_config_file error %s' % e)
            status = False

        return status

    def _manage_calculate(self):
        inputs = self._validate_inputs()
        if not inputs:
            return

        # # Manage selection
        # if self.list_ids == {}:
        #     message = "No features selected"
        #     tools_qgis.show_message(message, 0)
        #     return

        # function_name = 'gw_fct_assetmanage_selection'
        # self.child_value = None

        # # Manage extras
        # self.list_ids = json.dumps(self.list_ids)
        # self.dnom_value = tools_qt.get_combo_value(self.dlg_priority, 'cmb_dnom', 0)
        # self.material_value = tools_qt.get_combo_value(self.dlg_priority, 'cmb_material', 0)

        # extras = f'"selection":{self.list_ids}, "filters":{{"dnom":"{self.dnom_value}", "material":"{self.material_value}", "mapzone":"{self.mapzone_value}", "child":"{self.child_value}"}}'
        # body = tools_gw.create_body(extras=extras)
        # json_result = tools_gw.execute_procedure(function_name, body, schema_name='asset')
        # print(f"JSON_RESULT -> {json_result}")

    # region Selection

    def _manage_selection(self):
        """ Slot function for signal 'canvas.selectionChanged' """

        self._manage_btn_snapping()

    def _manage_btn_snapping(self):

        self.feature_type = "arc"
        layer = tools_qgis.get_layer_by_tablename('v_asset_arc_output')
        self.layers["arc"].append(layer)

        # Remove all previous selections
        self.layers = tools_gw.remove_selection(True, layers=self.layers)


        self.dlg_priority.btn_snapping.clicked.connect(
            partial(tools_gw.selection_init, self, self.dlg_priority, self.layer_to_work))


    def old_manage_btn_snapping(self):
        """ Fill btn_snapping QMenu """

        # Functions
        icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}svg")

        values = [
            [0, "Select Feature(s)", os.path.join(icons_folder, "mActionSelectRectangle.svg")],
            [1, "Select Features by Polygon", os.path.join(icons_folder, "mActionSelectPolygon.svg")],
            [2, "Select Features by Freehand", os.path.join(icons_folder, "mActionSelectRadius.svg")],
            [3, "Select Features by Radius", os.path.join(icons_folder, "mActionSelectRadius.svg")],
        ]

        # Create and populate QMenu
        select_menu = QMenu()
        for value in values:
            num = value[0]
            label = value[1]
            icon = QIcon(value[2])
            action = select_menu.addAction(icon, f"{label}")
            action.triggered.connect(partial(self._trigger_action_select, num))

        self.dlg_priority.btn_snapping.setMenu(select_menu)


    def _trigger_action_select(self, num):

        # Set active layer
        layer = tools_qgis.get_layer_by_tablename('v_asset_arc_output')
        self.iface.setActiveLayer(layer)

        if num == 0:
            self.iface.actionSelect().trigger()
        elif num == 1:
            self.iface.actionSelectPolygon().trigger()
        elif num == 2:
            self.iface.actionSelectFreehand().trigger()
        elif num == 3:
            self.iface.actionSelectRadius().trigger()


    def _selection_init(self):
        """ Set canvas map tool to an instance of class 'GwSelectManager' """

        # tools_gw.disconnect_signal('feature_delete')
        self.iface.actionSelect().trigger()
        # self.connect_signal_selection_changed()

    # endregion

    def _validate_inputs(self):
        dlg = self.dlg_priority

        result_name = dlg.txt_result_id.text()
        if not result_name:
            tools_qt.show_info_box("You should inform an Result Identifier!")
            return
        if tools_db.get_row(f"""
            select * from asset.cat_result
            where result_name = '{result_name}'
        """):
            tools_qt.show_info_box(f"'{result_name}' already exists. Please choose another Result Identifier.")
            return

    # region Attribute

    def _manage_attr(self):

        # Combo dnom
        sql = "SELECT distinct(dnom::float) as id, dnom as idval FROM cat_arc WHERE dnom is not null ORDER BY id;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_dnom, rows, 1, sort_by=0, add_empty=True)

        # Combo material
        sql = "SELECT id, id as idval FROM cat_mat_arc ORDER BY id;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_material, rows, 1, add_empty=True)

        # Combo exploitation
        sql = "SELECT expl_id as id, name as idval FROM ws.exploitation;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_expl_selection, rows, 1, add_empty=True)

        # Combo presszone
        sql = "SELECT presszone_id as id, name as idval FROM asset.presszone"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_presszone, rows, 1, add_empty=True)



    # endregion

    def _fill_table(self, dialog, widget, table_name, hidde=False, set_edit_triggers=QTableView.NoEditTriggers, expr=None):
        """ Set a model with selected filter.
            Attach that model to selected table
            @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """
        try:

            # Set model
            model = QSqlTableModel(db=gw_global_vars.qgis_db_credentials)
            model.setTable(table_name)
            model.setEditStrategy(QSqlTableModel.OnFieldChange)
            model.setSort(0, 0)
            model.select()

            # When change some field we need to refresh Qtableview and filter by psector_id
            # model.dataChanged.connect(partial(self._refresh_table, dialog, widget))
            widget.setEditTriggers(set_edit_triggers)

            # Check for errors
            if model.lastError().isValid():
                print(f"ERROR -> {model.lastError().text()}")

            # Attach model to table view
            if expr:
                widget.setModel(model)
                widget.model().setFilter(expr)
            else:
                widget.setModel(model)

            if hidde:
                self.refresh_table(dialog, widget)
        except Exception as e:
            print(f"EXCEPTION -> {e}")
