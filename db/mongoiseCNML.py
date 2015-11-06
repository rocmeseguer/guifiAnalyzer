"""
This module converts CNML objects to MongoDB compatible dictionaries
"""


def mongoiseZone(zone):
    m_zone = vars(zone)
    m_zone['_id'] = str(m_zone['id'])
    del m_zone['id']
    m_zone['subzones'] = [str(z) for z in m_zone['subzones']]
    m_zone['nodes'] = [str(n) for n in m_zone['nodes']]
    return m_zone


def mongoiseNode(node):
    m_node = vars(node)
    # Use node id as MongoDB id
    m_node['_id'] = str(m_node['id'])
    # Delete old id element
    del m_node['id']
    # Keep id of parentZone
    m_node['parentZone'] = str(m_node['parentZone'].id)
    # Keep an array of device ids
    devices = [mongoiseDevice(d) for d in m_node['devices'].values()]
    m_node['devices'] = devices
    services = [mongoiseService(d) for d in m_node['services'].values()]
    m_node['services'] = services
    return m_node

def mongoiseService(service):
    m_service = vars(service)
    m_service['_id'] = str(m_service['id'])
    del m_service['id']
    m_service['parentDevice'] = str(m_service['parentDevice'].id)
    return m_service

def mongoiseDevice(device):
    m_device = vars(device)
    m_device['_id'] = str(m_device['id'])
    del m_device['id']
    m_device['parentNode'] = str(m_device['parentNode'].id)
    radios = [mongoiseRadio(d) for d in m_device['radios'].values()]
    m_device['radios'] = radios
    interfaces = [mongoiseInterface(d) for d in m_device['interfaces'].values()]
    m_device['interfaces'] = interfaces
    return m_device

def mongoiseRadio(radio):
    m_radio = vars(radio)
    m_radio['_id'] = {'device':str(m_radio['parentDevice'].id),\
                        'radio':str(m_radio['id'])}
    del m_radio['id']
    m_radio['parentDevice'] = str(m_radio['parentDevice'].id)
    interfaces = [mongoiseInterface(d) for d in m_radio['interfaces'].values()]
    m_radio['interfaces'] = interfaces
    return m_radio

def mongoiseInterface(interface):
    m_iface = vars(interface)
    m_iface['_id'] = str(m_iface['id'])
    del m_iface['id']
    # Watch out that the parent can be either radio or device
    m_iface['parent'] = str(m_iface['parentRadio'].id)
    del m_iface['parentRadio']
    links = [mongoiseLink(d) for d in m_iface['links'].values()]
    m_iface['links'] = links
    return m_iface


def mongoiseLink(link):
    m_link = vars(link)
    m_link['_id'] = str(m_link['id'])
    del m_link['id']
    m_link['nodeA'] = str(m_link['nodeA'].id)
    m_link['nodeB'] = str(m_link['nodeB'].id)
    m_link['deviceA'] = str(m_link['deviceA'].id)
    m_link['deviceB'] = str(m_link['deviceB'].id)
    m_link['interfaceA'] = str(m_link['interfaceA'].id)
    m_link['interfaceB'] = str(m_link['interfaceB'].id)
    m_link['parentInterface'] = str(m_link['parentInterface'].id)
    return m_link

