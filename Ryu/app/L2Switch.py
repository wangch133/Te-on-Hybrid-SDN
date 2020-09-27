from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class L2Switch(app_manager.RyuApp):
    #set openflow protocol
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        #set a dictionary to save MAC2PORT table
        self.mac_port_table = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures)
    def switch_features_handler(self,ev):
        '''
        manage the initial link, from switch to controller
        '''
        #first parse event to get datapath and openflow protocol 
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        self.logger.info("datapath: %s link to controller",datapath.id)

        #secondly set match and action
        #Match() means that all data message match successful
        match = ofp_parser.OFPMatch()
        #set receive port and buffer for switch
        actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]

        #add flow and send it to switch in add_flow
        self.add_flow(datapath,0,match,actions,"default flow entry")

    def add_flow(self,datapath,priority,match,actions,extra_info):
        '''
        add flow entry to switch
        '''
        #get open flow protocol infomation
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        #set instruction infomation from openflow protocol 1.3
        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]

        #set flow entry mod
        mod = ofp_parser.OFPFlowMod(datapath=datapath,priority=priority,match=match,instructions=inst)

        print("send "+extra_info)
        #send flow entry to switch
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
    def packet_in_handler(self,ev):
        '''
        manage infomation from switch
        '''
        #first parser openflow protocol
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        #get datapath id from datapath, and save dpid into MAC table (default)
        dpid = datapath.id
        self.mac_port_table.setdefault(dpid, {})

        #analysize packet, get ethernet data and host MAC info
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        #get switch port where host packet send in
        in_port = msg.match['in_port']

        self.logger.info("Ctl get pkt, Mac from: %s send to: %s, send from dp: %s, in_port is: %s"
                            ,src,dst,dpid,in_port)
    
        #save src data into dictionary---MAC address table
        self.mac_port_table[dpid][src] = in_port

        #query MAC address table to get destinction host's port from current datapath
        #---first: find port to send packet
        #---second: not find port,so send packet by flood
        if dst in self.mac_port_table[dpid]:
            Out_Port = self.mac_port_table[dpid][dst]
        else:
            Out_Port = ofproto.OFPP_FLOOD

        #set match-action from above status
        actions = [ofp_parser.OFPActionOutput(Out_Port)]

        #add a new flow entry to switch by add_flow
        if Out_Port != ofproto.OFPP_FLOOD:
            match = ofp_parser.OFPMatch(in_port=in_port,eth_dst = dst)
            self.add_flow(datapath, 1, match, actions,"a new flow entry by specify port")
            self.logger.info("send packet to switch port: %s", Out_Port)

        #finally send the packet to datapath, to achive self_learn_switch
        Out = ofp_parser.OFPPacketOut(datapath=datapath,buffer_id=msg.buffer_id,
                                in_port=in_port,actions=actions,data=msg.data)

        datapath.send_msg(Out)