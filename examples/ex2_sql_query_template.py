#!/usr/bin/env python
# coding: utf-8
"""
  example 2
  ~~~~~~~~~

  Example alluvial flow visualisation.

  :copyright: 2015 by Martin Dittus, martin@dekstop.de
  :license: AGPL3, see LICENSE.txt for more details
"""

from string import Template

import psycopg2 as pg
import pandas as pd
import pandas.io.sql as psql

from alluvialflow import *
from alluvialflow.sql import *

# =========
# = Model =
# =========

# A parametrised query builder. Generates node-edge flows for user contribution sessions.
#
# The implementation involves two levels of template variable substitution:
# - query fragments (SQL logic), using python string templates: "${my_var}"
# - query parameters (SQL values), using psychopg2 parameter substitution: "%(my_var)s"
class ProjectContributorFlows(FlowDataSource):
    
    # connection: ...
    # first_date, last_date: ISO date strings
    # node_expr: a Case instance that produces a string identifier for each node
    # rank_expr: a Count, CountUnique, or Sum, ... instance that produces a rank order for each node
    # period_interval: a PostgreSQL interval string for step durations
    # period_format: a PostgreSQL date format string for step labels
    def __init__(self, connection, first_date, last_date, 
                 node_expr, rank_expr=CountUnique(Column('uid')),
                 period_interval='1 month', period_format='YYYY-MM'):
        self.connection = connection
        self.expressions = {
            'node_expr': node_expr.sql().replace('%', '%%'),
            'rank_expr': rank_expr.sql().replace('%', '%%'),
        }
        self.params = {
            'first_date': first_date, 
            'last_date': last_date,
            'period_interval': period_interval,
            'period_format': period_format,
        }
    
    # Returns an ordered list of node names, with 'Other' in first place, 
    # and the rest sorted in ascending order of rank.
    def get_nodes(self):
        sql = Template("""
            SELECT 
                ${node_expr} as node,
                ${rank_expr} rank
            FROM user_hmp_session s
            JOIN hot_project_description p ON (s.hot_project=p.hot_project)
            WHERE first_date >= %(first_date)s::date
            AND last_date < %(last_date)s::date
            GROUP BY node
            ORDER BY ${rank_expr} ASC
            """).substitute(self.expressions)
        d = psql.read_sql(sql, self.connection, params=self.params)
#         d.sort('rank', ascending=False)
        nodes = list(d.node.values)
        nodes.remove('Other')
        nodes.insert(0, 'Other')
        return nodes

    # returns a DataFrame[step, node; size]
    def get_sequence(self): 
        sql = Template("""
            SELECT 
                TO_CHAR(first_date, %(period_format)s) as step, 
                ${node_expr} as node,
                count(distinct uid) size
            FROM user_hmp_session s
            JOIN hot_project_description p ON (s.hot_project=p.hot_project)
            WHERE first_date >= %(first_date)s::date
            AND last_date < %(last_date)s::date
            GROUP BY step, node
            """).substitute(self.expressions)
        d = psql.read_sql(sql, self.connection, params=self.params)
        return d.set_index(['step', 'node'])

    # returns a DataFrame[step1, node1, step2, node2; size]
    def get_flows(self): 
        sql = Template("""
            WITH timeline AS (
                SELECT
                    TO_CHAR(first_date, 'YYYY-MM') as step, 
                    ${node_expr} as node,
                    uid
                FROM user_hmp_session s
                JOIN hot_project_description p ON (s.hot_project=p.hot_project)
                WHERE first_date >= %(first_date)s::date
                AND last_date < %(last_date)s::date
                GROUP BY step, node, uid
            )
            SELECT 
                t1.step step1, t1.node node1, 
                t2.step step2, t2.node node2,
                count(distinct t1.uid) size
            FROM (
                SELECT 
                    TO_CHAR(s1,                                %(period_format)s) step1,
                    TO_CHAR(s1 + interval %(period_interval)s, %(period_format)s) step2
                FROM generate_Series(
                    %(first_date)s::date, 
                    %(last_date)s::date - %(period_interval)s::interval, 
                    %(period_interval)s::interval) s1
            ) t
            JOIN timeline t1 ON (step1=t1.step)
            JOIN timeline t2 ON (step2=t2.step)
            WHERE t1.uid=t2.uid
            GROUP BY t1.step, t1.node, t2.step, t2.node
            """).substitute(self.expressions)
        d = psql.read_sql(sql, self.connection, params=self.params)
        return d.set_index(['step1', 'node1', 'step2', 'node2'])

# ========
# = Main =
# ========

if __name__=="__main__":

  connection = pg.connect("dbname=hotosm_history_20150813 user=osm host=localhost")

  first_date = '2013-08-01'
  last_date = '2015-08-01'

  # Note that ordering matters!
  top_node_types = Case(Column('title'),
      WhenAny(Like('%Nepal%'), Like('%Kaligandaki%'), Equal('<strong> IDP informal camps</strong>')).Then('Nepal'),
      WhenAny(Like('%Missing Maps%'), Like('%MissingMaps%')).Then('Missing Maps'),
      WhenAny(Like('%Ebola%')).Then('Ebola'),
      WhenAny(Like('%Central African Republic%'), Like('%CAR%')).Then('CAR'),
      WhenAny(Like('%South Sudan%')).Then('South Sudan'),
      WhenAny(Like('%MapLesotho%')).Then('MapLesotho'),
      Else('Other'))

  data = ProjectContributorFlows(connection, first_date, last_date, top_node_types)
  layout = AlluvialFlowLayout(data, node_margin=50, node_width=0.02, compact=True)
  diagram = AlluvialFlowDiagram(layout)
  fig = diagram.plot(size=(58,18), style=SimpleStyle(showlegend=False), 
                     credits=u'Martin Dittus · @dekstop · September 2015')
  
  plt.savefig("ex2_sql_query_template.pdf", bbox_inches='tight', facecolor=fig.get_facecolor())
  plt.savefig("ex2_sql_query_template.png", bbox_inches='tight', facecolor=fig.get_facecolor())