import logging
import sys


version = (0, 0, 1)
snapshot = None
base_version = '.'.join(map(str, version))
__version__ = f'{base_version}-{snapshot}' if snapshot else base_version
app_name = "Security Analysis"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
