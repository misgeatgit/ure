from opencog.atomspace import types, TruthValue
import formulas
from spatiotemporal import temporal_formulas
from opencog.atomspace import get_type_name
from pln.rule import Rule

'''
go_shopping_1 contains get_cool_stuff_1
go_shopping_2 contains get_cool_stuff_2

go_shopping contains get_cool_stuff

how to do that kind of reasoning?
'''


class TemporalRule(Rule):
    """
    Base class for temporal Rules. They evaluate a time relation such
    as BeforeLink, based on some AtTimeLinks.
    """

    # TODO it can't use the formulas directly. They require some
    # preprocessing to create a temporal-distribution-dictionary
    # out of some AtTimeLinks. And how to find all of the AtTimeLinks
    # for an Atom?
    # Easy way: the inputs here will eventually find every element of
    # A and B, so just recalculate every time.
    def __init__(self, chainer, link_type, formula):
        A = chainer.new_variable()
        B = chainer.new_variable()
        ta = chainer.new_variable()
        tb = chainer.new_variable()

        Rule.__init__(self,
                      formula=formula,
                      outputs=[chainer.link(link_type, [A, B])],
                      inputs=[chainer.link(types.AtTimeLink, [ta, A]),
                              chainer.link(types.AtTimeLink, [tb, B])])

        self.name = get_type_name(link_type) + 'EvaluationRule'

        self.probabilistic_inputs = False

    def temporal_compute(self, input_tuples):
        links_a = []
        links_b = []
        for (link_a, link_b) in input_tuples:
            links_a.append(link_a)
            links_b.append(link_b)

        dist1 = make_distribution(links_a)
        dist2 = make_distribution(links_b)

        strength = self.formula(dist1, dist2)
        
        # I'm not sure what to choose for this
        count = len(input_tuples)
        tv = TruthValue(strength, count)
        
        # Todo: The variable 'target' is not defined, so this doesn't work
        return [(target, tv)]


def make_distribution(time_links):
    dist = {}
    for link in time_links:
        time = get_integer(link.out[0])
        fuzzy_tv = link.tv.mean
        dist[time] = fuzzy_tv
    
    return dist


def get_integer(time_node):
    return int(time_node.name)    


class TemporalTransitivityRule(Rule):
    # Todo:
    # Hackily infer transitive temporal relationships using the
    # deduction formula
    # This Rule is important but the TV formula is wrong
    def __init__(self,
                 chainer,
                 link_type,
                 formula=formulas.deductionIndependenceBasedFormula):
        A = chainer.new_variable()
        B = chainer.new_variable()
        C = chainer.new_variable()

        Rule.__init__(self,
                      formula=formula,
                      outputs=[chainer.link(link_type, [A, C])],
                      inputs=[chainer.link(link_type, [A, B]),
                              chainer.link(link_type, [B, C])])

        self.name = get_type_name(link_type) + 'TransitivityRule'

        self.probabilistic_inputs = False

# there should also be temporal modus ponens too (to predict that
# something will happen)


class PredictiveAttractionRule(Rule):
    def __init__(self, chainer):
        A = chainer.new_variable()
        B = chainer.new_variable()
        Rule.__init__(self,
                      formula=formulas.identityFormula,
                      outputs=[chainer.link(types.PredictiveAttractionLink,
                                            [A, B])],
                      inputs=[chainer.link(types.AndLink,
                                           [chainer.link(types.AttractionLink,
                                                         [A, B]),
                                            chainer.link(types.BeforeLink,
                                                         [A, B])])])


class TemporalCompositionRule(Rule):
    """
    Rule class for the composition operation in the Allen Interval Algebra
    Two link types are given as input and one or more output relations
    are generated by looking them up in a composition table currently
    located at opencog/python/pln/examples/temporal/composition_table.txt
    taken from http://www.ics.uci.edu/~alspaugh/cls/shr/allen.html
    """
    def __init__(self, chainer, link_type1, link_type2, *args):
        A = chainer.new_variable()
        B = chainer.new_variable()
        # compositions can encompass either 1, 3, 5, 9 or 13 relations
        outputs = []
        for output_type in args:
            outputs.append(chainer.link(output_type, [A, B]))
        Rule.__init__(self,
                      name="TemporalCompositionRule ({0}).({1}) = ({2})"
                      .format(
                          get_type_name(link_type1),
                          get_type_name(link_type2),
                          " ".join([get_type_name(output_type)
                                    for output_type in args])),
                      # a formula is still needed
                      formula=None,
                      inputs=[chainer.link(link_type1, [A, B]),
                              chainer.link(link_type2, [A, B])],
                      outputs=outputs)


def create_composition_rules(chainer, composition_table):
    rules = []

    # maps Allen relation to its proper link type in OpenCog
    link_types = {
        "P": types.AfterLink,
        "p": types.BeforeLink,
        "D": types.ContainsLink,
        "d": types.DuringLink,
        "e": types.EqualsLink,
        "F": types.FinishedByLink,
        "f": types.FinishesLink,
        "M": types.MetByLink,
        "m": types.MeetsLink,
        "O": types.OverlappedByLink,
        "o": types.OverlapsLink,
        "S": types.StartedByLink,
        "s": types.StartsLink}

    columns = ["p", "m", "o", "F", "D", "s", "e", "S", "d", "f", "O", "M", "P"]

    with open(composition_table, "r") as f:
        # strips "\n" and header line; iterates over file
        for line in [line.strip() for line in f.readlines()[1:]]:
            # relations are located in the first column
            relation1 = line.split("\t")[0]
            for i in range(1,14):
                relation2 = columns[i-1]
                output = line.split("\t")[i].strip("()")
                print("relation 1: {0}, relation 2: {1}, output: {2}"
                      .format(relation1, relation2, output))
                rules.append(TemporalCompositionRule(
                    chainer,
                    link_types[relation1],
                    link_types[relation2],
                    # output can be more than one relation
                    *[link_types[relation] for relation in list(output)]))
    return rules

    # excerpt from a comment made by Ben in a discussion on temporal inference:
    # rules not only depend on link type, but also on type of first target
    # custom link types: DuringLink $x $y
    # or: EvaluationLink PredicateNode "During" ListLink $x $y
    # rule:
    # Implication
    # ANDLink
    #   Evaluation Precedes $x $y
    #   Evaluation During $x $z
    # ANDLink
    #   Evaluation Overlaps $x $z
    #   ExecutionLink
    #       GroundedSchemaNode IntervalCompositionRule
    #       ListLink
    #           Evaluation Precedes $x $y
    #           Evaluation During $x $z


def create_temporal_rules(chainer):
    rules = []
    combinations = [
        (types.BeforeLink, temporal_formulas.beforeFormula),
        (types.OverlapsLink, temporal_formulas.overlapsFormula),
        (types.DuringLink, temporal_formulas.duringFormula),
        (types.MeetsLink, temporal_formulas.meetsFormula),
        (types.StartsLink, temporal_formulas.startsFormula),
        (types.FinishesLink, temporal_formulas.finishesFormula),
        (types.EqualsLink, temporal_formulas.equalsFormula)]

    for (type, formula) in combinations:
        rules.append(TemporalRule(chainer, type, formula))

    for type, _ in combinations:
        # use temporal links to evaluate more temporal links
        rules.append(TemporalTransitivityRule(chainer, type))

    # Use the wrong formula to predict events
    #rules.append(ModusPonensRule(chainer, types.BeforeLink))

    #rules.append(PredictiveAttractionRule(chainer))

    return rules 

    # There are lots of reverse links, (like (After x y) = (Before y x)
    # It seems like those would just make it dumber though?