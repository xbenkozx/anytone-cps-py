
import sys, os, darkdetect

### DEBUG
# os.system('python build-ui.py')
# os.system('python compile.py')
###


from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyleFactory
from qt_material import apply_stylesheet
from CPS.UI import MainWindow, UI_Constants, Theme
from CPS.AnytoneMemory import AnyToneMemory
from CPS.Device import AnyToneVirtualDevice
from PySide6.QtSerialPort import QSerialPortInfo
from CPS.UserSettings import UserSettings



if __name__ == "__main__":
    AnyToneMemory.init()
    UserSettings.load()

    # atd = AnyToneVirtualDevice()
    # with open('bin-dump2.bin', 'rb') as f:
    #     atd.bin_data = bytearray(f.read())
    # atd.readRadioData()

    app = QApplication(sys.argv)

    # Load Theme
    Theme.applyTheme(app, UserSettings.theme[0], UserSettings.theme[1])
    
    widget = MainWindow()
    widget.show()
    app_icon = QIcon(UI_Constants.iconPath())
    widget.setWindowIcon(app_icon)
    sys.exit(app.exec())
