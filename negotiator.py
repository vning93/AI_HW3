from negotiator_base import BaseNegotiator
from random import random, shuffle
from functools import reduce

# Example negotiator implementation, which randomly chooses to accept
# an offer or return with a randomized counteroffer.
# Important things to note: We always set self.offer to be equal to whatever
# we eventually pick as our offer. This is necessary for utility computation.
# Second, note that we ensure that we never accept an offer of "None".
class Negotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.   
    def make_offer(self, offer):
        if random() < 0.05 and offer:
            # Very important - we save the offer we're going to return as self.offer
            self.offer = offer[:]
            return offer
        else:
            ordering = self.preferences[:]
            shuffle(ordering)
            self.offer = ordering[:]
            return self.offer

class BANegotiator(BaseNegotiator):

    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            # self.my_past_t_utility.append(self.get_utility(offer))
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        # If self.past_iters == self.iter_limit here then it is the last turn.
        # Look at past results and see if the other robot has always accepted on last turn.
        # If so then send them our preferences and hope they are dumb
        if self.past_iters == self.iter_limit:
            # If we are B then we have the chance to send the last offer
            if self.check_always_accepts_last() and not self.is_A:
                new_offer = self.preferences[:]
                self.offer = new_offer
                return new_offer
            elif not self.is_A:
                new_offer = self.calc_friendly_offer()
                util = self.get_utility(new_offer)
                if self.get_utility(offer) > util:
                    self.offer = offer
                else:
                    self.offer = new_offer
                return self.offer[:]
            else:
                # We are A on last turn
                if self.get_utility(offer) > 0:
                    self.offer = offer
                    return offer

        # slope, y_int = self.calc_regression()
        # r2 = self.calc_r_squared(slope, y_int)
        # if r2 >= .4 and len(self.their_past_utilities) >= (.3 * self.iter_limit):
        #     # Here we have a somewhat correlated regression and thus can
        #     # see a general trend given by the slope
        #     if slope >= -2:
        #         # This guy is being a stickler. Only accept if its also really good for me
        #         if self.should_accept_offer_aggressive(offer):
        #             return offer
        #         # Here we should make a smarter counter offer that improves our utility while
        #         # remaining relatively similar to theirs
        #     else:
        #         # Lowering standards. Be aggressive at first but then loosen grip
        #         if self.past_iters <= .5 * self.iter_limit and self.should_accept_offer_aggressive(offer):
        #             return offer
        #         elif self.should_accept_offer_casual(offer):
        #             return offer

        # If we do not have a trend line then accept at a semi-aggressive rate
        if self.should_accept_offer_casual(offer):
            self.offer = offer[:]
            self.my_past_offers.append(offer)
            self.my_past_utilities.append(self.get_utility(offer))
            return offer
        # elif self.hes_aggressive():
        #     new_offer = self.calc_counter_aggressive_offer()
        #     util = self.get_utility(new_offer)
        #     if self.get_utility(offer) > util:
        #         self.offer = offer
        #     else:
        #         self.offer = new_offer
        #     self.my_past_offers.append(self.offer[:])
        #     self.my_past_utilities.append(self.get_utility(self.offer[:]))
        #     return self.offer[:]
        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

    def hes_aggressive(self):
        if len(self.my_past_t_utility) == 0:
            return False
        bad_utils = 0
        for util in self.my_past_t_utility:
            bad_utils += 1 if util < 0 else 0
        return (bad_utils / len(self.my_past_t_utility)) >= .75

    def calc_counter_aggressive_offer(self):
        ind = -1
        m = 0
        for i in range(len(self.my_past_t_utility)):
            if self.my_past_t_utility[i] > m:
                m = self.my_past_t_utility[i]
                ind = i
        best_offer = self.their_past_offers[ind][:]
        fav_index = best_offer.index(self.preferences[0])
        # Bubble our favorite item up to the front
        while fav_index > 0:
            temp = best_offer[fav_index-1]
            best_offer[fav_index-1] = best_offer[fav_index]
            best_offer[fav_index] = temp
            fav_index -= 1

        snd_fav_index = best_offer.index(self.preferences[1])
        # Bubble second favorite up to the top

        while snd_fav_index > 1:
            temp = best_offer[snd_fav_index-1]
            best_offer[snd_fav_index-1] = best_offer[snd_fav_index]
            best_offer[snd_fav_index] = temp
            snd_fav_index -= 1

        return best_offer

    def calc_friendly_offer(self):
        ind = -1
        m = 0
        for i in range(len(self.my_past_t_utility)):
            if self.my_past_t_utility[i] > m:
                m = self.my_past_t_utility[i]
                ind = i
        best_offer = self.their_past_offers[ind][:]
        fav_index = best_offer.index(self.preferences[0])
        # Bubble our favorite item up to the front
        while fav_index > 0:
            temp = best_offer[fav_index-1]
            best_offer[fav_index-1] = best_offer[fav_index]
            best_offer[fav_index] = temp
            fav_index -= 1
        return best_offer

    def check_always_accepts_last(self):
        # If there was ever an instance where they were A and they did not accept on the
        # the last turn then return False.
        # NOTE: The self.iter_limit -1 is there because results reports iter_limit - 1 when a
        # bot accepts an offer on the last turn.
        if len(self.past_results) == 0:
            return False
        for item in self.past_results:
            if item['was_A'] == False and item['result'] == False and item['iters'] == self.iter_limit-1:
                return False
        return True

    def calc_new_offer(self):
        offer = self.preferences[:]
        still_looking = True
        while still_looking:
            shuffle(offer)
            util = self.get_utility(offer)
            if util > .4 * self.max_utility:
                still_looking = False
        return offer

    def calc_new_offer2(self):
        # We will gradually relax on the offers that we are giving.
        ordering = self.preferences[:]
        relax_coefficient = int(self.relax_factor * self.past_iters) + 1
        # relax_coefficient = 1 if relax_coefficient == 0 else relax_coefficient
        right_half = ordering[-relax_coefficient:]
        shuffle(right_half)
        ordering[-relax_coefficient:] = right_half
        util = self.get_utility(ordering)
        return ordering

    def calc_regression(self):
        mean_y = reduce(lambda tot, elem: tot + elem, self.their_past_utilities, 0) / len(self.their_past_utilities)
        mean_x = reduce(lambda tot, elem: tot + elem, [i for i in range(len(self.their_past_utilities))], 0) / len(self.their_past_utilities)
        numerator = 0
        denom = 0
        y_int = self.their_past_utilities[0] if len(self.their_past_utilities) else 0
        for i in range(len(self.their_past_utilities)):
            n = (i-mean_x) * (self.their_past_utilities[i]-mean_y)
            d = (i-mean_x) ** 2
            numerator += n
            denom += d
        denom = 1 if denom == 0 else denom
        slope = numerator / denom
        return (slope, y_int)

    def calc_regression_expectation(self):
        slope, y_int = self.calc_regression()
        if len(self.their_past_utilities):
            next_utility = self.their_past_utilities[0] + slope*len(self.their_past_utilities)
            return next_utility
        return None

    def calc_r_squared(self, slope=None, y_int=None):
        slope, y_int = self.calc_regression() if slope is None or y_int is None else (slope, y_int)
        sum_x = sum([i for i in range(len(self.their_past_utilities))])
        sum_x2 = sum([i**2 for i in range(len(self.their_past_utilities))])
        sum_y = sum([i for i in self.their_past_utilities])
        sum_y2 = sum([i**2 for i in self.their_past_utilities])
        zipped = zip(self.their_past_utilities, [i for i in range(len(self.their_past_utilities))])
        sum_xy = sum([util[0] * util[1] for util in zipped])
        nom = (len(self.their_past_utilities)*sum_xy) - (sum_x * sum_y)
        denom1 = (len(self.their_past_utilities)*sum_x2 - (sum_x**2))**0.5
        inter = len(self.their_past_utilities) * sum_y2 - (sum_y**2)
        inter = 0 if inter < 0 else inter
        denom2 = inter**0.5
        denom = denom1*denom2
        denom = 1 if denom == 0 else denom
        r = nom / denom
        r2 = r*r
        return r2

    def should_accept_offer_casual(self, offer):
        utility_to_me = self.get_utility(offer)
        percentage = 1 - (self.past_iters * self.scaling_factor)
        if utility_to_me >= (self.max_utility * percentage):
            return True
        return False

    def should_accept_offer_aggressive(self, offer):
        utility_to_me = self.get_utility(offer)
        percentage = 1 - (self.past_iters * (self.scaling_factor / 2))
        if utility_to_me >= (self.max_utility * percentage):
            return True
        return False

    def receive_results(self, results):
        res = {}
        res['result'] = results[0]
        res['my_points'] = results[1] if self.is_A else results[2]
        res['their_points'] = results[2] if self.is_A else results[1]
        res['was_A'] = self.is_A
        res['did_win'] = res['my_points'] > res['their_points']
        res['iters'] = results[3]
        self.past_iters = 0
        self.past_results.append(res)