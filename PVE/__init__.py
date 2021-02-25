from .settings import *

if env.bool('PRODUCTION') == True:
    from .production_settings import *
else:
    from .debug_settings import *
