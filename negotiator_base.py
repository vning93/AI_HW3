from functools import reduce

class BaseNegotiator:
    # Constructor - Note that you can add other fields here; the only 
    # required fields are self.preferences and self.offer
    def __init__(self):
        self.preferences = []
        self.offer = []
        self.iter_limit = 0
        # Their past offers
        self.their_past_offers = []
        # Their past utilities to offers that I have received
        self.their_past_utilities = []
        # Our utility to their offers
        self.my_past_t_utility = []
        # My past offers sent
        self.my_past_offers = []
        # My utility to my past sent offers
        self.my_past_utilities = []
        # Past results
        self.past_results = []
        self.past_iters = 0
        # Scaling factor for loosening aggression over time
        self.scaling_factor = 0
        self.is_A = False
        self.max_utility = 0
        # Scaling factor for creating new offers. Increases the variation
        # away from my preferences as time goes on
        self.relax_factor = 0
        ## TESTING USE ONLY ##
        self.max_threshold = 0
        self.min_threshold = 0
        self.linear_threshold_decrease_amt = 0
        # self.exponential_threshold_decrease_amt = 0
        self.past_trends = []

    # initialize(self : BaseNegotiator, preferences : list(String), iter_limit : Int)
        # Performs per-round initialization - takes in a list of items, ordered by the item's
        # preferability for this negotiator
        # You can do other work here, but still need to store the preferences 
    def initialize(self, preferences, iter_limit):
        self.preferences = preferences
        self.iter_limit = iter_limit
        self.scaling_factor = 1 / self.iter_limit
        self.max_utility = self.get_utility(self.preferences[:])
        self.relax_factor = len(self.preferences) / iter_limit

    # make_offer(self : BaseNegotiator, offer : list(String)) --> list(String)
        # Given the opposing negotiator's last offer (represented as an ordered list), 
        # return a new offer. If you wish to accept an offer & end negotiations, return the same offer
        # Note: Store a copy of whatever offer you make in self.offer at the end of this method.
    def make_offer(self, offer):
        pass
    # utility(self : BaseNegotiator) --> Float
        # Return the utility given by the last offer - Do not modify this method.
    def utility(self):
        total = len(self.preferences)
        return reduce(lambda points, item: points + ((total / (self.offer.index(item) + 1)) - abs(self.offer.index(item) - self.preferences.index(item))), self.offer, 0)

    # receive_utility(self : BaseNegotiator, utility : Float)
        # Store the utility the other negotiator received from their last offer
    def receive_utility(self, utility):
        self.their_past_utilities.append(utility)

    # receive_results(self : BaseNegotiator, results : (Boolean, Float, Float, Int))
        # Store the results of the last series of negotiation (points won, success, etc.)
    def receive_results(self, results):
        pass
        # self.past_results.append(results)

    def get_utility(self, offer):
        if offer is None:
            return 0
        past_offer = self.offer[:] if self.offer is not None else None
        self.offer = offer
        util = self.utility()
        self.offer = past_offer
        return util