from dc_checking.temporal_network import SimpleTemporalConstraint, SimpleContingentTemporalConstraint, TemporalNetwork
from random import randint
from dc_checking.dc_milp import DCCheckerMILP
from dc_checking.dc_be import DCCheckerBE
import timeit

def generate_network(num_cont=5):
    """Generate a somewhat randomized network.

    Args:
        num_cont: Number of contingent links
    """

    network = TemporalNetwork()

    # Add contingent links
    for i in range(num_cont):
        from_event = 'cont:start:' + str(i)
        to_event = 'cont:end:' + str(i)
        network.add_constraint(SimpleContingentTemporalConstraint(from_event, to_event, 0, randint(1, 4), 'cont:' + str(i)))

    # Add requirement links
    idx = 0
    for i in range(num_cont):
        for j in range(num_cont):
            for k in range(2):
                for l in range(2):
                    if i < j and randint(0, 4 * num_cont - 1) == 0:
                        if k == 0:
                            from_event = 'cont:start:' + str(i)
                        else:
                            from_event = 'cont:end:' + str(i)
                        if l == 0:
                            to_event = 'cont:start:' + str(j)
                        else:
                            to_event = 'cont:end:' + str(j)
                        network.add_constraint(SimpleTemporalConstraint(from_event, to_event, 0, randint(1, 4), 'req:' + str(idx)))
                        idx += 1

    return network


def run_random_stnus(num_trials, num_cont=5):
    """Generate NUM_TRIALS networks and run it on BE and MILP checking."""

    # Generate networks
    networks = []
    for i in range(num_trials):
        networks.append(generate_network(num_cont))

    # Run BE algorithm
    start = timeit.default_timer()

    for network in networks:
        checker = DCCheckerBE(network)
        controllable, conflict = checker.is_controllable()
        # print(controllable, conflict)

    stop = timeit.default_timer()
    print('BE Time: ', stop - start)

    # Run MILP algorithm
    start = timeit.default_timer()

    for network in networks:
        checker = DCCheckerMILP(network)
        controllable, _ = checker.is_controllable()
        # print(controllable)

    stop = timeit.default_timer()
    print('MILP Time: ', stop - start)


if __name__ == '__main__':
    run_random_stnus(3, 10)
