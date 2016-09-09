from settings import *

DATABASES['default']['NAME'] = 'freesound'
DATABASES['default']['USER'] = 'postgres'
INSTALLED_APPS = INSTALLED_APPS + ('django_nose', )
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--with-xunit',
]
SECRET_KEY = "testsecretwhichhastobeatleast16characterslong"

RAVEN_CONFIG = {}
