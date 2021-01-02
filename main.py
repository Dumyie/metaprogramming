import types
from dataclasses import dataclass
from typing import Callable, Any


class RecordMeta(type):
    """
    Meta class to modify the behaviour of the class creation process.
    """

    def __new__(cls, class_name, bases=None, dict=None):
        """
         Implement the class creation by manipulating the attr dictionary
        """
        new_attr = {}
        for key, value in dict.items():
            if not key.startswith("__"):
                new_attr["__" + key + "__field"] = value
                new_attr[key] = property(cls.make_fget(key), cls.make_fset(key))
            else:
                new_attr[key] = value
        return super(RecordMeta, cls).__new__(cls, class_name, bases, new_attr)

    def make_fget(key):
        """
        Defines a field with a label and preconditions
        """

        def fget(self):
            return getattr(self, "__%s" % key)

        return fget

    def make_fset(key):
        """
        Defines a field with a label and preconditions
        """

        def fset(self, value):
            if hasattr(self, key):
                raise AttributeError("Attribute %s is readonly, cannot be set" % (key))
            setattr(self, "__" + key, value)

        return fset

    def __call__(self, *args, **kwargs):
        """This method is called when the constructor of the new class
        is to be used to create an object

        """

        list_attr = [x for x in dir(self) if not x.startswith('_')]
        if len(list_attr) > len(kwargs):
            raise TypeError('Missing attribute')
        if len(list_attr) < len(kwargs):
            raise TypeError('More attributes provided')
        complete_attrib_list = self.get_all_attributes()
        for key, value in kwargs.items():
            if complete_attrib_list[key] is not None:
                if type(value) != complete_attrib_list[key]:
                    raise TypeError("Invalid type for {0} has been passed".format(key))
            get_precondition = getattr(self, "__" + key + "__field").precondition
            if get_precondition is not None:
                if not get_precondition(value):
                    raise TypeError('Precondition for ' + key + ' has been violated.')
        return super().__call__(*args, **kwargs)

    def get_all_attributes(self):
        """
        This method collects all the attributes of an object including inherited attributes
        """
        complete_attrib_list = {}
        list_of_objects = self.mro()
        list_of_objects.reverse()
        for i in range(2, len(list_of_objects)):
            complete_attrib_list.update(list_of_objects[i].__annotations__)
        return complete_attrib_list

    def __repr__(self):
        """
        This method prettifies the printing of objects.
        """
        test = dir(self)
        val = str(self.__name__) + "(\n"
        for k, v in self.__dict__.items():
            if k.endswith("__field"):
                val += "  # " + str(v.label) + "\n  "
                is_string = False
                placeholder = k[0:-7]
                label = placeholder.split('__')[1]
                for y, z in self.__annotations__.items():
                    if y == label:
                        if str(z) == "<class 'str'>":
                            is_string = True
                            break
                if is_string:
                    val += str(label) + "='{" + placeholder + "}'\n"
                else:
                    val += str(label) + "={" + placeholder + "}\n"
        val += ")"
        return val

@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] = None


class Record(metaclass=RecordMeta):
    """
     A simple record object
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        """
        This method overrides the string method and returns a prettified object.
        """
        dict = self.__dict__
        pretty_object = str(self.__class__)
        return pretty_object.format(**dict)

