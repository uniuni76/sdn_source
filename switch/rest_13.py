import json

from ryu.app import switch_13
from webob import Response
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
from ryu.lib.ofctl_utils import str_to_int
import peewee


simple_switch_instance_name = 'switch_api_app'
db1 = peewee.SqliteDatabase("/root/data1.db")
db2 = peewee.SqliteDatabase("/root/data1.db")

class Flow1(peewee.Model):
    in_port1 = peewee.IntegerField()
    mac_address1 = peewee.TextField()
    out_port1 = peewee.IntegerField()
    in_port2 = peewee.IntegerField()
    mac_address2 = peewee.TextField()
    out_port2 = peewee.IntegerField()
    datapath = peewee.TextField()

    class Meta:
        database = db1

class Flow2(peewee.Model):
    in_port1 = peewee.IntegerField()
    mac_address1 = peewee.TextField()
    out_port1 = peewee.IntegerField()
    in_port2 = peewee.IntegerField()
    mac_address2 = peewee.TextField()
    out_port2 = peewee.IntegerField()
    datapath = peewee.TextField()

    class Meta:
        database = db2

class SwitchRest13(switch_13.Switch13):

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SwitchController,
                      {simple_switch_instance_name: self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})
    
    def set_flow(self, dpid, in_port, mac_address, out_port):
        datapath = self.switches.get(dpid)
        parser = datapath.ofproto_parser

        actions = [parser.OFPActionOutput(out_port)]
        match = parser.OFPMatch(in_port=in_port, eth_dst=mac_address)

        self.add_flow(datapath, 1, match, actions)

        return 
    
class SwitchController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(SwitchController, self).__init__(req, link, data, **config)
        self.simple_switch_app = data[simple_switch_instance_name]

    @route('switch', '/add/{in_port1}', methods=['GET'])
    def add_mac_table(self, req, **kwargs):

        simple_switch = self.simple_switch_app
        in_port1 = str_to_int(kwargs['in_port1'])

        flow1 = Flow1.get(Flow1.in_port1 == in_port1)
        flow2 = Flow1.get(Flow2.in_port1 == in_port1)
        dpid1 = dpid_lib.str_to_dpid(flow1.datapath)
        dpid2 = dpid_lib.str_to_dpid(flow2.datapath)

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        return simple_switch.set_flow(dpid1, flow1.in_port1, flow1.mac_address1, flow1.out_port1,
                                       dpid2, flow2.in_port1, flow2.mac_address1, flow2.out_port1)