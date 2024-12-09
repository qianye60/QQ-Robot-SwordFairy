import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

nonebot.load_builtin_plugins("echo")
# nonebot.load_plugin("thirdparty_plugin")
nonebot.load_plugins("plugins")
# nonebot.load_from_toml("config.toml", encoding="utf-8")

if __name__ == "__main__":
    nonebot.run()
