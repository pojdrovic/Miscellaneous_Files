__author__ = 'Petar Ojdrovic'
 
import numpy
import scipy.stats
import time
 
#Options Pricing
 
"""
S: initial stock price
k: strike price
T: expiration time
sigma: volatility
r: risk-free rate
"""
 
##What is d1, d2, and pricer? d1 is the first differential of the underlying pr
def d1(S0, K, r, siga, T):
    return (numpy.log(S0/K) + (r + siga**2/2) * T)/(siga * numpy.sqrt(T))
 
def d2(S0, K, r, siga, T):
    return (numpy.log(S0/K) + (r - siga**2/2) * T)/(siga * numpy.sqrt(T))
 
def OptionsPricing(type, S0, K, r, sigma, T):
    if type=="C":
        return S0 * scipy.stats.norm.cdf(d1(S0, K, r, sigma, T)) - K * numpy.exp(-r * T) * scipy.stats.norm.cdf(d2(S0, K, r, sigma, T))
    else:
        return K * numpy.exp(-r * T) * scipy.stats.norm.cdf(-d2(S0, K, r, sigma, T)) - S0 * scipy.stats.norm.cdf(-d1(S0, K, r, sigma, T))
 
 
 
S0 = 104
K = 105
r = .15
sigma = 0.45
T = 0.05
type = "C"
 
print("Stock price is", S0)
print("Strike price is", K)
print("interest rate is", r)
print("volatility is", sigma)
print("time to maturity in years", T)
 
t=time.time()
c_OP = OptionsPricing(type, S0, K, r, sigma, T)
elapsed = time.time()-t
print("options price:", c_OP, elapsed)