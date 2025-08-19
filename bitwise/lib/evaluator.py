# split out from tmodel6 v0.6
# added 'eq', 'notall' validation
# used by rule engine code

from collections import namedtuple, OrderedDict as odict

Condition = namedtuple( 'Condition', ['name_lhs', 'relation', 'name_rhs' ])
#                                    [ String,     String,     Any ]

"""

RelationDef = namedtuple('RelationDef', ['name', 'inverse', symmetric', 'transitive')

RelationDef('eq', 'neq', True, True)
RelationDef('neq', 'eq', True, False)
RelationDef('lt', 'gte', False, True)

... etc.

"""

class EvaluationError(Exception):

	def __init__(self, message='EvaluationError', exception=None):
		super(EvaluationError, self).__init__(self)
		self.valerr_dict = odict()
		self.valerr_dict['message'] = message
		self.valerr_dict['exception'] = exception or 'Unknown Exception'

	def __str__(self):
		return 'EvaluationError( msg = {0}, exception = {1} )'.format(
		                 self.valerr_dict['message'], self.valerr_dict['exception'])

class Evaluation(object):
	"""Static class, global container for evaluations"""

	"""Relations or conditions in the form: ( A, rel, B )"""

	@staticmethod
	def _is( value, *args):
		"""Pythonic 'is' test, arg can be None"""
		return value is args[0]

	@staticmethod
	def isnot( value, *args):
		return value is not args[0]

	@staticmethod
	def equal( value, *args):
		return value == args[0]

	@staticmethod
	def ne( value, *args):
		return value != args[0]

	@staticmethod
	def less_than_eq( value, *args):
		return value <= args[0]

	@staticmethod
	def greater_than_eq( value, *args):
		return value >= args[0]

	@staticmethod
	def less_than( value, *args):
		return value < args[0]

	@staticmethod
	def greater_than( value, *args):
		return value > args[0]

	@staticmethod
	def between_equal( value, *args):
		return args[0] <= value <= args[1]

	@staticmethod
	def between_not_equal( value, *args):
		return args[0] < value < args[1]

	@staticmethod
	def _in( value, vlist ):
		"""Can implement ( A = B OR A = C OR A = D OR ... )"""
		return value in vlist

	@staticmethod
	def notin( value, vlist ):
		"""Can implement DeMorgan form of:

		   NOT ( A = B OR A = C OR A = D OR ... ) =>
		   A != B AND A != C AND A != D ..."""

		return value not in vlist
		
	@staticmethod	
	def xor( value, *args):
		"""Strict typing, args must be boolean xor trouble.
		Needs rehinking, another a unary function masquerading as binary ?
		Needs notxor form ?
		"""
		
		if isinstance(value, bool) and isinstance(args[0], bool):
			return bool(value) ^ bool(args[0])
		else:
			return False

	@staticmethod
	def all_eq( value, vlist ):
		"""All the same value. A unary function masquerading as binary.
		   Implements A = B AND A = C AND A = D ... etc.
		   into a single relationship. Maybe comparing checksums."""

		vlist.append(value)
		return len(set(vlist)) == 1

	@staticmethod
	def notall_eq( value, vlist ):
		"""Not all the same value. A unary function masquerading as binary.
		   Implements ( rather anomalous ) DeMorgan form of:

		   NOT ( A = B AND A = C AND A = D AND ... ) =>
		   A != B OR A != C OR A != D ..."""

		vlist.append(value)
		return len(set(vlist)) != 1

	def typeof( value, *args ):
		"""arg[0] can be a Python type or tuple of types."""

		return isinstance(value, arg[0])

	def not_typeof( value, *args ):
		"""arg[0] can be a Python type or tuple of types."""

		return not isinstance(value, arg[0])

	""" Data Validations """

	@staticmethod
	def empty( value ):
		return len(value)== 0

	@staticmethod
	def not_empty( value ):
		return len(value)>0

	@staticmethod
	def is_alphanumeric( value ):
		return (isinstance(value, basestring) and value.isalnum())

	@staticmethod
	def max_length( value, *args):
		return len(value) <= args[0]

	@staticmethod
	def min_length( value, *args):
		return len(value) >= args[0]

	@staticmethod
	def length( value, *args ):
		"""Kludge to store MySQL-like length info outside of CDef format."""
		return True


class Evaluator(object):
	"""Slightly tricky. Subclass needs to do super(MyEvaluator, self).__init__()
	   if adding app-level evaluations in sublass __init__, via
	   self.evaluations.update(_my_val_dict). Don't use names _e and _evaluations
	   as class variables to avoid shared class name space problems."""

	_e = Evaluation
	_evaluations = { 'is': _e._is,
					 'isnot': _e.isnot,
					 'eq': _e.equal,
					 'ne': _e.ne,
					 'xor': _e.xor,
					 'gte': _e.greater_than_eq,
					 'lte': _e.less_than_eq,
					 'gt': _e.greater_than,
					 'lt': _e.less_than,
					 'btwe': _e.between_equal,
					 'btw': _e.between_not_equal,
					 'in' : _e._in,
					 'notin' : _e.notin,
					 'all_eq' : _e.all_eq,
					 'notall_eq' : _e.notall_eq,
					 'typeof': _e.typeof,
					 'not_typeof': _e.not_typeof,
					 'empty': _e.empty,
					 'notempty': _e.not_empty,
					 'isalpha': _e.is_alphanumeric,
					 'maxlen': _e.max_length,
					 'minlen': _e.min_length,
					 'len': _e.length }

	def __init__(self, custom_evaluations=None):
		self.evaluations =  self._evaluations
		if custom_evaluations:
			self.evaluations.update(custom_evaluations)

	def validate( self, key, value, *args):
		if key in self.evaluations:
			try:
				return self.evaluations[key](value, *args)
			except Exception as e:
				t_msg = 'Bad Arguemnts: Evaluation "{0}" failed using value "{1}" with argument "{2}".' \
				            .format(key, value, args)
				raise EvaluationError(t_msg, e)
		else:
			t_msg = 'Bad Evaluation Name: The evaluation name "{0}" is invalid. '.format(key)
			raise EvaluationError(t_msg)


