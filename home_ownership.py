import math
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

"""
Sample Modeling Data Structure

d = {
'home_price' : 100000.0,
'down_payment' : 0.2,
'maintenance': 0.01,
'home_owners_insurance': 0.0056,
'mortgage_term' : 15,
'mortgage_rate' : 0.037,
'property_tax' : 0.017,
'marginal_tax_rate' : 0.36,
'stock_market' : 0.06,
'house_appreciation' : 0.03,
'years'  : 1,
'income_rent'  : 900,
'personal_rent' : 900,
'rent_rate' : 0.03,
}


"""

def investment_return(amount, annual_rate, months):
    """
    Expected return from investing amount for 'months' months
    """
    rate = 1 + annual_rate/12
    return amount * rate ** months - amount


def investment_return_on_stream(amounts, annual_rate):
    """
    Expected Cumulative return from investing a monthly sum every month
    """
    months_left = len(amounts)
    total = 0.0
    for amount in amounts:
        total += investment_return(amount, annual_rate, months_left)
        months_left -= 1
    return total

def get_upfront_costs(d, verbose = True):
    """
    Up front costs are the downpayment 
    and the opportunity cost of not investing the
    downpayment in the stock market
    """

    down_payment = d['home_price'] * d['down_payment']
    down_payment_opportunity_cost  = investment_return(down_payment, d['stock_market'], d['years'] * 12)

    if verbose:
        print ('Down Payment: %d' % down_payment)
        print ('Down Payment Opportunity Cost: %d' % down_payment_opportunity_cost)
    return down_payment, down_payment_opportunity_cost



def get_ownership_cost_stream(d, verbose = True):

    """
    Get Monthly costs of maintaining a home you own.
    Includes teax deducted property tax , maintenence and insurance
    """
    home_value = d['home_price']
    ownership = []
    for year in range(d['years']):
        yearly_cost = 0.0
        yearly_cost +=  (home_value *  d['property_tax']) * (1- d['marginal_tax_rate'])
        yearly_cost += home_value *  d['maintenance']
        yearly_cost += home_value *  d['home_owners_insurance']
        home_value *= (1+ d['house_appreciation'])
        monthly_cost = yearly_cost / 12
        ownership += [monthly_cost] * 12

    ownership = np.array(ownership)

    if verbose:
        print ('Total Ownership Costs: %d ' % ownership.sum())
    return ownership



def get_mortgage_cost_stream(d, verbose = True):
    """
    Compute the monthly mortgage payments broken
    down by principal and interest
    """

    principal = d['home_price'] * (1 - d['down_payment'] )
    rate = d['mortgage_rate'] / 12
    num_payments = d['mortgage_term']  * 12
    monthly_payment = principal *  (rate/(1-math.pow((1+rate), (-num_payments))))
    
    principal_cost = []
    interest_cost = []
    
    principal_left = principal
    
    for year in range( d['years']): 
        for month in range(12):
            if principal_left <=0:
                principal_cost.append(0)
                interest_cost.append(0)
            else:
                interest_portion = rate * principal_left
                principal_portion = monthly_payment - interest_portion
                principal_left -= principal_portion
                principal_cost.append(principal_portion)
                interest_cost.append(interest_portion * (1- d['marginal_tax_rate']))
    
    principal_cost = np.array(principal_cost)
    interest_cost = np.array(interest_cost)
    total_cost = principal_cost + interest_cost
    
    if verbose:
        print('Total Mortgage Cost: %d ' % (monthly_payment * num_payments))
        print('Total Mortgage Payed - Tax Deductions: %d ' % total_cost.sum())
        print ('Total Interest Payed %d ' % interest_cost.sum())
        print ('Total Principal Payed %d ' % principal_cost.sum())

    
    return principal_cost, interest_cost, total_cost


class Home():
    """
    The decision is between paying rent in your current home or buying a new home.

    Upfront Costs:
        Down Payment: since this money could have stayed in the stock market, there is an 
        opportunity cost


    Cost Streams:
        Ownership
        Mortgage

        No opportunity costs apply, Handled in income stream


    Income Streams:
        averted rent - (Ownership + Mortgage)

    if this is positive, then you get a return on that stream.
    if it is negative, you have an opportunity cost on that stream


    When you sell the house:

        you get the gains from the house and pay of the remaining principal

    """



    def __init__(self, d):
        self.d = d


    def get_rent_stream(self, verbose = True):
        """
        Stream of Rent that is averted
        """
        d = self.d

        rents = []
        rent = d['personal_rent']
            
        for year in range(d['years']): 
            for month in range(12):
                rents.append(rent)
            rent *= 1 + d['rent_rate']

        rents = np.array(rents)
        if verbose:
            print ('Total Rent Averted %d' % rents.sum())
        return rents


    def simulate(self):

        # OPTION 1: Buy home

        # Upfront Cost
        down_payment, down_payment_opportunity_cost = get_upfront_costs(self.d)

        # Cost Streams
        mortgage_principal_stream, mortgage_interest_stream, mortgage_total_stream  = get_mortgage_cost_stream(self.d)
        ownership_stream = get_ownership_cost_stream(self.d)

        # House Sale
        mortgage_paid = mortgage_total_stream.sum()
        mortgage_left = self.d['home_price'] * (1 - self.d['down_payment'] ) - mortgage_principal_stream.sum()

        home_value = self.d['home_price']
        home_return = investment_return(self.d['home_price'], self.d['house_appreciation'], self.d['years'] * 12)


        bottom_line_buying = - ownership_stream.sum() - mortgage_total_stream.sum() \
                             - down_payment - down_payment_opportunity_cost \
                             + home_value + home_return - mortgage_left \

        print (bottom_line_buying)

        # OPTION 2: Keep Renting
        rents = self.get_rent_stream()
        bottom_line_renting = - rents.sum() 

        print(bottom_line_renting)



        # There is a virtual stream in this scenario: the difference in cost streams could be invested
        # I keep having trouble wrapping my head around this. The idea is, your mortgage is lower than your
        #rent, you could be investing that money. Conversely, if your mortgage is higher than your rents, then you 
        #loose the potential to invest that money 
        derived_income_stream =    rents  - mortgage_total_stream - ownership_stream 
        derived_income_stream_investment_gain = investment_return_on_stream(derived_income_stream, self.d['stock_market'])
        print ('Return/ Cost on Stream of Averted Rent - Mortgage - Ownership: %d' % derived_income_stream_investment_gain)



        bottom_line =     (bottom_line_buying  + derived_income_stream_investment_gain) - bottom_line_renting
  
        
        print('Bottom Line: %d' %  bottom_line)
        
        plt.figure()
        plt.plot(ownership_stream, label = 'Ownership')
        plt.plot(mortgage_total_stream, label = 'Morgage')
        plt.plot(ownership_stream + mortgage_total_stream, label =  'total monthly costs')
        plt.plot(rents, label = 'Rents Averted')
        plt.legend()


    
### Rental

class Rental():

    """
    The decision is between buying a home and investing the money in the
    stock market.

    Upfront Costs:
        Down Payment

        since this money could have stayed in the stock market, there is an 
        opportunity cost


    Cost Streams:
        Ownership
        Mortgage

        since this money could have been invested in the stock market, there is an 
        opportunity cost

    Income Streams:
        Rent

        this income can be invested, so there is an investment return

    """

    def __init__(self, d):
        self.d = d


    def get_rent_stream(self, verbose = True):
        """
        Returns:
        Stream of Income rents plus investment return of the stream of rents.
        """
        d = self.d 

        rents = []
        rent = d['income_rent']

        for year in range(d['years']): 
            for month in range(12):
                rents.append(rent * (1 - d['marginal_tax_rate']))
            rent *= 1 + d['rent_rate']

        rents = np.array(rents)

        if verbose:
            print ('Total Rental Income: %d' % rents.sum())

        return rents


    
    def simulate(self):


        # Upfront Cost
        down_payment, down_payment_opportunity_cost = get_upfront_costs(self.d)

        # Cost Streams
        mortgage_principal_stream, mortgage_interest_stream, mortgage_total_stream  = get_mortgage_cost_stream(self.d)
        ownership_stream = get_ownership_cost_stream(self.d)

        # Opportunity Costs
        ownership_opportunity_cost = investment_return_on_stream(mortgage_total_stream + ownership_stream, self.d['stock_market'])

        print ('Ownership Opportunity Cost: %d ' % ownership_opportunity_cost)


        # Income
        rents = self.get_rent_stream()
        rents_investment_return = investment_return_on_stream(rents, self.d['stock_market'])
        print ('Rental Income Investment Returns: %d ' % rents_investment_return)


        # House Sale
        mortgage_paid = mortgage_total_stream.sum()
        mortgage_left = self.d['home_price'] * (1 - self.d['down_payment'] ) - mortgage_principal_stream.sum()

        home_value = self.d['home_price']
        home_return = investment_return(self.d['home_price'], self.d['house_appreciation'], self.d['years'] * 12)


        bottom_line = - ownership_stream.sum() - mortgage_total_stream.sum() \
                             - ownership_opportunity_cost \
                             - down_payment - down_payment_opportunity_cost \
                             + rents.sum() + rents_investment_return \
                             + home_value + home_return - mortgage_left \

        
        print('Bottom Line: %d' %  bottom_line)
        
        plt.figure()
        plt.plot(ownership_stream, label = 'Ownership')
        plt.plot(mortgage_total_stream, label = 'Morgage')
        plt.plot(ownership_stream + mortgage_total_stream, label =  'total monthly costs')
        plt.plot(rents, label = 'Rental Income')
        plt.legend()



    

