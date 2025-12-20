import configparser, ast, os

class UserSettings:

    theme = (0,0)
    comport = ''
    virtual_com_file = ''
    read_write_options = 1

    def save():
        config = configparser.ConfigParser()
        config['User'] = {
            'theme': UserSettings.theme,
            'comport': UserSettings.comport,
            'virt_com_file': UserSettings.virtual_com_file,
            'read_write_options': UserSettings.read_write_options
        }

        with open('user.settings', 'w') as f:
            config.write(f)

    def load():
        if not os.path.isfile('user.settings'):
            return
        config = configparser.ConfigParser()
        config.read('user.settings')

        if 'theme' in config['User']:
            UserSettings.theme = ast.literal_eval(config['User']['theme'])
        if 'comport' in config['User']:
            UserSettings.comport = config['User']['comport']
        if 'virt_com_file' in config['User']:
            UserSettings.virtual_com_file = config['User']['virt_com_file']
        if 'read_write_options' in config['User']:
            UserSettings.read_write_options = int(config['User']['read_write_options'])