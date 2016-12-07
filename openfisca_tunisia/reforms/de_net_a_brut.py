# -*- coding: utf-8 -*-

from __future__ import division

from openfisca_core import columns
from openfisca_core.reforms import Reform
from openfisca_core.variables import Variable

try:
    from scipy.optimize import fsolve
except ImportError:
    fsolve = None

from .. import entities


def calculate_net_from(salaire_imposable, simulation, period, requested_variable_names):
    # We're not wanting to calculate salaire_imposable again, but instead manually set it as an input variable
    # To avoid possible conflicts, remove its function
    simulation.holder_by_name['salaire_imposable'].formula.function = None
    simulation.get_or_new_holder('salaire_imposable').array = salaire_imposable

    # Work in isolation
    temp_simulation = simulation.clone()

    # Calculated variable holders might contain undesired cache
    # (their entity.simulation points to the original simulation above)
    for name in requested_variable_names:
        del temp_simulation.holder_by_name[name]

    # Force recomputing of salaire_net
    del temp_simulation.holder_by_name['salaire_net_a_payer']

    net = temp_simulation.calculate('salaire_net_a_payer', period)[0]

    return net


class salaire_imposable(Variable):
    column = columns.FloatCol
    entity = entities.Individu
    label = u"Salaire imposable"

    def function(self, simulation, period):
        # Calcule le salaire brut à partir du salaire net par inversion numérique.
        net = simulation.get_array('salaire_net_a_payer', period)
        assert net is not None
        simulation = self.holder.entity.simulation

        # List of variables already calculated. We will need it to remove their holders,
        # that might contain undesired cache
        requested_variable_names = simulation.requested_periods_by_variable_name.keys()
        if requested_variable_names:
            requested_variable_names.remove(u'salaire_imposable')
        # Clean 'requested_periods_by_variable_name', that is used by -core to check for computation cycles.
        # This variable, salaire_imposable, might have been called from variable X,
        # that will be calculated again in our iterations to compute the salaire_net requested
        # as an input variable, hence producing a cycle error
        simulation.requested_periods_by_variable_name = dict()

        def solve_func(net):
            def innerfunc(essai):
                return calculate_net_from(essai, simulation, period, requested_variable_names) - net
            return innerfunc

        brut_calcule = \
            fsolve(
                solve_func(net),
                net * 1.25,  # on entend souvent parler cette méthode...
                xtol = 1 / 100  # précision
                )

        return period, brut_calcule


class de_net_a_brut(Reform):
    name = u'Inversion du calcul brut -> net'

    def apply(self):
        self.update_variable(salaire_imposable)
