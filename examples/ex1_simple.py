#!/usr/bin/env python
"""
  example 1
  ~~~~~~~~~

  Example alluvial flow visualisation.

  :copyright: 2015 by Martin Dittus, martin@dekstop.de
  :license: AGPL3, see LICENSE.txt for more details
"""

import pandas as pd

from alluvialflow import *

# =========
# = Model =
# =========

class Flows(FlowDataSource):
    
  def get_nodes(self):
    return ['A', 'B', 'C']

  # returns a DataFrame[step, node; size]
  def get_sequence(self): 
    d = pd.DataFrame(columns=['step', 'node', 'size'])
    d = d.append([{'step': 1, 'node': 'A', 'size': 10}])
    d = d.append([{'step': 1, 'node': 'B', 'size': 10}])
    d = d.append([{'step': 1, 'node': 'C', 'size': 10}])
    d = d.append([{'step': 2, 'node': 'A', 'size': 5}])
    d = d.append([{'step': 2, 'node': 'B', 'size': 20}])
    d = d.append([{'step': 2, 'node': 'C', 'size': 5}])
    d = d.append([{'step': 3, 'node': 'A', 'size': 8}])
    d = d.append([{'step': 3, 'node': 'B', 'size': 20}])
    d = d.append([{'step': 3, 'node': 'C', 'size': 2}])
    return d.set_index(['step', 'node'])

  # returns a DataFrame[step1, node1, step2, node2; size]
  def get_flows(self): 
    d = pd.DataFrame(columns=['step1', 'node1', 'step2', 'node2', 'size'])
    d = d.append([{'step1': 1, 'node1': 'A', 'step2': 2, 'node2': 'A', 'size': 5}])
    d = d.append([{'step1': 1, 'node1': 'A', 'step2': 2, 'node2': 'B', 'size': 5}])
    d = d.append([{'step1': 1, 'node1': 'B', 'step2': 2, 'node2': 'B', 'size': 10}])
    d = d.append([{'step1': 1, 'node1': 'C', 'step2': 2, 'node2': 'C', 'size': 5}])
    d = d.append([{'step1': 1, 'node1': 'C', 'step2': 2, 'node2': 'B', 'size': 5}])
    d = d.append([{'step1': 2, 'node1': 'A', 'step2': 3, 'node2': 'A', 'size': 5}])
    d = d.append([{'step1': 2, 'node1': 'B', 'step2': 3, 'node2': 'B', 'size': 20}])
    d = d.append([{'step1': 2, 'node1': 'C', 'step2': 3, 'node2': 'C', 'size': 2}])
    d = d.append([{'step1': 2, 'node1': 'C', 'step2': 3, 'node2': 'A', 'size': 3}])
    return d.set_index(['step1', 'node1', 'step2', 'node2'])

# ========
# = Main =
# ========

if __name__=="__main__":
  data = Flows()
  layout = AlluvialFlowLayout(data)
  diagram = AlluvialFlowDiagram(layout)
  fig = diagram.plot(size=(4,3), style=SimpleStyle())
  
  plt.savefig("ex1_simple.pdf", bbox_inches='tight', facecolor=fig.get_facecolor())
  plt.savefig("ex1_simple.png", bbox_inches='tight', facecolor=fig.get_facecolor())