from starlette.config import Config, undefined

env = Config()

IS_TESTING = env("IS_TESTING", cast=str, default="").lower() == "true"

if IS_TESTING:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""
else:
    SUPABASE_URL = env("SUPABASE_URL", cast=str, default=undefined)
    SUPABASE_KEY = env("SUPABASE_KEY", cast=str, default=undefined)
