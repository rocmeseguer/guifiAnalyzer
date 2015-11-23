import os
import sys
# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append('lib')
# sys.path.append('lib/libcnml')
# sys.path.append('lib/pyGuifiAPI')

from ..lib import libcnml
from ..lib.libcnml import logger as logger
import logging

# Change format of logger
logger.setLevel(logging.DEBUG)

from ..lib import pyGuifiAPI
from ..lib.pyGuifiAPI.error import GuifiApiError

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
    conn = pyGuifiAPI.GuifiAPI('edimoger', '100105a', secure=False)
    logger.info("Going to authenticate")
    try:
        conn.auth()
    except GuifiApiError as e:
        print e.reason
    # logger.info(conn.is_authenticated())
    # logger.info(conn.authToken)
    logger.info("Authenticated succesfully")
    return conn


def parseCNMLZone(zoneId, conn):
    """
    Return a zone parced by libcnml
    """
    zonefile = os.path.join(os.getcwd(), 'guifiAnalyzerOut','cnml', str(zoneId))
    if not os.path.isfile(zonefile):
        logger.info('Cannot find zone %s locally. Will download', zoneId)
        zonefile = getCNMLZone(zoneId, conn)
    try:
        return libcnml.CNMLParser(zonefile)
    except IOError:
        print _('Error opening CNML file: '), zonefile


def getCNMLZone(zoneId, conn):
    """
    Return unparsed detail CNML of zone
    Search for file locally, if not found Download zone cnml
    """
    logger.info('Downloading Zone %s detailed CNML ', zoneId)
    try:
        fp = conn.downloadCNML(int(zoneId), 'detail')
        filename = os.path.join(os.getcwd(), 'cnml', str(zoneId))
        with open(filename, 'w') as zonefile:
            zonefile.write(fp.read())
        logger.info('Zone saved successfully to %s', str(filename))
        return filename
    except URLError as e:
        print _('Error accessing to the Internet:'), str(e.reason)


# Careful for Links: If there is a node B it will return this as Id
def getParentCNMLNode(comp):
    """
    Return the CNMLNode object of the parent node of a component
    """
    if isinstance(comp, libcnml.libcnml.CNMLLink):
        return getParentCNMLNode(comp.parentInterface)
    elif isinstance(comp, libcnml.libcnml.CNMLInterface):
        return getParentCNMLNode(comp.parentRadio)
    elif isinstance(comp, libcnml.libcnml.CNMLRadio):
        return getParentCNMLNode(comp.parentDevice)
    elif isinstance(comp, libcnml.libcnml.CNMLDevice):
        return getParentCNMLNode(comp.parentNode)
    elif isinstance(comp, libcnml.libcnml.CNMLService):
        return getParentCNMLNode(comp.parentNode)
    elif isinstance(comp, libcnml.libcnml.CNMLNode):
        return comp
    else:
        return None


def cnmlObjectCopy(obj):
    if isinstance(obj, libcnml.libcnml.CNMLZone):
        new = libcnml.libcnml.CNMLZone(
            obj.id,
            obj.parentzone,
            obj.totalAPs,
            obj.box,
            obj.totalClients,
            obj.totalDevices,
            obj.totalLinks,
            obj.totalServices,
            obj.totalNodes,
            obj.title,
            obj.graphserverId
            )
        new.subzones = obj.subzones.copy()
        new.nodes = obj.nodes.copy()
    elif isinstance(obj, libcnml.libcnml.CNMLNode):
        new = libcnml.libcnml.CNMLNode(
            obj.id,
            obj.title,
            obj.latitude,
            obj.longitude,
            obj.totalLinks,
            obj.status,
            obj.parentZone,
            obj.graphserverId,
            obj.created)
        new.devices = obj.devices.copy()
        new.services = obj.services.copy()
    elif isinstance(obj, libcnml.libcnml.CNMLService):
        new = libcnml.libcnml.CNMLService(
            obj.id,
            obj.title,
            obj.type,
            obj.status,
            obj.created,
            obj.parentDevice)
    elif isinstance(obj, libcnml.libcnml.CNMLDevice):
        new = libcnml.libcnml.CNMLDevice(
            obj.id,
            obj.name,
            obj.firmware,
            obj.status,
            obj.title,
            obj.type,
            obj.parentNode,
            obj.graphserverId)
        new.radios = obj.radios.copy()
        new.interfaces = obj.interfaces.copy()
    elif isinstance(obj, libcnml.libcnml.CNMLRadio):
        new = libcnml.libcnml.CNMLRadio(
            obj.id,
            obj.protocol,
            obj.snmp_name,
            obj.snmp_index,
            obj.ssid,
            obj.mode,
            obj.antenna_gain,
            obj.antenna_angle,
            obj.channel,
            obj.clients_accepted,
            obj.parentDevice)
        new.interfaces = obj.interfaces.copy()
    elif isinstance(obj, libcnml.libcnml.CNMLInterface):
        new = libcnml.libcnml.CNMLInterface(
            obj.id,
            obj.snmp_name,
            obj.snmp_index,
            obj.ipv4,
            obj.mask,
            obj.mac,
            obj.type,
            obj.parentRadio)
        new.links = obj.links.copy()
    elif isinstance(obj, libcnml.libcnml.CNMLLink):
        new = libcnml.libcnml.CNMLLink(
            obj.id,
            obj.status,
            obj.type,
            obj.deviceA,
            obj.interfaceA,
            obj.nodeA,
            obj.parentInterface)
        new.nodeB = obj.nodeB
        new.deviceB = obj.deviceB
        new.interfaceB = obj.interfaceB
    else:
        logger.warning(
            'No CNML object to copy. Found object of type %s',
            type(obj))
        new = obj
    return new


def cnmlNodeToDict(node):
    """
    Convert a CNMLNode object to a dictionary with accessable properties:

    """
    result = {}
    for device in node.getDevices():
        result[('device', device)] = {}
        for interface in device.getInterfaces():
            result[('device', device)][('interface', interface)] = {}
            for link in interface.getLinks():
                result[('device', device)][
                    ('interface', interface)]['link', link] = {}
        for radio in device.getRadios():
            result[('device', device)]['radio', radio] = {}
            for interface in radio.getInterfaces():
                result[('device', device)]['radio', radio][
                    ('interface', interface)] = {}
                for link in interface.getLinks():
                    result[('device', device)]['radio', radio][
                        ('interface', interface)]['link', link] = {}
    return result


def getCNMLNodeLinks(node):
    #node = self.getNode(node)
    links = {}
    linkIds = []
    for device in node.getDevices():
        for radio in device.getRadios():
            for iface in radio.getInterfaces():
                # Add new links (ignoring duplicates)
                temp = [l for l in iface.links if l not in linkIds]
                linkIds = linkIds + temp
                for link in temp:
                    links.update({link: iface.links[link]})
        for iface in device.getInterfaces():
            temp = [l for l in iface.links if l not in linkIds]
            linkIds = linkIds + temp
            for link in temp:
                links.update({link: iface.links[link]})
    return links


def getCNMLCoreZone(zoneIn):
    """
    Return Zone containing only core part of the network
    """
    zone = cnmlObjectCopy(zoneIn)
    nodes = {node.id: cnmlObjectCopy(
            node) for node in zone.getNodes() if node.totalLinks > 1}
    zone.nodes = nodes
    for node in zone.getNodes():
        node.devices = {device.id: cnmlObjectCopy(
            device) for device in node.getDevices()}
        node.services = {service.id: cnmlObjectCopy(
            service) for service in node.getServices()}
        for device in node.getDevices():
            device.interfaces = {
                iface.id: cnmlObjectCopy(iface) for iface in device.getInterfaces()}
            device.radios = {
                (device.id, radio.id): cnmlObjectCopy(radio) for radio in device.getRadios()}
            for interface in device.getInterfaces():
                # Remove links that at least one of the involved nodes has less than 2 links
                interface.links = {link.id: cnmlObjectCopy(
                    link) for link in interface.getLinks() if (link.nodeA).totalLinks > 1 and (link.nodeB).totalLinks > 1}
            for radio in device.getRadios():
                radio.interfaces = {
                    iface.id: cnmlObjectCopy(iface) for iface in radio.getInterfaces()}
                for interface in radio.getInterfaces():
                    # Remove links that at least one of the involved nodes has less than 2 links
                    interface.links = {link.id: cnmlObjectCopy(
                        link) for link in interface.getLinks() if (link.nodeA).totalLinks > 1 and (link.nodeB).totalLinks > 1}
    return zone

def dump(obj):
    """
    Dump objects attributes
    """
    for attr in dir(obj):
        print "obj.%s = %s" % (attr, getattr(obj, attr))


def print_dict(dictionary, ident='\t', braces=0):
    """ Recursively prints nested dictionaries."""
    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            print '%s%s%s%s%s' % (ident, braces * '[', key[0], key[1], braces * ']')
            print_dict(value, ident + ident, braces + 0)
        else:
            print ident + '%s \t %s : %s' % (key[0], key[1], str(value))
