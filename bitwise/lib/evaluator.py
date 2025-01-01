# split out from tmodel6 v0.6
# added 'eq' validatiom
# used by rule engine code

from collections import namedtuple, OrderedDict as odict

Condition = namedtuple( 'Condition', ['name_lhs', 'relation', 'name_rhs' ])
#                                    [ String,     String,     Any ]  

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
	
	@staticmethod 
	def _is( value, *args):
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
	def xor( value, *args):
		"""Strict typing, args must be boolean xor trouble"""
		if isinstance(value, bool) and isinstance(args[0], bool):
			return bool(value) ^ bool(args[0])
		else:
			return False
	
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
		return value in vlist
		
	@staticmethod 		
	def notin( value, vlist ):
		return value not in vlist
		
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
		"""Kludge to store optional length info outside of CDef format."""
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
			

