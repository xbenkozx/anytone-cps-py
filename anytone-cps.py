
import sys, argparse, os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from CPS.UserSettings import UserSettings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--firmware')
    parser.add_argument('-d','--debug', action='store_true')
    args = parser.parse_args()

    if args.firmware != None:
        if args.firmware == '4.00':
            pass
            # from CPS_400.UI import MainWindow, UI_Constants, Theme
            # from CPS_400.AnytoneMemory import AnyToneMemory
            # from CPS_400.UserSettings import UserSettings
        else:
            print('Invalid FW Version. Defaulting to newest')
            from CPS.UI import MainWindow, UI_Constants, Theme
            from CPS.AnytoneMemory import AnyToneMemory
    else:
        from CPS.UI import MainWindow, UI_Constants, Theme
        from CPS.AnytoneMemory import AnyToneMemory

    AnyToneMemory.init()
    UserSettings.load()

    app = QApplication(sys.argv)

    # Load Theme
    Theme.applyTheme(app, UserSettings.theme[0], UserSettings.theme[1])
    
    widget = MainWindow()
    widget.debug = args.debug
    widget.show()
    app_icon = QIcon(UI_Constants.iconPath())
    widget.setWindowIcon(app_icon)
    sys.exit(app.exec())
