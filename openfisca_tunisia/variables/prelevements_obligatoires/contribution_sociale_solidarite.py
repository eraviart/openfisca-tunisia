# -*- coding: utf-8 -*-


from openfisca_tunisia.variables.base import *  # noqa analysis:ignore
from openfisca_tunisia.variables.prelevements_obligatoires.impot_revenu.irpp import calcule_base_imposable


class contribution_sociale_solidarite(Variable):
    value_type = float
    entity = Individu
    label = "Contribution sociale de solidarité"
    definition_period = MONTH

    def formula(individu, period, parameters):
        """
        Art. 53
        Pour les personnes physiques, la différence entre l’impôt sur le revenu déterminé
        sur la base du barème de l’impôt sur le revenu prévu à l’article 44 du code
        de l’impôt sur le revenu des personnes physiques et de l’impôt sur les sociétés,
        en majorant de un point les taux d’imposition applicables aux tranches de revenu
        prévues par ledit barème et l’impôt sur le revenu déterminé sur la base
        dudit barème d’impôt sans la majoration d'un point des taux d’imposition,
        """
        salaire_imposable = individu('salaire_imposable', period = period)
        deduction_famille_annuelle = individu.foyer_fiscal('deduction_famille', period = period.this_year)
        irpp_mensuel_salarie = individu('irpp_mensuel_salarie', period = period)

        non_exonere, revenu_assimile_salaire_apres_abattement = calcule_base_imposable(
            salaire_imposable, deduction_famille_annuelle, period, parameters)
        bareme_irpp = parameters(period.start).impot_revenu.bareme.copy()
        bareme_css = parameters(period.start).prelevements_sociaux.contribution_sociale_solidarite.salarie
        bareme_irpp.add_tax_scale(bareme_css)
        return - irpp_mensuel_salarie - 1.0 * non_exonere * bareme_irpp.calc(
            (12 * revenu_assimile_salaire_apres_abattement - deduction_famille_annuelle)
            ) / 12