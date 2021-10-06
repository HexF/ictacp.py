from typing import Any, List, Type, TypeVar

Class = TypeVar('Class')

def all_subclasses(cls:Class) -> List[Class]:
    subclasses = []

    for scls in cls.__subclasses__():
        subclasses.append(scls)
        subclasses.extend(all_subclasses(scls))
    
    return subclasses