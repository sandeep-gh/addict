import copy

# don't want namedtuple to dictionified
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def isnamedtupleinstance(x):
    t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple:
        return False
    f = getattr(t, '_fields', None)
    if not isinstance(f, tuple):
        return False
    return all(type(n) == str for n in f)


def get_changed_history_list(arritems, tprefix="", path_guards=None):
    for idx, aitem in enumerate(arritems):
        if isinstance(aitem, Dict):
            yield from aitem.get_changed_history(tprefix+f"/{idx}", path_guards = path_guards
                                                 )
        elif isinstance(aitem, list):
            yield from get_changed_history_list(aitem, tprefix+f"/{idx}", path_guards = path_guards)
        else:
            # list are by default tracked for changes
            yield tprefix + f"/{idx}"


def clear_changed_history_list(arritems):
    for idx, aitem in enumerate(arritems):
        if isinstance(aitem, Dict):
            aitem.clear_changed_history()
        elif isinstance(aitem, list):
            clear_changed_history_list(aitem)
        else:
            pass


class Dict(dict):
    def __init__(__self, *args, **kwargs):
        object.__setattr__(__self, '__parent', kwargs.pop('__parent', None))
        object.__setattr__(__self, '__key', kwargs.pop('__key', None))
        object.__setattr__(__self, '__frozen', False)
        object.__setattr__(__self, '__track_changes',
                           kwargs.pop('track_changes', False))
        if object.__getattribute__(__self, '__track_changes'):
            object.__setattr__(__self, '__tracker', set())
        for arg in args:
            if not arg:
                continue
            elif isinstance(arg, dict):
                for key, val in arg.items():
                    __self[key] = __self._hook(val)
            elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
                __self[arg[0]] = __self._hook(arg[1])
            else:
                for key, val in iter(arg):
                    __self[key] = __self._hook(val)

        for key, val in kwargs.items():
            __self[key] = __self._hook(val)

    def __setattr__(self, name, value):
        if hasattr(self.__class__, name):
            raise AttributeError("'Dict' object attribute "
                                 "'{0}' is read-only".format(name))
        else:
            self[name] = value

    def __setitem__(self, name, value):
        isFrozen = (hasattr(self, '__frozen') and
                    object.__getattribute__(self, '__frozen'))
        if isFrozen and name not in super(Dict, self).keys():
            raise KeyError(name)

        # import traceback
        # import sys
        # traceback.print_stack(file=sys.stdout)
        # pickle.load calls setitem with out calling init 
        try:
            if object.__getattribute__(self, '__track_changes'):
                object.__getattribute__(self, '__tracker').add((name))
        except:
            pass
        
        super(Dict, self).__setitem__(name, value)
        try:
            p = object.__getattribute__(self, '__parent')
            key = object.__getattribute__(self, '__key')
        except AttributeError:
            p = None
            key = None
        if p is not None:
            p[key] = self
            object.__delattr__(self, '__parent')
            object.__delattr__(self, '__key')

    def __add__(self, other):
        if not self.keys():
            return other
        else:
            self_type = type(self).__name__
            other_type = type(other).__name__
            msg = "unsupported operand type(s) for +: '{}' and '{}'"
            raise TypeError(msg.format(self_type, other_type))

    @classmethod
    def _hook(cls, item):
        if isinstance(item, dict):
            return cls(item)
        elif isinstance(item, (list, tuple)) and not isnamedtupleinstance(item):
            return type(item)(cls._hook(elem) for elem in item)
        return item

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __missing__(self, name):
        if object.__getattribute__(self, '__frozen'):
            raise KeyError(name)
        return self.__class__(__parent=self, __key=name, track_changes=object.__getattribute__(self, '__track_changes'))

    def __delattr__(self, name):
        del self[name]

    def to_dict(self):
        base = {}
        for key, value in self.items():
            if isinstance(value, type(self)):
                base[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                base[key] = type(value)(
                    item.to_dict() if isinstance(item, type(self)) else
                    item for item in value)
            else:
                base[key] = value
        return base

    def copy(self):
        return copy.copy(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    def __deepcopy__(self, memo):
        other = self.__class__()
        memo[id(self)] = other
        for key, value in self.items():
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def update(self, *args, **kwargs):
        other = {}
        if args:
            if len(args) > 1:
                raise TypeError()
            other.update(args[0])
        other.update(kwargs)
        for k, v in other.items():
            if ((k not in self) or
                (not isinstance(self[k], dict)) or
                    (not isinstance(v, dict))):
                self[k] = v
            else:
                self[k].update(v)

    def __getnewargs__(self):
        return tuple(self.items())

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    def __or__(self, other):
        if not isinstance(other, (Dict, dict)):
            return NotImplemented
        new = Dict(self)
        new.update(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, (Dict, dict)):
            return NotImplemented
        new = Dict(other)
        new.update(self)
        return new

    def __ior__(self, other):
        self.update(other)
        return self

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        else:
            self[key] = default
            return default

    def freeze(self, shouldFreeze=True):
        object.__setattr__(self, '__frozen', shouldFreeze)
        for key, val in self.items():
            if isinstance(val, Dict):
                val.freeze(shouldFreeze)

    def unfreeze(self):
        self.freeze(False)

    def get_changed_history(self, prefix="", path_guards = None):
        if super().__getattribute__("__track_changes") == False:
            return

        for key, value in self.items():
            if isinstance(value, type(self)):
                try:
                    if not path_guards or prefix+"/" + str(key) not in path_guards:
                        yield from value.get_changed_history(prefix+"/" + str(key), path_guards=path_guards)
                except Exception as e:
                    logger.debug(f"concat error {self.items} {self}")
                    logger.debug(f"concat error {self}")
                    raise e
            elif isinstance(value, list):
                yield from get_changed_history_list(value, prefix+"/" + str(key), path_guards=path_guards)
            else:
                if key in super().__getattribute__("__tracker"):
                    yield prefix + "/" + key

    def clear_changed_history(self):
        if super().__getitem__("__track_changes") == False:
            print("tracker not enabled")
            return
        for key, value in self.items():
            if isinstance(value, type(self)):
                try:
                    value.clear_changed_history()
                except Exception as e:
                    print("no tracker found for ", value, value.items())
                    raise e
            elif isinstance(value, list):
                clear_changed_history_list(value)

        super().__getattribute__("__tracker").clear()

    def set_tracker(self, track_changes=False):
        """
        pickle/unpickle forgets about trackers and frozenness
        """

        for key, value in self.items():
            if isinstance(value, type(self)):
                value.set_tracker(self)
        object.__setattr__(self, '__frozen',
                           False)
        object.__setattr__(self, '__track_changes',
                           track_changes)
        if track_changes:
            object.__setattr__(self, '__tracker', set())


def walker(adict, ppath="", guards=None):
    for key, value in adict.items():
        try:
            if guards:
                if f"{ppath}/{key}" in guards:
                    yield (f"{ppath}/{key}", value)
                    continue  # stop at the guard
            if isinstance(value, Dict):
                yield from walker(value, ppath + f"/{key}", guards=guards)
            else:
                yield (f"{ppath}/{key}", value)
                pass
        except Exception as e:
            print(f"in walker exception {ppath} {key} {e}")
            raise ValueError
