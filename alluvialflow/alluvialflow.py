"""
  alluvialflow
  ~~~~~~~~~~~~

  Alluvial flow visualisations in Python.

  :copyright: 2015 by Martin Dittus, martin@dekstop.de
  :license: AGPL3, see LICENSE.txt for more details
"""

from collections import defaultdict

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

# ===================
# = Flow data model =
# ===================

# interface
class FlowDataSource:
  
  # Returns an ordered list of node names
  def get_nodes(self):
    raise Exception('Not implemented')
  
  # returns a DataFrame[step, node; size]
  def get_sequence(self): 
    raise Exception('Not implemented')
  
  # returns a DataFrame[step1, node1, step2, node2; size]
  def get_flows(self): 
    raise Exception('Not implemented')

# ==========
# = Layout =
# ==========

# TODO: find a more elegant way to skip missing node/flow entries without all these try/except blocks
class AlluvialFlowLayout:
  # flow_data_source: a FlowDataSource instance
  # scale_weights: a scaling function for scalars.
  # compact: adjust vertical node spacing to current flow sizes? Otherwise keep it constant throughout.
  def __init__(self, flow_data_source, 
         node_margin=50, node_width=0.02,
         scale_weights=lambda n: n,
         compact=True,
         show_stationary_component=True):
    self.flow_data_source = flow_data_source
    self.node_margin = node_margin
    self.node_width = node_width
    self.scale_weights = scale_weights
    self.compact = compact
    self.show_stationary_component = show_stationary_component
    self.__layout()
  
  def __layout(self):
    nodes = self.flow_data_source.get_nodes()     # ordered list of node names
    sequence = self.flow_data_source.get_sequence() # DataFrame[step, node; size]
    steps = sequence.index.levels[0]        # already sorted
    flows = self.flow_data_source.get_flows()     # DataFrame[step1, node1, step2, node2; size]

    self.nodes = nodes
    self.steps = steps
    
    self.minx = 0
    self.maxx = len(steps) - 1 + 0.3
    self.miny = 0
    self.maxy = 0 # will be updated during layout
    
    # step -> x
    self.step_x = dict(zip(steps, range(len(steps))))

    # step -> node -> y1/y2
    self.node1_y1 = defaultdict(lambda: dict())
    self.node1_y2 = defaultdict(lambda: dict())
    self.node2_y1 = defaultdict(lambda: dict())
    self.node2_y2 = defaultdict(lambda: dict())

    # node -> size
    if self.compact==False:
      self.node_maxsize = defaultdict(lambda: 0)
      for step in steps:
        for node1 in nodes:
          try:
            node = sequence.loc[step, node1]
            node_size = self.scale_weights(node['size'])
            self.node_maxsize[node1] = max(self.node_maxsize[node1], node_size)
          except KeyError:
            pass

    # step -> node1 -> node2 -> y-center
    self.edge_node1_y = defaultdict(lambda: defaultdict(lambda: dict())) # source
    self.edge_node2_y = defaultdict(lambda: defaultdict(lambda: dict())) # destination

    # step -> node1 -> node2 -> size
    self.edge_size = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0))) # edge

    for step1, step2 in zip(steps[:-1], steps[1:]):
      # edge sizes
      pos = self.miny
      for node1 in nodes:
        for node2 in nodes:
          try:
            flow = flows.loc[step1, node1, step2, node2]
            size = self.scale_weights(flow['size'])
            self.edge_size[step1][node1][node2] = size
          except KeyError:
            # skip missing node/flow entries... this awkward code pattern repeats below.
            pass
        
      # source ports
      pos = self.miny
      for node1 in nodes:
        self.node1_y1[step1][node1] = pos
        try:
          node = sequence.loc[step1, node1]
          node_size = self.scale_weights(node['size'])
          total_node_flow_size = 0
          for node2 in nodes:
            try:
              flow = flows.loc[step1, node1, step2, node2]
              size = self.scale_weights(flow['size'])
              self.edge_node1_y[step1][node1][node2] = pos + (size/2.0)
              total_node_flow_size += size
              pos += size
            except KeyError:
              pass
          if self.show_stationary_component:
            pos += node_size - total_node_flow_size # "in" flow
        except KeyError:
          pass
        self.node1_y2[step1][node1] = pos
        if self.compact==False:
          pos = self.node1_y1[step1][node1] + self.node_maxsize[node1]
        pos += self.node_margin
      self.maxy = max(self.maxy, pos)
        
      # destination ports
      pos = self.miny
      for node2 in nodes:
        self.node2_y1[step2][node2] = pos
        try:
          node = sequence.loc[step2, node2]
          node_size = self.scale_weights(node['size'])
          total_node_flow_size = 0
          for node1 in nodes:
            try:
              flow = flows.loc[step1, node1, step2, node2]
              size = self.scale_weights(flow['size'])
              self.edge_node2_y[step2][node1][node2] = pos + (size/2.0)
              total_node_flow_size += size
              pos += size
            except KeyError:
              pass
          if self.show_stationary_component:
            pos += node_size - total_node_flow_size # "out" flow
        except KeyError:
          pass
        self.node2_y2[step2][node2] = pos
        if self.compact==False:
          pos = self.node2_y1[step2][node2] + self.node_maxsize[node2]
        pos += self.node_margin
      self.maxy = max(self.maxy, pos)


# ==========
# = Styles =
# ==========

# interface
class DiagramStyle:
  def get_nodecolor(self, node):
    raise Exception('Not implemented')

  def get_nodealpha(self, node):
    raise Exception('Not implemented')

  def get_nodezorder(self, node):
    raise Exception('Not implemented')

  def get_edgecolor(self, step1, node1, step2, node2):
    raise Exception('Not implemented')
  
  def get_edgealpha(self, step1, node1, step2, node2):
    raise Exception('Not implemented')
  
  def get_edgezorder(self, step1, node1, step2, node2):
    raise Exception('Not implemented')
  
  def get_curve(self):
    raise Exception('Not implemented')

  def get_facecolor(self):
    raise Exception('Not implemented')
  
  def get_textcolor(self):
    raise Exception('Not implemented')
  
  def get_showlegend(self):
    raise Exception('Not implemented')

# Blue nodes and edges.
class SimpleStyle(DiagramStyle):
  def __init__(self, 
         nodecolor='#75A8EB', nodealpha=1.0, 
         edgecolor='#75A8EB', edgealpha=0.6,
         curve=0.4,
         facecolor='white', textcolor='black',
        showlegend=True):
    self.nodecolor = nodecolor
    self.nodealpha = nodealpha
    self.edgecolor = edgecolor
    self.edgealpha = edgealpha
    self.curve = curve
    self.facecolor = facecolor
    self.textcolor = textcolor
    self.showlegend = showlegend
    
  def get_nodecolor(self, node):
    return self.nodecolor
  
  def get_nodealpha(self, node):
    return self.nodealpha

  def get_nodezorder(self, node):
    return None

  def get_edgecolor(self, step1, node1, step2, node2):
    return self.edgecolor
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    return None
  
  def get_curve(self):
    return self.curve

  def get_facecolor(self):
    return self.facecolor
  
  def get_textcolor(self):
    return self.textcolor
  
  def get_showlegend(self):
    return self.showlegend

# Blue for ingroup-flows, grey for everything else.
class IngroupStyle(DiagramStyle):
  def __init__(self, ingroup_nodes,
         ingroup_color='#75A8EB', ingroup_zorder=1, 
         outgroup_color='#cccccc', outgroup_zorder=0,
         nodealpha=1.0, edgealpha=0.9,
         curve=0.4,
         facecolor='white', textcolor='black',
        showlegend=True):
    self.ingroup_nodes = ingroup_nodes
    self.ingroup_color = ingroup_color
    self.ingroup_zorder = ingroup_zorder
    self.outgroup_color = outgroup_color
    self.outgroup_zorder = outgroup_zorder
    self.nodealpha = nodealpha
    self.edgealpha = edgealpha
    self.curve = curve
    self.facecolor = facecolor
    self.textcolor = textcolor
    self.showlegend = showlegend
    
  def get_nodecolor(self, node):
    if node in self.ingroup_nodes:
      return self.ingroup_color
    else:
      return self.outgroup_color
  
  def get_nodealpha(self, node):
    return self.nodealpha

  def get_nodezorder(self, node):
    if node in self.ingroup_nodes:
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

  def get_edgecolor(self, step1, node1, step2, node2):
    if (node1==node2) and (node1 in self.ingroup_nodes):
      return self.ingroup_color
    else:
      return self.outgroup_color
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    if (node1==node2) and (node1 in self.ingroup_nodes):
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

  def get_curve(self):
    return self.curve

  def get_facecolor(self):
    return self.facecolor
  
  def get_textcolor(self):
    return self.textcolor
  
  def get_showlegend(self):
    return self.showlegend

# Blue for all ingroup source flows (inflows), grey for everything else.
class IngroupInflowStyle(IngroupStyle):
  def get_edgecolor(self, step1, node1, step2, node2):
    if node2 in self.ingroup_nodes:
      return self.ingroup_color
    else:
      return self.outgroup_color
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    if node2 in self.ingroup_nodes:
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

# Blue for all ingroup destination flows (outflows), grey for everything else.
class IngroupOutflowStyle(IngroupStyle):
  def get_edgecolor(self, step1, node1, step2, node2):
    if node1 in self.ingroup_nodes:
      return self.ingroup_color
    else:
      return self.outgroup_color
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    if node1 in self.ingroup_nodes:
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

# Blue for all ingroup source/destination flows (inflows and outflows), grey for everything else.
class IngroupAllflowStyle(IngroupStyle):
  def get_edgecolor(self, step1, node1, step2, node2):
    if (node1 in self.ingroup_nodes) or (node2 in self.ingroup_nodes):
      return self.ingroup_color
    else:
      return self.outgroup_color
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    if (node1 in self.ingroup_nodes) or (node2 in self.ingroup_nodes):
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

# Maps nodes onto the full range of a cmap colour palette.
# Flows are coloured by their destination node.
# Any nodes not in the "nodes" list are considered part of the outgroup, and coloured differently.
class GradientStyle(DiagramStyle):
  def __init__(self, nodes,
         cmap=plt.get_cmap('YlOrRd'), ingroup_zorder=10, 
         outgroup_color='#666666', outgroup_zorder=1,
         nodealpha=1.0, edgealpha=0.8,
         curve=0.4,
         facecolor='#181820', textcolor='#999999',
        showlegend=True):
    self.nodes = nodes
    self.cmap = cmap
    self.node_color_map = dict(zip(nodes, np.linspace(0, 1, len(nodes))))
    self.ingroup_zorder = ingroup_zorder
    self.outgroup_color = outgroup_color
    self.outgroup_zorder = outgroup_zorder
    self.nodealpha = nodealpha
    self.edgealpha = edgealpha
    self.curve = curve
    self.facecolor = facecolor
    self.textcolor = textcolor
    self.showlegend = showlegend
    
  def get_nodecolor(self, node):
    if node in self.nodes:
      return self.cmap(self.node_color_map[node])
    else:
      return self.outgroup_color
  
  def get_nodealpha(self, node):
    return self.nodealpha

  def get_nodezorder(self, node):
    if node in self.nodes:
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder

  def get_edgecolor(self, step1, node1, step2, node2):
    if node2 in self.nodes:
      return self.cmap(self.node_color_map[node2])
    else:
      return self.outgroup_color
  
  def get_edgealpha(self, step1, node1, step2, node2):
    return self.edgealpha
  
  def get_edgezorder(self, step1, node1, step2, node2):
    if node2 in self.nodes:
      return self.ingroup_zorder
    else:
      return self.outgroup_zorder
    
  def get_curve(self):
    return self.curve

  def get_facecolor(self):
    return self.facecolor
  
  def get_textcolor(self):
    return self.textcolor
  
  def get_showlegend(self):
    return self.showlegend

# ================
# = Plot helpers =
# ================

# centred on (x, y)
def box_path(x, y, w, h):
  return Path([
    (x - w/2.0, y - h/2.0),
    (x - w/2.0, y + h/2.0),
    (x + w/2.0, y + h/2.0),
    (x + w/2.0, y - h/2.0),
    (x - w/2.0, y - h/2.0),
  ], [
    Path.MOVETO,
    Path.LINETO,
    Path.LINETO,
    Path.LINETO,
    Path.CLOSEPOLY,
  ])

def box_patch(x, y, w, h, color=None, label=None, **kwargs):
  return patches.PathPatch(box_path(x, y, w, h), 
               linewidth=0, edgecolor=None,
               facecolor=color, **kwargs)

# horizontal curve: 0..1, from straight line to hard curve around the midpoint.
def horiz_flow_path(x1, y1, x2, y2, curve):
  dx = x2 - x1
  midpoint = dx * curve
  return Path([
    (x1, y1),
    (x1 + midpoint, y1),
    (x2 - midpoint, y2),
    (x2, y2)
  ], [
    Path.MOVETO,
    Path.CURVE4,
    Path.CURVE4,
    Path.CURVE4,
  ])

def flow_patch(x1, y1, x2, y2, size, color=None, curve=0.7, **kwargs):
  return patches.PathPatch(horiz_flow_path(x1=x1, y1=y1, x2=x2, y2=y2, curve=curve), 
               linewidth=size, edgecolor=color,
               facecolor='none', **kwargs)

# ========
# = Plot =
# ========

class AlluvialFlowDiagram:
  
  # alluvial_flow_layout: an AlluvialFlowLayoutalFlowLayout instance
  def __init__(self, alluvial_flow_layout):
    self.layout = alluvial_flow_layout
  
  # size: plot size as (x, y) tuple
  # style: a DiagramStyle instance
  # credits: copyright string
  def plot(self, size=(16,9), style=SimpleStyle(), credits=None):
    fig = plt.figure(figsize=size, facecolor=style.get_facecolor())
    ax = plt.gca()
    
    # edges
    point_height = size[1] * 72.0
    yrange = self.layout.maxy - self.layout.miny
    
    for step1, step2 in zip(self.layout.steps[:-1], self.layout.steps[1:]):
      for node1 in self.layout.nodes:
        for node2 in self.layout.nodes:
          try:
            size = self.layout.edge_size[step1][node1][node2]
            line_width = (size * (point_height / yrange)) * 0.8  # corresponding width in points
            node_w = self.layout.node_width / 2.0 #* 1.5 # slight overlap
            ax.add_patch(flow_patch(
              self.layout.step_x[step1] + node_w,
              self.layout.edge_node1_y[step1][node1][node2],
              self.layout.step_x[step2] - node_w,
              self.layout.edge_node2_y[step2][node1][node2], 
              size=line_width, 
              color=style.get_edgecolor(step1, node1, step2, node2),
              alpha=style.get_edgealpha(step1, node1, step2, node2),
              zorder=style.get_edgezorder(step1, node1, step2, node2), 
              curve=style.get_curve()
            ))
          except KeyError:
            # TODO.. eww
            pass
    
    # nodes
    for step1, step2 in zip(self.layout.steps[:-1], self.layout.steps[1:]):
      for node in self.layout.nodes:
        try:
          # src port
          x = self.layout.step_x[step1] + self.layout.node_width/2.0
          y1 = self.layout.node1_y1[step1][node]
          y2 = self.layout.node1_y2[step1][node]
          ax.add_patch(box_patch(
              x, (y1+y2)/2.0, 
              w=self.layout.node_width, h=(y2-y1),
              label=node, 
              color=style.get_nodecolor(node), 
              alpha=style.get_nodealpha(node),
              zorder=style.get_nodezorder(node)
            ))

          # dst port
          x = self.layout.step_x[step2] - self.layout.node_width/2.0
          y1 = self.layout.node2_y1[step2][node]
          y2 = self.layout.node2_y2[step2][node]
          ax.add_patch(box_patch(
              x, (y1+y2)/2.0, 
              w=self.layout.node_width, h=(y2-y1),
              label=node, 
              color=style.get_nodecolor(node), 
              alpha=style.get_nodealpha(node),
              zorder=style.get_nodezorder(node)
            ))  
        except KeyError:
          # TODO.. eww
          pass

    # credits
    if credits:
      last_step = self.layout.steps[-1]
      if self.layout.compact:
        # on top of last node
        last_node = self.layout.nodes[-1]
        last_step_maxy = self.layout.node2_y2[last_step][last_node]
        x = self.layout.step_x[last_step]
        y = last_step_maxy + self.layout.node_margin
      else:
        # to the right of last step
        x = self.layout.step_x[last_step] + 0.2
        y = 0
      plt.text(x, y, credits, 
           rotation='vertical', color=style.get_textcolor(),
           horizontalalignment='center', verticalalignment='bottom')
    
    # step labels
    for step in self.layout.steps:
      plt.text(self.layout.step_x[step], 0 - self.layout.node_margin, 
           step, rotation='vertical', color=style.get_textcolor(),
           horizontalalignment='center', verticalalignment='top')

    # node legend
    if style.get_showlegend():
      rev_nodes = self.layout.nodes[::-1] # reverse order
      artists = [box_patch(0, 0, 
                 w=self.layout.node_width, h=self.layout.node_width, 
                 label=node, color=style.get_nodecolor(node), alpha=1)
            for node in rev_nodes]
      leg = plt.legend(artists, rev_nodes, frameon=False)
      for node, txt in zip(rev_nodes, leg.get_texts()):
        txt.set_color(style.get_nodecolor(node))  
  #       txt.set_color(style.get_textcolor())

    # ax.autoscale_view()
    plt.axis('off')
    plt.xlim(self.layout.minx, self.layout.maxx)
    plt.ylim(self.layout.miny, self.layout.maxy)
    
    return fig