"""
  alluvialflow.sql
  ~~~~~~~~~~~~~~~~

  SQL query fragments for flow models.

  :copyright: 2015 by Martin Dittus, martin@dekstop.de
  :license: AGPL3, see LICENSE.txt for more details
"""

import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.schema import Column, Table
import sqlalchemy.sql.expression as sax
import sqlalchemy.sql.functions as saf

# ===========
# = Helpers =
# ===========

def compile_expr(expr, engine=None):
#   if hasattr(expr, '__iter__'):
  if type(expr) is list:
    return [compile_expr(v, engine) for v in expr]
  return expr.compile(bind=engine, compile_kwargs={"literal_binds": True})

def sql(expr):
#   if hasattr(expr, '__iter__'):
  if type(expr) is list:
    return ' '.join([sql(v) for v in expr])
  return str(expr)

# =======================
# = SQL query fragments =
# =======================

#
# For node expressions
#

class Case:
  class WhenExpr:
    def __init__(self, when_expr, value):
      self.when_expr = when_expr
      self.value = value

    def _visit(self, expr):
      return [
        text('  WHEN'),
        self.when_expr._visit(expr), 
        text('THEN :value\n').bindparams(value=self.value)]

  def __init__(self, expr, *when_expr_list):
    self.expr = expr
    self.when_expr_list = when_expr_list

  def sql(self):
    return sql(compile_expr([
        text('CASE\n'),
        [e._visit(self.expr) for e in self.when_expr_list],
        text('END\n'),
      ]))

class WhenAny:
  def __init__(self, *expr_list):
    self.expr_list = expr_list

  def _visit(self, expr):
    return sax.or_(*[e._visit(expr) for e in self.expr_list])
  
  def Then(self, value):
    return Case.WhenExpr(self, value)

class Like:
  def __init__(self, value):
    self.value = value

  def _visit(self, expr):
    return expr.like(self.value)

class Equal:
  def __init__(self, value):
    self.value = value

  def _visit(self, expr):
    return expr == self.value

class Else:
  def __init__(self, value):
    self.value = value

  def _visit(self, expr):
    return text('ELSE :value\n').bindparams(value=self.value)

#
# For rank expressions
#

class Sum:
  def __init__(self, expr):
    self.expr = expr

  def sql(self):
    return sql(compile_expr([
        saf.sum(self.expr)
      ]))

class Count:
  def __init__(self, expr):
    self.expr = expr

  def sql(self):
    return sql(compile_expr([
        saf.count(self.expr)
      ]))

class CountUnique:
  def __init__(self, expr):
    self.expr = expr

  def sql(self):
    return sql(compile_expr([
        saf.count(sax.distinct(self.expr))
      ]))

class Min:
  def __init__(self, expr):
    self.expr = expr

  def sql(self):
    return sql(compile_expr([
        saf.min(self.expr)
      ]))

class Max:
  def __init__(self, expr):
    self.expr = expr

  def sql(self):
    return sql(compile_expr([
        saf.max(self.expr)
      ]))