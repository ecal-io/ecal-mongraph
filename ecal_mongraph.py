"""
  @package ecal_mongraph
  Create a graph out of a running eCAL network.
"""

import os
import sys
import time
import pprint

import xml.etree.ElementTree as xmltree
from xml.dom import minidom

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import networkx as nx

import ecal.core.core as ecal_core

def get_mon_d() -> dict:
  """ get eCAL monitoring dictionary

  This function initializes eCAL, collects all items for a few seconds
  and store them into a python dictionary.

  :return: the monitoring dictionary
  :rtype: dictionary
  """

  # print eCAL version and date
  print("eCAL %s (%s)\n"%(ecal_core.getversion(), ecal_core.getdate()))

  # initialize eCAL API
  ecal_core.initialize([sys.argv[0]], "ecal_mongraph")

  # initialize eCAL monitoring API
  ecal_core.mon_initialize()
  # collect monitoring information
  time.sleep(2)

  # get all eCAL entities as disctionary
  mon_d = ecal_core.mon_monitoring()

  # finalize eCAL monitoring API
  ecal_core.mon_finalize()

  # return monitoring dictionary
  return mon_d

def get_sorted_d(mon_d) -> dict:
  """ sort eCAL monitoring dictionary

  The eCAL monitoring dictionary is sorted hierarchical from hosts to processes
  to publisher and subscriber. This function is sorting out these entities by
  topics to better find connected publisher and subscriber.

  :param mon_d: the monitoring dictionary
  :type mon_d: dictionary
  :return: the topic based sorted monitoring dictionary
  :rtype: dictionary
  """

  # get topic list
  topics_l = mon_d[1]['topics']

  # get process list
  process_l = mon_d[1]['processes']

  # prepare collections
  host_d = {}
  uname_d = {}
  topic_d = {}
  topic_type_d = {}  

  # sort topics an collect information about them
  for topic in topics_l:
    sort_key = "%s-%s\n[%s]"%(topic['uname'], str(topic['pid']), topic['hname'])
    if topic['hname'] not in host_d:
      host_d[topic['hname']] = set()
    host_d[topic['hname']].add(sort_key)
    uname_d[sort_key] = topic['uname'] + ' ' + str(topic['pid'])

    # add the process to the topic dictionary if it is not already in there
    if sort_key not in topic_d:
      # get the process information from the process list
      process_information_d = list(filter(lambda p: p['hname'] == topic['hname'] and p['pid'] == topic['pid'], process_l))[0]
      # add information about the process (and empty dictionaries for topics that it is publishing or subscribing to)
      topic_d[sort_key] = {'publisher'  : {},
                           'subscriber' : {},
                           'uname'      : topic['uname'],
                           'pmemory'    : process_information_d['pmemory'],
                           'pcpu'       : process_information_d['pcpu']}

    if topic['direction'] == 'publisher':
      topic_d[sort_key]['publisher'][topic['tname']] = {"dfreq": topic['dfreq'], "tsize": topic['tsize']}
    if topic['direction'] == 'subscriber':
      topic_d[sort_key]['subscriber'][topic['tname']] = {}

    if topic['tname'] not in topic_type_d:
      topic_type_d[topic['tname']] = (topic['ttype'])

  res_d = {}
  res_d['hosts']  = host_d
  res_d['unames'] = uname_d
  res_d['topics'] = topic_d
  res_d['types']  = topic_type_d

  return res_d

def convert_to_tree(sorted_d) -> dict:
  """ convert the sorted monitoring dictionary into a XML tree

  :param sorted_d: the sorted monitoring dictionary
  :type sorted_d: dictionary
  :return: the monitoring XML tree
  :rtype: xmltree.Element
  """

  host_d       = sorted_d['hosts']
  uname_d      = sorted_d['unames']
  topic_d      = sorted_d['topics']
  topic_type_d = sorted_d['types']

  # create xml
  eroot = xmltree.Element('eCAL')
     
  host_l = sorted(host_d.keys())
  for host in host_l:
    ehost = xmltree.SubElement(eroot, 'host')
    ehost.text = host
    pid_d = {}
    for pid in host_d[host]:
      pid_d[uname_d[pid]] = pid
    uname_l = sorted(pid_d.keys())
    for uname in uname_l:
      pid = pid_d[uname]
      eprocess = xmltree.SubElement(ehost, 'process')
      eprocess.attrib['uname'] = topic_d[pid]['uname']
      eprocess.attrib['pmemory'] = str(topic_d[pid]['pmemory'])
      eprocess.attrib['pcpu'] = str(topic_d[pid]['pcpu'])
      eprocess.text = uname_d[pid]
      publisher_l = sorted(topic_d[pid]['publisher'].keys())
      for publisher in publisher_l:
        epublisher = xmltree.SubElement(eprocess, 'publisher')
        epublisher.text = publisher
        if topic_d[pid]['publisher']:
          epublisher.attrib['dfreq'] = str(topic_d[pid]['publisher'][publisher]['dfreq'])
          epublisher.attrib['tsize'] = str(topic_d[pid]['publisher'][publisher]['tsize'])
      subscriber_l = sorted(topic_d[pid]['subscriber'])
      for subscriber in subscriber_l:
        esubscriber = xmltree.SubElement(eprocess, 'subscriber')
        esubscriber.text = subscriber
  if topic_type_d:
    emessages = xmltree.SubElement(eroot, 'messages')
    messages_l = list(topic_type_d.keys()) 
    for message in messages_l:
      emessage = xmltree.SubElement(emessages, 'message')
      emessage.attrib['name'] = message
      emessage.attrib['type'] = topic_type_d[message]

  # return the tree
  return eroot

def write_xml(tree, target_file, show_file):
  """ write / show the monitoring XML tree

  :param tree: the monitoring XML tree
  :type tree: xmltree.Element
  :param target_file: file name to write the XML tree to
  :type target_file: string
  :param show_file: show the XML file with associated standard application
  :type show_file: boolean
  """

  # write to string and make it pretty
  raw_xml = xmltree.tostring(tree, 'utf-8')
  reparsed = minidom.parseString(raw_xml)
  xml_s = reparsed.toprettyxml(indent="  ")

  # check extension
  if os.path.splitext(target_file)[1].lower() != ".xml":
    target_file += '.xml'

  # write the file
  open(target_file, "w").write(xml_s)

  # show result xml
  if show_file:
    os.startfile(target_file)

def nudge(pos, x_shift, y_shift):
  return {n:(x + x_shift, y + y_shift) for n,(x,y) in pos.items()}

def find_entities(topics_d, entity):
  res_d = {}
  for uname in topics_d:
    topics = topics_d[uname]
    # do we have the entity ?
    if len(topics[entity]):
      for e in topics[entity]:
        l = []
        if e in res_d:
          l = res_d[e]
        else:
          res_d[e] = l
        l.append(uname)
  return res_d

def get_nodes(pub_d, sub_d):
  nodes_d = {}
  for host in sorted_d['hosts']:
    host_d = sorted_d['hosts'][host]
    for uname in host_d:
      attr_d = {}
      has_pub = len(sorted_d['topics'][uname]['publisher'])
      has_sub = len(sorted_d['topics'][uname]['subscriber'])
      attr_d['pname'] = sorted_d['topics'][uname]['uname']
      if has_pub and has_sub:
        attr_d['color'] = 'blue'
      else: 
        if has_pub:
          attr_d['color'] = 'red'
        else:
         if has_sub:
            attr_d['color'] = 'green'
         else:
            attr_d['color'] = 'white'
      nodes_d[uname] = attr_d
  return nodes_d

def get_edges(pub_d, sub_d):
  edges_d = {}
  edges_n = 0
  for tname in pub_d:
    if tname in sub_d:
      for pub_uname in pub_d[tname]:
        for sub_uname in sub_d[tname]:
          #print("add edge from %s to %s"%([pub_uname], [sub_uname]))
          attr_d = {}
          attr_d['label'] = tname
          edges_d[(pub_uname, sub_uname, edges_n)] = attr_d
          edges_n += 1
  return edges_d

def render(sorted_d, target_file, show_file):
  """ render / show the sorted monitoring dictionary as graph (PNG)

  :param sorted_d: the sorted monitoring dictionary
  :type sorted_d: dictionary
  :param target_file: file name to write graph to (PNG)
  :type target_file: string
  :param show_file: show the graph file with associated standard application
  :type show_file: boolean
  """

  # create the graph
  G = nx.MultiDiGraph()

  # sort pubs and subs out
  pub_d = find_entities(sorted_d['topics'], 'publisher')
  sub_d = find_entities(sorted_d['topics'], 'subscriber')

  # add the nodes
  nodes_d = get_nodes(pub_d, sub_d)
  for node in nodes_d:
    G.add_node(node, label=nodes_d[node]['pname'], color=nodes_d[node]['color'])
    #G.add_node(nodes_d[node]['pname'], color=nodes_d[node]['color'])

  # add the edges
  edges_d = get_edges(pub_d, sub_d)
  edges_l = [edge for edge in edges_d]
  for edge in edges_d:
    G.add_edge(edge[0], edge[1], label=edges_d[edge]['label'])
  
  # layout
  pos = nx.spring_layout(G, k=4, weight=2)

  # draw nodes
  colored_d = nx.get_node_attributes(G, 'color')
  color_l   = [colored_d.get(node) for node in G.nodes()]
  options = {
    "edgecolors": "black",
    "node_color" : color_l
  }
  nodes = nx.draw_networkx_nodes(G, pos, **options)

  # draw node labels
  labels = {}    
  for node in G.nodes():
    # use the pname
    labels[node] = G.nodes()[node]['label']
    # use the full name (key)
    #labels[node] = node
  pos_labels = nudge(pos, 0, 0.1)
  nx.draw_networkx_labels(G, pos_labels, labels)

  # draw edges
  edges = nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->")
  
  # draw edge labels
  #nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'label'))
  nx.draw_networkx_edge_labels(G, pos)

  # plot graph
  #ax = plt.gca()
  #ax.set_axis_off()
  #plt.show()

  # create dot
  #dot_G = nx.drawing.nx_pydot.to_pydot(G)
  #print(dot_G)

  # check extension
  if os.path.splitext(target_file)[1].lower() != ".png":
    target_file += '.png'

  # create png
  ag = nx.drawing.nx_agraph.to_agraph(G)
  ag.layout('dot')
  ag.draw(target_file)

  if show_file:
    os.startfile(target_file)
  
if __name__ == "__main__":
  sorted_d = get_sorted_d(get_mon_d())
  write_xml(convert_to_tree(sorted_d), "_result_mon_graph", False)
  render(sorted_d, "_result_mon_graph", False)
