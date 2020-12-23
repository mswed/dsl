"""Welcome to the dynamic script loader!"""

import os
import sys
import json
import subprocess
from itertools import islice
from functools import partial
from pprint import pprint

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

from shiboken2 import wrapInstance

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymel.core as pm
import maya.OpenMayaUI as mui


class Script(object):
    """
    A python or mel script object
    """

    def __init__(self, file_path):
        self.valid = False
        self.file_path = file_path
        self.header = self.read_header()
        self.script_name, self.script_extension = os.path.splitext(os.path.basename(file_path))
        self.button_color = 'yellow'
        self.button_name = 'new button'
        self.button_description = 'no description'
        self.button_help = 'no help :('
        self.button_tabs = None
        self.valid = False

        self.split_header()

    @property
    def is_valid(self):
        return self.valid

    def read_header(self):
        """
        reads the first 20 lines of a script and returns them
        :return: str, the first 20 lines of the file
        """

        if os.path.isfile(self.file_path):
            # we only care about python and mel files
            if self.file_path.endswith('.py') or self.file_path.endswith('.mel'):
                with open(self.file_path) as target_script:
                    header = list(islice(target_script, 20))
                    self.valid = True
                    return header

    def split_header(self):
        """
        Analyze the header test, and if a DSL header is found collect the script info into the class
        """
        if self.script_extension == '.py' or self.script_extension == '.mel':
            try:
                self.button_color = self.find_in_header('dsl_color:')[0]
                self.button_name = self.find_in_header('dsl_button:')[0]
                self.button_description = '\n'.join(self.find_in_header('dsl_description:'))
                self.button_help = '\n'.join(self.find_in_header('dsl_help:'))

                # a button can appear in multiple tabs and preform multiple actions
                self.button_tabs = {}
                tabs = self.find_in_header('dsl_tab:')
                for tab in tabs:
                    tab_info = tab.split(':')
                    button_tab = tab_info[0]
                    button_line = tab_info[1]
                    button_command = tab_info[2]
                    self.button_tabs[button_tab] = {'button_line': button_line, 'button_command': button_command}

                # mark the script as valid
                self.valid = True
            except IndexError, e:
                # print e
                pass

    def find_in_header(self, text):
        """
        locates the line containing a text, removes the text from the line, and returns the new line
        :param text: str, text to find
        :return: the line containing the found text, with the found text removed
        """
        found_text = [s for s in self.header if text in s]
        clean_text = [s[len(text) + 2:].strip() for s in found_text]

        return clean_text


def maya_main_window():
    """
    creates a pointer to maya's main window
    :return: instance, containing maya's main window as a Qt widget
    """
    pointer = mui.MQtUtil.mainWindow()
    return wrapInstance(long(pointer), QtWidgets.QWidget)


class DSLButton(QtWidgets.QPushButton):

    def __init__(self, label, color, command, script, help, script_path):
        super(DSLButton, self).__init__(label)

        # add help variable
        self.help = help
        self.script_path = script_path
        self.label = label
        # create font
        button_font = QtGui.QFont()
        button_font.setBold(True)

        # set button appearance
        self.setFont(button_font)

        main, dark, light = self.set_colors(color)
        self.setStyleSheet('''QPushButton {         color: black;
                                                    background-image: None;
                                                    border-image: None;
                                                    background-color: %s; 
                                                    border-radius: 5px;
                                                    border: 1px solid %s;
                                            }
                                            QPushButton:hover{
                                                    background-color: %s;
                                            }
                                            QPushButton:pressed{
                                                    background-color: %s;
                                            }
                                        ''' % (main, main, light, dark))
        # self.setStyleSheet("background-color: %s; color: black;" % self.set_colors(color))
        self.setMinimumSize(200, 30)
        self.setMinimumSize(200, 30)

        # button command
        self.clicked.connect(partial(self.button_callback, script, command))

        # add context menu
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        help_option = QtWidgets.QAction(self)
        help_option.setText('Help')
        help_option.triggered.connect(self.show_help)
        self.addAction(help_option)

        separator = QtWidgets.QAction(self)
        separator.setSeparator(True)
        self.addAction(separator)

        edit_file = QtWidgets.QAction(self)
        edit_file.setText('Edit Script')
        edit_file.triggered.connect(self.edit_script)
        self.addAction(edit_file)

    def button_callback(self, script_name, command):

        if self.script_path.endswith('.py'):

            if command == 'main()':
                command_string = 'import %s\nreload(%s)' % (script_name, script_name)
                exec (command_string)
                print(self.script_path)

            else:
                command_string = 'import %s\nreload(%s)\n%s.%s' % (
                    script_name, script_name, script_name, command)
                print(command_string)
                exec (command_string)
        else:
            pm.mel.source(self.script_path)
            pm.mel.eval(command)

    @staticmethod
    def set_colors(color='yellow'):

        main_color = color
        dark_color = color
        light_color = color

        if color.lower() == 'yellow':
            main_color = '#fdfd96'
            dark_color = '#fcfc4b'
            light_color = '#fefee1'
        if color.lower() == 'red':
            main_color = '#ff6961'
            dark_color = '#ff2015'
            light_color = '#ffb2ae'
        if color.lower() == 'green':
            main_color = '#77dd77'
            dark_color = '#3ace3a'
            light_color = '#b4ecb4'
        if color.lower() == 'purple':
            main_color = '#b39eb5'
            dark_color = '#917394'
            light_color = '#d5c9d6'
        if color.lower() == 'blue':
            main_color = '#aec6cf'
            dark_color = '#8eafbc'
            light_color = '#dee8eb'

        return main_color, dark_color, light_color

    def show_help(self):
        # create a window instance
        help_win = QtWidgets.QDialog()
        help_win.setWindowTitle('Help for %s' % self.label)
        help_win.setMinimumSize(600, 100)
        help_win.setMaximumSize(600, 100)

        # create a layout
        main_layout = QtWidgets.QVBoxLayout()

        # add the help text to the layout
        help_text = QtWidgets.QLabel(self.help)
        help_text.setMaximumSize(600, 100)
        main_layout.addWidget(help_text)

        # add the layout to the window
        help_win.setLayout(main_layout)

        # show window
        help_win.exec_()

    def edit_script(self):
        if sys.platform == 'win32':
            os.startfile(self.script_path)
        else:
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener, self.script_path])


class PreferencesWindow(QtWidgets.QDialog):
    """
    Window for script folder selection
    """

    def __init__(self, parent):
        super(PreferencesWindow, self).__init__(parent)

        self.parent = parent
        self.data = parent.load_preferences()
        self.setWindowTitle('DSL Preferences')
        self.setMinimumWidth(500)

        # build UI
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # position preferences
        position_preferences_widget = QtWidgets.QWidget()
        position_preference_layout = QtWidgets.QFormLayout()
        position_preference_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        position_preference_layout.setFormAlignment(QtCore.Qt.AlignLeft)
        position_preferences_widget.setLayout(position_preference_layout)
        self.position_options = QtWidgets.QComboBox()
        self.position_options.addItems(['Primary screen, right edge',
                                        'Primary screen, left edge',
                                        'Secondary screen, right edge',
                                        'secondary screen, left edge'])
        self.position_options.setCurrentText(self.data.get('position'))
        self.position_options.currentTextChanged.connect(self.set_position)
        position_preference_layout.addRow('Position', self.position_options)
        self.docking_position_options = QtWidgets.QComboBox()
        self.docking_position_options.addItems(['left', 'right', "Don't Dock"])
        docking_position = self.data.get('docking_position')
        if docking_position is None:
            docking_position = "Don't Dock"
        self.docking_position_options.setCurrentText(docking_position)
        self.docking_position_options.currentTextChanged.connect(self.set_docking_position)
        position_preference_layout.addRow('Docking Position', self.docking_position_options)
        self.main_layout.addWidget(position_preferences_widget)

        # folders layout
        folders_widget = QtWidgets.QWidget()
        folders_layout = QtWidgets.QHBoxLayout()
        folders_layout.setContentsMargins(0, 0, 0, 0)
        folders_layout.setSpacing(0)
        folders_widget.setLayout(folders_layout)
        self.main_layout.addWidget(folders_widget)

        self.add_folder_btn = QtWidgets.QPushButton('Add Folder')
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.add_folder_btn.setMinimumHeight(24)

        self.add_folder_btn.setStyleSheet('''.QPushButton { color: black;
                                                            background-image: None; 
                                                            border-image: None; 
                                                            background-color: #77dd77; 
                                                            border-radius:0px; 
                                                            border-top-left-radius: 10px; 
                                                            border: 1px solid #77dd77;
                                                    } 
                                                    .QPushButton:hover{
                                                            background-color: #627B5E; 
                                                    } 
                                                    .QPushButton:pressed{
                                                            background-color: #233120;
                                                    }
                                                ''')

        self.remove_folder_btn = QtWidgets.QPushButton('Remove Folder')
        self.remove_folder_btn.clicked.connect(self.remove_folder)
        self.remove_folder_btn.setMinimumHeight(24)

        self.remove_folder_btn.setStyleSheet('''.QPushButton {  color: black;
                                                                background-image: None; 
                                                                border-image: None; 
                                                                background-color: #ff6961; 
                                                                border-radius:0px; 
                                                                border-top-right-radius: 10px; 
                                                                border: 1px solid #ff6961;
                                                        } 
                                                        .QPushButton:hover{
                                                                background-color: #876768; 
                                                        } 
                                                        .QPushButton:pressed{
                                                                background-color: #3B2D2E;
                                                        }
                                                    ''')

        self.list_of_folders = QtWidgets.QListWidget()
        self.list_of_folders.setAlternatingRowColors(True)

        folders_layout.addWidget(self.add_folder_btn)
        folders_layout.addWidget(self.remove_folder_btn)
        self.main_layout.addWidget(self.list_of_folders)

        # save and cancel
        save_widget = QtWidgets.QWidget()
        save_layout = QtWidgets.QHBoxLayout()
        save_widget.setLayout(save_layout)
        self.cancel_btn = QtWidgets.QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close_preferences)
        self.cancel_btn.setMinimumHeight(24)
        self.save_btn = QtWidgets.QPushButton('Save')
        self.save_btn.clicked.connect(self.save_preferences)
        self.save_btn.setMinimumHeight(24)
        save_layout.addWidget(self.cancel_btn)
        save_layout.addWidget(self.save_btn)

        self.main_layout.addWidget(save_widget)
        self.build_list()

        self.show()

    def set_position(self):
        self.data['position'] = self.position_options.currentText()

    def set_docking_position(self):
        docking_position = self.docking_position_options.currentText()
        if docking_position == "Don't Dock":
            docking_position = None
        self.data['docking_position'] = docking_position

    def save_preferences(self):
        self.parent.save_preferences(self.data)
        self.close()

    def close_preferences(self):
        self.close()

    def add_folder(self):
        """
        Add folder to list
        """
        target_dir = pm.fileDialog2(dir=os.path.expanduser('~'), ff='*.json', ds=2, fm=3, okc='Select')
        try:
            target_dir = str(target_dir[0])
            if self.data['folders']:
                if target_dir not in self.data['folders']:
                    self.data['folders'].append(target_dir)
            else:
                self.data['folders'] = [target_dir]
        except IndexError:
            return

        self.list_of_folders.clear()
        self.build_list()

    def remove_folder(self):
        """
        Remove folder from list
        """
        selected_items = self.list_of_folders.selectedItems()
        for i in selected_items:
            self.data['folders'].remove(i.text())

        self.list_of_folders.clear()
        self.build_list()

    def build_list(self):
        """
        Build the list of folders
        """
        try:
            if self.data['folders']:
                for i in self.data['folders']:
                    # add path
                    item = QtWidgets.QListWidgetItem()
                    item.setText(i)
                    item.setSizeHint(QtCore.QSize(item.sizeHint().width(), 36))

                    # create widget with buttons
                    widget = QtWidgets.QWidget()
                    widget_layout = QtWidgets.QHBoxLayout()
                    widget_layout.setContentsMargins(4, 0, 4, 4)
                    widget.setLayout(widget_layout)

                    spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                   QtWidgets.QSizePolicy.Minimum)
                    default_btn = QtWidgets.QPushButton('A')
                    default_btn.setFixedSize(24, 24)

                    default_btn.setCheckable(True)

                    default_btn.setStyleSheet('''QPushButton{background-color: #b39eb5; color: black; border:#b39eb5 1px;
                                                 border-radius:12px; max-width:24px; max-height:24px; min-width:24px;
                                                 min-height:24px;}
                                                 QPushButton:checked{background-color: #fdfd96; color: black;
                                                  border: #fdfd96 1px}''')

                    default_btn.folder = i
                    default_btn.clicked.connect(self.activate_directory)

                    if i == self.data['default_folder']:
                        default_btn.setChecked(True)

                    widget_layout.addItem(spacer)
                    widget_layout.addWidget(default_btn)

                    self.list_of_folders.addItem(item)
                    self.list_of_folders.setItemWidget(item, widget)
        except TypeError:
            print 'no preferences found'

    def activate_directory(self):
        """
        Select a directory to load into the DSL, it is also set as the default to load on launch
        """
        folder = self.sender().folder
        self.parent.current_dir = folder

        self.data['default_folder'] = folder
        # self.parent.save_preferences(self.data)

        self.list_of_folders.clear()
        self.build_list()
        self.parent.load_scripts(folder)


class DSL(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    """
    create a window with a list of buttons representing scripts in the selected folder
    """

    # noinspection PyArgumentList
    def __init__(self, parent=maya_main_window()):
        # call the parent class and pass in the parent object
        super(DSL, self).__init__(parent)

        # we have possible root paths saved in a json file
        self.preferences_file = pm.internalVar(userPrefDir=True) + '/dsl_preferences.json'
        if not os.path.isfile(self.preferences_file):
            # if we don't have a preference file save one
            self.save_preferences({'folders': '', 'default_folder': '', 'position': '',
                                   'dockable': False, 'docking_position': ''})

        self.current_dir = None

        # general window setup
        self.setWindowTitle('DSL Version 3.0')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # create fonts
        self.title_font = QtGui.QFont()
        self.title_font.setPointSize(24)
        self.title_font.setBold(True)

        self.empty_font = QtGui.QFont()
        self.empty_font.setPointSize(12)
        self.empty_font.setBold(True)

        # create a main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # add a menu bar and actions
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.file_menu = self.menu_bar.addMenu('File')
        self.preferences_action = QtWidgets.QAction('Preferences',
                                                    self,
                                                    statusTip='List of available folders',
                                                    triggered=self.show_folder_list)

        self.refresh = QtWidgets.QAction('Refresh',
                                         self,
                                         statusTip='Refresh script list',
                                         triggered=self.load_scripts)

        self.file_menu.addAction(self.preferences_action)
        self.file_menu.addAction(self.refresh)

        # load the scripts from the root dir
        self.load_scripts()

        # self.reposition()

    def save_preferences(self, preferences):
        with open(self.preferences_file, "w") as write_file:
            json.dump(preferences, write_file, indent=2)

    def reposition(self):
        try:
            data = self.load_preferences()

            # grab the window (there HAS to be a simpler way)
            window = self.parent().parent().parent().parent().parent()
            screen = QtWidgets.QDesktopWidget()
            primary_screen = screen.availableGeometry()
            secondary_screen = screen.availableGeometry(screen=1)

            position = data.get('position')
            if position == 'Primary screen, right edge':
                window.setGeometry(primary_screen.right() - 300, 30, 300, 600)
            elif position == 'Primary screen, left edge':
                window.setGeometry(primary_screen.left() - 0, 30, 300, 600)
            elif position == 'Secondary screen, right edge':
                window.setGeometry(secondary_screen.right() - 300, 30, 300, 600)
            elif position == 'secondary screen, left edge':
                window.setGeometry(secondary_screen.left() - 0, 30, 300, 600)
            else:
                return

        except TypeError:
            print 'preferences not found'

    def load_scripts(self, active_dir=None):
        """
        Find the root dir and load all of the scripts from it
        :return:
        """
        try:
            if active_dir is None:
                data = self.load_preferences()
                self.current_dir = data['default_folder']
            else:
                self.current_dir = active_dir
            self.clear_layout()

            if self.current_dir:
                self.create_layout()
            else:
                self.create_empty_layout()
        except TypeError:
            print 'preferences not found'

    def load_preferences(self):
        """
        Load the yaml with a list of possible script folders
        :return: list(str), str, list of possible script folders and a default folder
        """
        if os.path.isfile(self.preferences_file):
            try:

                with open(self.preferences_file, "r") as read_file:
                    data = json.load(read_file)

                return data
            except Exception as e:
                print e

    def show_folder_list(self):
        self.preferences_action = PreferencesWindow(self)

    def clear_layout(self):
        """
        Delete all buttons form the layout
        """
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

    def create_empty_layout(self):
        title = QtWidgets.QLabel("Something's Wrong")
        title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        title.setContentsMargins(1, 1, 1, 20)
        title.setFont(self.title_font)
        self.main_layout.addWidget(title)

        empty_widget = QtWidgets.QWidget()
        empty_layout = QtWidgets.QVBoxLayout()
        empty_widget.setLayout(empty_layout)
        empty_label = QtWidgets.QLabel('No scripts found.\nPlease use File > Preferences to add and\n'
                                       'activate a folder script')
        empty_label.setFont(self.empty_font)
        empty_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        empty_label.setMinimumSize(300, 600)
        empty_layout.addWidget(empty_label)
        self.main_layout.addWidget(empty_widget)

        self.setLayout(self.main_layout)

    def create_layout(self):
        """
        Add buttons to the window representing all of the scripts
        """
        # create the window's main layout
        title = QtWidgets.QLabel(os.path.basename(self.current_dir).title())
        title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        title.setContentsMargins(1, 1, 1, 20)
        title.setFont(self.title_font)

        self.main_layout.addWidget(title)

        # create the tab system
        tab_widget = QtWidgets.QTabWidget()
        created_tabs = {}
        scripts = self.build_script_list()

        # style tabs
        tab_widget.setStyleSheet(
            '''QTabBar::tab { background: #red; height: 25px; width: 75px; border-top-left-radius: 5px; border-top-right-radius: 5px; border: 1px solid}
               QTabBar:tab:selected{background: #4b4b4b;}''')
        # create all the tabs
        for tab, sc in scripts.iteritems():

            if tab not in created_tabs.keys():
                created_tabs[tab] = QtWidgets.QWidget()
                created_tabs[tab].vertical_layout = QtWidgets.QVBoxLayout(created_tabs[tab])
                created_tabs[tab].tab_rows = self.create_tab_rows(created_tabs[tab].vertical_layout, tab)
                tab_index = tab_widget.addTab(created_tabs[tab], tab)

                # move the Main tab to the start of the tab list
                if tab == 'Main':
                    tab_widget.tabBar().moveTab(tab_index, 0)

            for script in sc:
                # add a button to the tab
                button = DSLButton(label=script.button_name,
                                   color=script.button_color,
                                   command=script.button_tabs[tab].get('button_command'),
                                   script=script.script_name,
                                   help=script.button_help,
                                   script_path=script.file_path)

                # check if we already have a button in this location
                if created_tabs[tab].tab_rows[tab + script.button_tabs[tab].get('button_line')].count() == 0:
                    created_tabs[tab].tab_rows[tab + script.button_tabs[tab].get('button_line')].addWidget(button)

                    # add the description to the tab
                    button_description = QtWidgets.QLabel(script.button_description)
                    button_description.setMinimumSize(200, 30)
                    button_description.setMaximumSize(200, 30)
                    button_description.setContentsMargins(10, 1, 1, 1)
                    created_tabs[tab].tab_rows[tab + script.button_tabs[tab].get('button_line')].addWidget(
                        button_description)

                else:
                    print('Unable to add %s to %s there is already a button at this location' % (
                        script.button_name, tab + script.button_tabs[tab].get('button_line')))
                    continue

                    # fill out empty spaces

            for horizontal_layout in range(created_tabs[tab].vertical_layout.count()):
                found_layout = created_tabs[tab].vertical_layout.itemAt(horizontal_layout)
                if found_layout.count() == 0:
                    frame = QtWidgets.QFrame()
                    frame.setMinimumSize(200, 30)
                    frame.setMaximumSize(200, 30)
                    found_layout.addWidget(frame)

        tab_widget.setCurrentIndex(0)

        self.main_layout.addWidget(tab_widget)

        self.setLayout(self.main_layout)

    def create_tab_rows(self, tab_layout, tab_name):
        tab_rows = {}

        for i in range(1, 21):
            tab_rows[tab_name + str(i)] = QtWidgets.QHBoxLayout()
            tab_layout.addLayout(tab_rows[tab_name + str(i)])

        return tab_rows

    def build_script_list(self):
        """
        builds a list of script to load into the interface
        :return: list(Script), a list of Script objects containing
                 the script info, such as its name, location in the UI and the command to run it
        """
        # get list of files
        script_folders = [folder for folder in os.listdir(self.current_dir) if
                          os.path.isdir(os.path.join(self.current_dir, folder))]
        for folder in script_folders:
            if folder not in sys.path:
                sys.path.append(os.path.join(self.current_dir, folder))

        # search all of our directories for scripts and use their headers to determine their info
        found_scripts = {}

        for folder in script_folders:
            path = os.path.join(self.current_dir, folder)

            for f in os.listdir(path):
                script_path = os.path.join(path, f).replace('\\', '/')
                script = Script(file_path=script_path)
                if script.is_valid:
                    for location in script.button_tabs.keys():
                        try:
                            if location in found_scripts.keys():
                                location_scripts = found_scripts[location]
                                location_scripts.append(script)
                                found_scripts[location] = location_scripts
                            else:
                                found_scripts[location] = [script]
                        except AttributeError:
                            print 'failed to add script', script_path

        return found_scripts


if __name__ == "__main__":

    try:
        ui.close()
    except Exception:
        pass

    ui = DSL()
    dsl_preferences = ui.load_preferences()

    area = dsl_preferences.get('docking_position')
    if not area:
        area = None
    print 'WTF?!', area
    ui.show(dockable=True, allowedAreas=['left', 'right'], area=area, retain=False)
    ui.reposition()
