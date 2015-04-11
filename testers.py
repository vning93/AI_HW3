from negotiator_base import BaseNegotiator
from random import random, shuffle, randint
from functools import reduce

# Example negotiator implementation, which randomly chooses to accept
# an offer or return with a randomized counteroffer.
# Important things to note: We always set self.offer to be equal to whatever
# we eventually pick as our offer. This is necessary for utility computation.
# Second, note that we ensure that we never accept an offer of "None".

## 1a ##

class LinearNegotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.
    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        if self.past_iters == 0:
            self.max_threshold = 0.9 * self.max_utility
            self.min_threshold = 0.1 * self.max_utility
            self.linear_threshold_decrease_amt = (self.max_threshold - self.min_threshold) / self.iter_limit

        if self.past_iters == self.iter_limit:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.min_threshold:
                return offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        if self.should_accept_or_not(offer):
            return offer

        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

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

    def calc_new_offer(self):
        # We will gradually relax on the offers that we are giving.
        ordering = self.preferences[:]
        relax_coefficient = int(self.relax_factor * self.past_iters) + 1
        # relax_coefficient = 1 if relax_coefficient == 0 else relax_coefficient
        right_half = ordering[-relax_coefficient:]
        shuffle(right_half)
        ordering[-relax_coefficient:] = right_half
        util = self.get_utility(ordering)
        return ordering

    def should_accept_or_not(self, offer):
        util = self.get_utility(offer)
        # Accept if offer is better than what we expected
        if util > self.max_threshold:
            return True
        # Adjust the threshold for next time
        else:
            self.max_threshold -= self.linear_threshold_decrease_amt
            return False

## 1b ##

class AsymptoticNegotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.
    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        if self.past_iters == 0:
            self.max_threshold = 0.9 * self.max_utility
            self.min_threshold = 0.1 * self.max_utility

        if self.past_iters == self.iter_limit:
            if self.check_always_accepts_last() and not self.is_A:
                new_offer = self.preferences[:]
                self.offer = new_offer
                return new_offer
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.min_threshold:
                return offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        if self.should_accept_or_not(offer):
            return offer
        elif self.theyre_aggressive():
            # We have a majority of terrible offers from them. Throw them a bone
            ordering = self.preferences[:]
            shuffles = 0
            while True:
                shuffle(ordering)
                shuffles += 1
                t_expected_util = self.their_expected_utility(ordering)
                m_expected_util = self.get_utility(ordering)
                diff = abs(m_expected_util - t_expected_util)
                if (diff <= .3 * abs(m_expected_util) or diff <= .3 * abs(t_expected_util)) and m_expected_util >= t_expected_util and m_expected_util > -len(self.preferences):
                    break
                elif shuffles > 1000 and m_expected_util >= t_expected_util and m_expected_util > len(self.preferences):
                    break
            self.my_past_offers.append(ordering)
            self.my_past_utilities.append(self.get_utility(ordering))
            self.offer = ordering[:]
            return ordering
        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

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

    def calc_new_offer(self):
        # We will gradually relax on the offers that we are giving.
        ordering = self.preferences[:]
        relax_coefficient = int(self.relax_factor * self.past_iters) + 1
        # relax_coefficient = 1 if relax_coefficient == 0 else relax_coefficient
        right_half = ordering[-relax_coefficient:]
        shuffle(right_half)
        ordering[-relax_coefficient:] = right_half
        util = self.get_utility(ordering)
        return ordering

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

    def should_accept_or_not(self, offer):
        util = self.get_utility(offer)
        t_util = self.their_expected_utility(offer)
        diff = abs(util - t_util)
        if (diff <= .35 * abs(util) or diff <= .35 * abs(t_util)) and util >= t_util and util > -len(self.preferences):
            return True

        # Accept if offer is better than what we expected
        if util > self.max_threshold:
            return True
        # Adjust the threshold for next time
        elif self.theyre_aggressive() and util > self.min_threshold:
            return True
        else:
            if self.max_threshold * 1 / (self.past_iters) < self.min_threshold:
                self.max_threshold = self.min_threshold
            else:
                self.max_threshold *= 0.9 * (1 / (self.past_iters))
            return False

    def theyre_aggressive(self):
        if len(self.my_past_t_utility) < .5 * self.iter_limit:
            # Wait till we have some sort of trend data
            return False
        negs = 0
        for util in self.my_past_t_utility:
            negs += 1 if util < 0 else 0
        return negs > .7*len(self.my_past_t_utility)

    def their_expected_utility(self, offer):
        if len(self.their_past_utilities) == 0:
            return 0
        prefs = None
        m = -1
        index = -1
        for i, util in enumerate(self.their_past_utilities):
            if util > m:
                m = util
                index = i
        prefs = self.their_past_offers[index]
        if prefs is not None:
            try:
                total = len(prefs)
                return reduce(lambda points, item: points + ((total / (offer.index(item) + 1)) - abs(offer.index(item) - prefs.index(item))), offer, 0)
            except ValueError as e:
                return 0
        else:
            return 0

## 1c ##

class LinearThenAsymptoticNegotiator(BaseNegotiator):

    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        if self.past_iters == 0:
            self.max_threshold = 0.9 * self.max_utility
            self.min_threshold = 0.1 * self.max_utility
            self.linear_threshold_decrease_amt = (self.max_threshold - self.min_threshold) / self.iter_limit

        if self.past_iters == self.iter_limit:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.min_threshold:
                return offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        if self.should_accept_or_not(offer):
            return offer

        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

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

    def calc_new_offer(self):
        # We will gradually relax on the offers that we are giving.
        ordering = self.preferences[:]
        relax_coefficient = int(self.relax_factor * self.past_iters) + 1
        # relax_coefficient = 1 if relax_coefficient == 0 else relax_coefficient
        right_half = ordering[-relax_coefficient:]
        shuffle(right_half)
        ordering[-relax_coefficient:] = right_half
        util = self.get_utility(ordering)
        return ordering

    def should_accept_or_not(self, offer):
        if self.past_iters <= self.iter_limit / 2:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.max_threshold:
                return True
            # Adjust the threshold for next time
            else:
                self.max_threshold -= self.linear_threshold_decrease_amt
                return False
        else:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.max_threshold:
                return True
            # Adjust the threshold for next time
            else:
                if self.max_threshold * 1 / (self.past_iters*self.past_iters) < self.min_threshold:
                    self.max_threshold = self.min_threshold
                else:
                    self.max_threshold *= 0.9 * (1 / (self.past_iters))
                return False

## 1d ##

class FlexibleNegotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.
    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        if self.past_iters == 0:
            self.max_threshold = 0.9 * self.max_utility
            self.min_threshold = 0.1 * self.max_utility
            self.linear_threshold_decrease_amt = (self.max_threshold - self.min_threshold) / self.iter_limit

        if self.past_iters == self.iter_limit:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.min_threshold:
                return offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        if self.should_accept_or_not(offer):
            return offer

        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

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

    def calc_new_offer(self):
        # We will gradually relax on the offers that we are giving.
        ordering = self.preferences[:]
        relax_coefficient = int(self.relax_factor * self.past_iters) + 1
        # relax_coefficient = 1 if relax_coefficient == 0 else relax_coefficient
        right_half = ordering[-relax_coefficient:]
        shuffle(right_half)
        ordering[-relax_coefficient:] = right_half
        util = self.get_utility(ordering)
        return ordering

    def should_accept_or_not(self, offer):
        if len(self.their_past_utilities) > 1:
            their_current_offer_utility = self.their_past_utilities[len(self.their_past_utilities)-1]
            their_prev_offer_utility = self.their_past_utilities[len(self.their_past_utilities)-2]
            trend = (their_current_offer_utility - their_prev_offer_utility) / their_prev_offer_utility
            self.past_trends.append(trend)
            # print(self.their_past_utilities)
            # print(self.past_trends)
            if abs(self.past_trends[len(self.past_trends)-1]) < 0.99:
                self.max_threshold -= self.max_threshold * self.past_trends[len(self.past_trends)-1]
            util = self.get_utility(offer)
            if util >= self.max_threshold:
                return True
            else:
                return False

## 2 ##

class MeanNegotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.
    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        new_offer = self.preferences[:]
        self.my_past_offers.append(new_offer)
        self.my_past_utilities.append(self.get_utility(new_offer))
        self.offer = new_offer[:]
        return new_offer

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

## 3 ##

class PseudoRandomNegotiator(BaseNegotiator):
    # Override the make_offer method from BaseNegotiator to accept a given offer 5%
    # of the time, and return a random permutation the rest of the time.
    def make_offer(self, offer):
        if offer is None:
            self.is_A = True
            my_offer = self.preferences[:]
            self.my_past_offers.append(my_offer)
            self.my_past_utilities.append(self.get_utility(my_offer))
            self.offer = my_offer
            return my_offer

        if self.past_iters == 0:
            self.max_threshold = 0.9 * self.max_utility
            self.min_threshold = 0.1 * self.max_utility
            self.linear_threshold_decrease_amt = (self.max_threshold - self.min_threshold) / self.iter_limit

        if self.past_iters == self.iter_limit:
            util = self.get_utility(offer)
            # Accept if offer is better than what we expected
            if util > self.min_threshold:
                return offer

        self.their_past_offers.append(offer)
        self.my_past_t_utility.append(self.get_utility(offer))
        self.past_iters += 1

        if self.should_accept_or_not(offer):
            return offer

        else:
            new_offer = self.calc_new_offer()
            self.my_past_offers.append(new_offer)
            self.my_past_utilities.append(self.get_utility(new_offer))
            self.offer = new_offer[:]
            return new_offer

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

    def calc_new_offer(self):
        # We will gradually relax on the offers that we are giving.
        # ordering = self.preferences[:]
        if len(self.my_past_offers) > 0:
            ordering = self.my_past_offers[len(self.my_past_offers)-1][:]
            first_index = randint(0, len(ordering)-1)
            second_index = randint(0, len(ordering)-1)
            first_item = ordering[first_index]
            second_item = ordering[second_index]
            ordering[first_index] = second_item
            ordering[second_index] = first_item
            util = self.get_utility(ordering)
            return ordering
        else:
            util = self.get_utility(self.preferences)
            return self.preferences

    def should_accept_or_not(self, offer):
        if len(self.their_past_utilities) > 1:
            their_current_offer_utility = self.their_past_utilities[len(self.their_past_utilities)-1]
            their_prev_offer_utility = self.their_past_utilities[len(self.their_past_utilities)-2]
            trend = (their_current_offer_utility - their_prev_offer_utility) / their_prev_offer_utility
            self.past_trends.append(trend)
            # print(self.their_past_utilities)
            # print(self.past_trends)
            if abs(self.past_trends[len(self.past_trends)-1]) < 0.99:
                self.max_threshold -= self.max_threshold * self.past_trends[len(self.past_trends)-1]
            util = self.get_utility(offer)
            if util >= self.max_threshold:
                return True
            else:
                return False