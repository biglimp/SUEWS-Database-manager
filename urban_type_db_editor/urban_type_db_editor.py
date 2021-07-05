# -*- coding: utf-8 -*-
"""
/***************************************************************************
 urban_type_db_editor
                                 A QGIS plugin
 This plugin allows for edits in the SUEWS database
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-21
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Oskar Bäcklin University of Gothenburg
        email                : oskar.backlin@gu.se
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from future import standard_library
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QFileDialog, QAction, QMessageBox
from qgis.gui import  QgsFieldComboBox, QgsMessageBar
from qgis.core import  QgsMapLayerProxyModel, Qgis, QgsProject, QgsFieldProxyModel, QgsField

# Initialize Qt resources from file resources.py
from .resources import *
import pandas as pd
import re
import time

# Import the code for the dialog
from .urban_type_db_editor_dialog import urban_type_db_editorDialog
import os.path


class urban_type_db_editor(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'urban_type_db_editor_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dlg = urban_type_db_editorDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Urban Type Database editor')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('urban_type_db_editor', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/urban_type_db_editor/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Urban Type Database editor'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = urban_type_db_editorDialog()
        
        for i in range(2,15):
            # Oc == Old Class
            Oc = eval('self.dlg.textBrowser_' + str(i))
            Oc.clear()
            vars()['self.dlg.textBrowser_' + str(i)] = Oc

            Nc = eval('self.dlg.textEdit_Edit_' + str(i))
            Nc.clear()
            vars()['self.dlg.textEdit_Edit_' + str(i)] = Nc
        
        self.dlg.comboBoxTableSelect.clear()
        self.dlg.comboBoxRef.clear()
        
        db_path = r'C:\Script\NGEO306\database_copy.xlsx'
        idx_col = 'ID'
        idx=-1

        Type = pd.read_excel(db_path, sheet_name= 'Lod1_Types', index_col=  idx_col)
        veg = pd.read_excel(db_path, sheet_name= 'Lod2_Veg', index_col = idx_col)
        veg.name = 'Lod2_Veg'
        nonveg = pd.read_excel(db_path, sheet_name= 'Lod2_NonVeg', index_col = idx_col)
        nonveg.name = 'Lod2_NonVeg'
        ref = pd.read_excel(db_path, sheet_name= 'References', index_col= idx_col)
        alb =  pd.read_excel(db_path, sheet_name= 'Lod3_Albedo', index_col= idx_col)
        alb.name = 'Lod3_Albedo'
        em =  pd.read_excel(db_path, sheet_name= 'Lod3_Emissivity', index_col= idx_col)
        em.name = 'Lod3_Emissivity'
        OHM =  pd.read_excel(db_path, sheet_name= 'Lod3_OHM', index_col= idx_col) # Away from Veg
        OHM.name = 'Lod3_OHM'
        LAI =  pd.read_excel(db_path, sheet_name= 'Lod3_LAI', index_col= idx_col)
        LAI.name = 'Lod3_OHM'
        st = pd.read_excel(db_path, sheet_name= 'Lod3_Storage', index_col = idx_col)
        st.name = 'Lod3_Storage'
        cnd = pd.read_excel(db_path, sheet_name= 'Lod3_Conductance', index_col = idx_col) # Away from Veg
        cnd.name = 'Lod3_Conductance'
        LGP = pd.read_excel(db_path, sheet_name= 'Lod3_LGP', index_col= idx_col)
        LGP.name = 'Lod3_LGP'
        dr = pd.read_excel(db_path, sheet_name= 'Lod3_Drainage', index_col= idx_col)
        dr.name = 'Lod3_Drainage'


        table_dict = {
            'Emissivity': 'Lod3_Emissivity',
            'OHM': 'Lod3_OHM',
            'Albedo': 'Lod3_Albedo',
            'Leaf Area Index': 'Lod3_LAI',
            'Water Storage': 'Lod3_Storage',
            'Conductance': 'Lod3_Conductance',
            'Leaf Growth Power': 'Lod3_LGP',
            'Drainage': 'Lod3_Drainage'
        }

        table_dict_ID = {
            'Emissivity': 'Em',
            'OHM': 'OHM',
            'Albedo': 'Alb',
            'Leaf Area Index': 'LAI',
            'Water Storage': 'St',
            'Conductance': 'Cnd',
            'Leaf Growth Power': 'LGP',
            'Drainage': 'Dr',
            'Vegetation' : 'Veg',
            'Building' : 'NonVeg',
            'Paved' : 'NonVeg',
            'Bare Soil': 'NonVeg',}

        table_dict_pd = {
            'Emissivity': em,
            'OHM': OHM,
            'Albedo': alb,
            'Leaf Area Index': LAI,
            'Water Storage': st,
            'Conductance': cnd,
            'Leaf Growth Power': LGP,
            'Drainage': dr,
            'Vegetation' : veg,
            'Building' : nonveg,
            'Paved' : nonveg,
            'Bare Soil': nonveg,
            }
        
        dict_gen_type = {
            'Paved' : 'NonVeg',
            'Building' : 'NonVeg',
            'Evergreen Tree' : 'Veg',
            'Decidous Tree' : 'Veg',
            'Grass' : 'Veg',
            'Bare Soil' : 'NonVeg',
            'Water' : 'Water'
  
        }


        rev_table_dict = dict((v, k) for k, v in table_dict.items())

        self.dlg.comboBoxTableSelect.addItems(list(rev_table_dict.values()))
        self.dlg.comboBoxTableSelect.setCurrentIndex(-1)
        
        ref_list = []
        for i in range(len(ref)):
            ref_list.append(str(ref['Author'].iloc[i]) + ' (' + str(ref['Publication Year'].iloc[i]) + ')')
        ref['authoryear'] = ref_list
        self.dlg.comboBoxRef.addItems(sorted(ref_list)) 
        self.dlg.comboBoxRef.setCurrentIndex(-1)

        self.dlg.pushButtonGen.clicked.connect(self.push_to_database)

        
        def table_changed():
            table_name = self.dlg.comboBoxTableSelect.currentText()
            
            # Clear ComboBoxes
            self.dlg.textBrowserNewID.clear()
            self.dlg.textBrowserDf.clear()
            for i in range(2,15):
                # Oc == Old Class
                Oc = eval('self.dlg.textBrowser_' + str(i))
                Oc.clear()
                Oc.setDisabled(True)
                vars()['self.dlg.textBrowser_' + str(i)] = Oc

                Nc = eval('self.dlg.textEdit_Edit_' + str(i))
                Nc.clear()
                Nc.setDisabled(True)
                vars()['self.dlg.textEdit_Edit_' + str(i)] = Nc

            try:
                table = table_dict_pd[str(table_name)]
                col_list = list(table)[2:-1]
                len_list = len(col_list)

                idx = 2
                for i in range(len_list):
                    if idx > 13:
                        break 
                    # Left side
                    Oc = eval('self.dlg.textBrowser_' + str(idx))
                    Oc.setEnabled(True)
                    Oc.setText(str(col_list[i]))
                    vars()['self.dlg.textBrowser_' + str(idx)] = Oc

                    Nc = eval('self.dlg.textEdit_Edit_' + str(idx))
                    Nc.setEnabled(True)
                    vars()['self.dlg.textEdit_Edit_' + str(idx)] = Nc
                    idx = idx+1

                self.dlg.textBrowserNewID.setText(table_dict_ID[str(self.dlg.comboBoxTableSelect.currentText())] + str(len(table) + 1))
                #self.dlg.textBrowserNewID.setText(str(" ".join(re.findall("[a-zA-Z]+", table.index[1])))+ str(len(table)+1))
                self.dlg.textBrowserDf.setText(str(table.drop(columns ='General Type').reset_index().to_html(index=False)))        
                self.dlg.comboBoxSurface.setCurrentIndex(-1)
            except:
                pass

        self.dlg.comboBoxTableSelect.currentIndexChanged.connect(table_changed) 
        
        def surface_changed():
            table_name = self.dlg.comboBoxTableSelect.currentText()
            surface = self.dlg.comboBoxSurface.currentText()
            table = table_dict_pd[str(table_name)]
            table_sel = table[table['Surface'] == surface]
            self.dlg.textBrowserDf.setText(str(table_sel.drop(columns ='General Type').reset_index().to_html(index=False))) 

        self.dlg.comboBoxSurface.currentIndexChanged.connect(surface_changed)

        def ref_changed():
            self.dlg.textBrowserRef.clear()

            try:
                ID = ref[ref['authoryear'] ==  self.dlg.comboBoxRef.currentText()].index.item()
                self.dlg.textBrowserRef.setText(
                    '<b>Author: ' +'</b>' + str(ref.loc[ID, 'Author']) + '<br><b>' +
                    'Year: ' + '</b> '+ str(ref.loc[ID, 'Publication Year']) + '<br><b>' +
                    'Title: ' + '</b> ' +  str(ref.loc[ID, 'Title']) + '<br><b>' +
                    'Journal: ' + '</b>' + str(ref.loc[ID, 'Journal']) + '<br><b>' +
                    'Ref ID: ' + '</b>' + str(ID)
                )
            except:
                pass
    
        self.dlg.comboBoxRef.currentIndexChanged.connect(ref_changed) 

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        else:
            self.dlg.__init__()

    def push_to_database(self):
        try:
            db_path = r'C:\Script\NGEO306\database_copy.xlsx'   
            idx_col = 'ID'
            
            Type = pd.read_excel(db_path, sheet_name= 'Lod1_Types', index_col=  idx_col)
            veg = pd.read_excel(db_path, sheet_name= 'Lod2_Veg', index_col = idx_col)
            nonveg = pd.read_excel(db_path, sheet_name= 'Lod2_NonVeg', index_col = idx_col)
            alb =  pd.read_excel(db_path, sheet_name= 'Lod3_Albedo', index_col= idx_col)
            alb.name = 'Lod3_Albedo'
            em =  pd.read_excel(db_path, sheet_name= 'Lod3_Emissivity', index_col= idx_col)
            em.name = 'Lod3_Emissivity'
            OHM =  pd.read_excel(db_path, sheet_name= 'Lod3_OHM', index_col= idx_col) # Away from Veg
            OHM.name = 'Lod3_OHM'
            LAI =  pd.read_excel(db_path, sheet_name= 'Lod3_LAI', index_col= idx_col)
            LAI.name = 'Lod3_OHM'
            st = pd.read_excel(db_path, sheet_name= 'Lod3_Storage', index_col = idx_col)
            st.name = 'Lod3_Storage'
            cnd = pd.read_excel(db_path, sheet_name= 'Lod3_Conductance', index_col = idx_col) # Away from Veg
            cnd.name = 'Lod3_Conductance'
            LGP = pd.read_excel(db_path, sheet_name= 'Lod3_LGP', index_col= idx_col)
            LGP.name = 'Lod3_LGP'
            dr = pd.read_excel(db_path, sheet_name= 'Lod3_Drainage', index_col= idx_col)
            dr.name = 'Lod3_Drainage'
            ref = pd.read_excel(db_path, sheet_name= 'References', index_col= idx_col)


            table_dict_pd = {
                'Emissivity': em,
                'OHM': OHM,
                'Albedo': alb,
                'Leaf Area Index': LAI,
                'Water Storage': st,
                'Conductance': cnd,
                'Leaf Growth Power': LGP,
                'Drainage': dr,
                'Vegetation' : veg,
                'Building' : nonveg,
                'Paved' : nonveg,
                'Bare Soil': nonveg,
            }
            table_dict_ID = {
                'Emissivity': 'Em',
                'OHM': 'OHM',
                'Albedo': 'Alb',
                'Leaf Area Index': 'LAI',
                'Water Storage': 'St',
                'Conductance': 'Cnd',
                'Leaf Growth Power': 'LGP',
                'Drainage': 'Dr',
                'Vegetation' : 'Veg',
                'Building' : 'NonVeg',
                'Paved' : 'NonVeg',
                'Bare Soil': 'NonVeg',
                }
                
            dict_gen_type = {
                'Paved' : 'NonVeg',
                'Building' : 'NonVeg',
                'Evergreen Tree' : 'Veg',
                'Decidous Tree' : 'Veg',
                'Grass' : 'Veg',
                'Bare Soil' : 'NonVeg',
                'Water' : 'Water'
    
            }

            table = table_dict_pd[str(self.dlg.comboBoxTableSelect.currentText())]
            fill_table = pd.read_excel(db_path, sheet_name= table.name, index_col= 'ID')

            col_list = list(table)
            len_list = len(col_list)

            idx = 1
            dict_reclass = {
                'ID' : str(table_dict_ID[str(self.dlg.comboBoxTableSelect.currentText())] + int(round(time.time()))),
                'General Type' : dict_gen_type[self.dlg.comboBoxSurface.currentText()],
                'Surface' : self.dlg.comboBoxSurface.currentText()
            }
        
            idx = 2

            for i in range(len_list-1):
                if idx > 13:
                    break 
                # Left side
                Oc = eval('self.dlg.textBrowser_' + str(idx))
                oldField = Oc.toPlainText()
                vars()['self.dlg.textBrowser_' + str(idx)] = Oc
                # Right Side
                Nc = eval('self.dlg.textEdit_Edit_' + str(idx))
                newField = Nc.value()
                vars()['self.dlg.textEdit_Edit_' + str(idx)] = Nc
                dict_reclass[oldField] =  [newField]

                idx += 1
            
            dict_reclass['Ref'] = ref[ref['authoryear'] ==  self.dlg.comboBoxRef.currentText()].index.item() 
            
            df_new_edit = pd.DataFrame(dict_reclass).set_index('ID')

            # IF Party to write to correct sheet in .xlsx
            
            var = self.dlg.comboBoxTableSelect.currentText()

            if var == 'Emissivity':
                em = em.append(df_new_edit)
                print(em)
            elif var == 'OHM':
                OHM = OHM.append(df_new_edit)
                print(OHM)
            elif var == 'Leaf Area Index':
                LAI = LAI.append(df_new_edit)
                print(LAI)
            elif var == 'Conductance':
                cnd = cnd.append(df_new_edit)
                print(cnd)
            elif var == 'Leaf Growth Power':
                LGP = LGP.append(df_new_edit)
                print(LGP)
            elif var == 'Drainage':
                dr = dr.append(df_new_edit)
                print(dr)
            else:
                print('Error!')

            with pd.ExcelWriter(db_path) as writer:  
                Type.to_excel(writer, sheet_name='Lod1_Types')
                ref.to_excel(writer, sheet_name='References')
                em.to_excel(writer, sheet_name='Lod3_Emissivity')
                OHM.to_excel(writer, sheet_name='Lod3_OHM')
                alb.to_excel(writer, sheet_name='Lod3_Albedo')
                LAI.to_excel(writer, sheet_name='Lod3_LAI')
                st.to_excel(writer, sheet_name='Lod3_Storage')
                cnd.to_excel(writer, sheet_name='Lod3_Conductance')
                veg.to_excel(writer, sheet_name='Lod2_Veg')
                nonveg.to_excel(writer, sheet_name='Lod2_NonVeg')
                LGP.to_excel(writer, sheet_name='Lod3_LGP')
                dr.to_excel(writer, sheet_name='Lod3_Drainage')

                QMessageBox.information(None, "Sucessful",'Edit Successfully pushed to Database')
            
            # reset plugin and update according to changes

            self.run()
        except:
            pass

        
   
