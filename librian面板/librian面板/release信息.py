import logging

from pathlib import Path


此處 = Path(__file__).parent

是release = (此處 / '../../.librian_release_info').is_file()

if 是release: 
    logging.warning('是release！')
else:
    logging.warning('不是release！')

