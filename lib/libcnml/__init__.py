# __init__.py - Guifi.net API handler
# Copyright (C) 2012 Pablo Castellano <pablo@anche.no>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

__version__ = '0.7'
__author__ = 'Pablo Castellano <pablo@anche.no>'
__license__ = 'GPLv3+'

__all__ = ['libcnml']

import logging
logger = logging.getLogger(__name__)
# To change the logging level of libcnml use this code in your program:
#  import libcnml
#  import logging
#  libcnml.logger.setLevel(logging.INFO)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(fmt='%(asctime)s |  %(pathname)s | %(levelname)s:%(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

from .libcnml import CNMLParser, Status
