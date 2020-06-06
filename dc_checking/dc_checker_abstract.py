from abc import ABC, abstractmethod

class DCChecker(ABC):

    @abstractmethod
    def __init__(self, tn):
        '''
        Takes a temporal network TN as input.
        The temporal network TN cannot be modified by any side effect.
        '''
        pass

    @abstractmethod
    def is_controllable(self):
        '''
        Check DC for the temporal network TN.
        Returns Boolean, Conflict or None.
        '''
        pass
