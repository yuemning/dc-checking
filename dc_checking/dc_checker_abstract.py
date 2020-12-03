from abc import ABC, abstractmethod

class DCChecker(ABC):

    @abstractmethod
    def __init__(self, tn):
        """Initializes Dynamic Controllability Checker class.

        Args:
            tn: Temporal network to be checked.

        The temporal network TN cannot be modified by any side effect.
        """

        pass

    @abstractmethod
    def is_controllable(self):
        """Check DC for the temporal network TN.

        Returns:
            controllable: A boolean representing if the network is controllable
            conflict: Temporal conflict if uncontrollable, or None
        """

        pass
