import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('lib')
sys.path.append('lib/libcnml')
sys.path.append('lib/pyGuifiAPI')

import libcnml
from libcnml import logger as logger
import logging

# Change format of logger
logger.setLevel(logging.DEBUG)

import pyGuifiAPI
from pyGuifiAPI.error import GuifiApiError

from utils import *

from urllib2 import URLError

import gettext
_ = gettext.gettext

import json
import operator
import copy


def authenticate():
    """
    Authenticate to the test server (using pyGuififAPI library)
    """
    conn = pyGuifiAPI.GuifiAPI('edimoger', '100105a',secure=False)
    logger.info("Going to authenticate")
    try:
        conn.auth()
    except GuifiApiError, e:
        print e.reason
    #logger.info(conn.is_authenticated())
    #logger.info(conn.authToken)
    logger.info("Authenticated succesfully")
    return conn

def parseCNMLZone(zoneId,conn):
    """
    Return a zone parced by libcnml
    """
    zonefile = os.path.join(os.getcwd(),'cnml',str(zoneId))
    if not os.path.isfile(zonefile):
        logger.info('Cannot find zone %s locally. Will download',zoneId)
        zonefile = getCNMLZone(zoneId,conn)
    try:
        return libcnml.CNMLParser(zonefile)
    except  IOError:
        print _('Error opening CNML file: ' ), zonefile

def getCNMLZone(zoneId,conn):
    """
    Return unparsed detail CNML of zone
    Search for file locally, if not found Download zone cnml
    """
    logger.info('Downloading Zone %s detailed CNML ',zoneId)
    try:
        fp = conn.downloadCNML(int(zoneId), 'detail')
        filename = os.path.join(os.getcwd(),'cnml',str(zoneId))
        with open(filename, 'w') as zonefile:
            zonefile.write(fp.read())
        logger.info('Zone saved successfully to %s', str(filename))
        return filename
    except URLError, e:
        print _('Error accessing to the Internet:'), str(e.reason)


# Careful for Links: If there is a node B it will return this as Id
def getParentCNMLNode(comp):
    """
    Return the CNMLNode object of the parent node of a component
    """
    if type(comp) is libcnml.libcnml.CNMLLink :
        return getParentCNMLNode(comp.parentInterface)
    elif type(comp) is libcnml.libcnml.CNMLInterface :
        return getParentCNMLNode(comp.parentRadio)
    elif type(comp) is libcnml.libcnml.CNMLRadio :
        return getParentCNMLNode(comp.parentDevice)
    elif type(comp) is libcnml.libcnml.CNMLDevice :
        return getParentCNMLNode(comp.parentNode)
    elif type(comp) is libcnml.libcnml.CNMLNode :
        return comp
    else :
        return None

def cnmlNodeToDict(node):
    """
    Convert a CNMLNode object to a dictionary with accessable properties:

    """
    result = {}
    for device in node.getDevices():
        result[('device',device)] = {}
        for interface in device.getInterfaces():
            result[('device',device)][('interface',interface)]  = {}
            for link in interface.getLinks():
                result[('device',device)][('interface',interface)]['link',link] = {}
        for radio in device.getRadios():
            result[('device',device)]['radio',radio] = {}
            for interface in radio.getInterfaces():
                result[('device',device)]['radio',radio][('interface',interface)] = {}
                for link in interface.getLinks():
                    result[('device',device)]['radio',radio][('interface',interface)]['link',link] = {}
    return result

def dump(obj):
	"""
	Dump objects attributes
	"""
	for attr in dir(obj) :
		print "obj.%s = %s" % (attr, getattr(obj, attr))


def print_dict(dictionary, ident = '\t', braces=0):
    """ Recursively prints nested dictionaries."""
    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            print '%s%s%s%s%s' %(ident,braces*'[',key[0],key[1],braces*']')
            print_dict(value, ident+ident, braces+0)
        else:
            print ident+'%s \t %s : %s' %(key[0], key[1], str(value))