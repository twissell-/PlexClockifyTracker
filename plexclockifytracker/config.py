class Config:
    __conf = {
        "clockify_api_key": "",
        "plex_username": "",
        "mapping": [{"libraries": ["TV Shows", "Movies"], "project": "Watching TV"}],
    }

    __setters = __conf.keys()

    @staticmethod
    def get(name):
        return Config.__conf[name]

    @staticmethod
    def set(name, value):
        if name in Config.__setters:
            Config.__conf[name] = value
        else:
            raise NameError("Name not accepted in set() method")


def configure(
    clockify_api_key: str,
    plex_username: str,
    mapping: "list[dict]" = None,
):

    Config.set("clockify_api_key", clockify_api_key)
    Config.set("plex_username", plex_username)
    Config.set("mapping", mapping)
