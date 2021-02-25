from .settings import *
# you need to set "myproject = 'prod'" as an environment variable
# in your OS (on which your website is hosted)
if env.bool('PRODUCTION') == True:
   from .production_settings import *
else:
   from .debug_settings import *
