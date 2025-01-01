
# Generalized Lookup Objects **************************************************#

# Ripped from Python 3 operators, with a functional makeover

def attrgetter(attr, *attrs):
    """
    Return a callable object that fetches the given attribute(s) from its operand.
    After f = attrgetter('name'), the call f(r) returns r.name.
    After g = attrgetter('name', 'date'), the call g(r) returns (r.name, r.date).
    After h = attrgetter('name.first', 'name.last'), the call h(r) returns
    (r.name.first, r.name.last).
    """

    if not attrs:
        if not isinstance(attr, str):
            raise TypeError('attribute name must be a string')
        names = attr.split('.')
        def func(obj):
            for name in names:
                obj = getattr(obj, name)
            return obj
    else:
        _attrs = (attr,) + attrs
        getters = tuple(map(attrgetter, _attrs))
        def func(obj):
            return tuple(getter(obj) for getter in getters)
    return func

def attrsetter(*attrs):
    if len(attrs) == 1:
        _attr = attrs[0]
        def func(obj, value):
            setattr( obj, _attr, value )
    else:
        def func(obj, *values):
            for item, value in zip(items, values):
                setattr( obj, item, value )
    return func


def itemgetter(item, *items):
    """
    Return a callable object that fetches the given item(s) from its operand.
    After f = itemgetter(2), the call f(r) returns r[2].
    After g = itemgetter(2, 5, 3), the call g(r) returns (r[2], r[5], r[3])
    """
    
    if not items:
        def func(obj):
            return obj[item]
    else:
        items = (item,) + items
        def func(obj):
            return tuple(obj[i] for i in items)
    return func


def itemsetter(*items):
    if len(items) == 1:
        item = items[0]
        def func(obj, value):
            obj[item] = value
    else:
        def func(obj, *values):
            for item, value in zip(items, values):
                obj[item] = value
    return func

i_get, i_set = itemgetter, itemsetter   # by index: list, tuple or dict
a_get, a_set = attrgetter, attrsetter 


