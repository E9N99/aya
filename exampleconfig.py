from sample_config import Config
class Development(Config):
    # get this values from the my.telegram.org
    APP_ID = 9671629
    API_HASH = "be5c84e9dc1ca0e2b53d54b71e575124"
    # the name to display in your alive message
    ALIVE_NAME = "BiLaL"
    # create any PostgreSQL database (i recommend to use elephantsql) and paste that link here
    DB_URI = ""
    # After cloning the repo and installing requirements do python3 telesetup.py an fill that value with this
    STRING_SESSION = ""
    # create a new bot in @botfather and fill the following vales with bottoken and username respectively
    TG_BOT_TOKEN = ""
    # command handler
    COMMAND_HAND_LER = "."
    # sudo enter the id of sudo users userid's in that array
    SUDO_USERS = []
    # command hanler for sudo
    SUDO_COMMAND_HAND_LER = "."
