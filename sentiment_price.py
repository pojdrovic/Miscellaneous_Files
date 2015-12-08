import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import csv
from numpy import *
from scipy.stats.kde import gaussian_kde
import os

##############################
# Petar Ojdrovic
##############################
# parses sentiment data
# compares with underlying prices

import bisect # for bisection search
def find_le(a, x):
    'Find rightmost value less than or equal to x'
    i = bisect.bisect_right(a, x)
    if i:
        return i-1#a[i-1]
    raise ValueError

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return i#a[i]
    raise ValueError


#### load prices ####
data = loadtxt('Prices_NYSE100_2011-2013_5.csv', delimiter=',', dtype='string')
tickers = data[0,1:]
times = data[1:,0]
times = [datetime.datetime.strptime(t, '%Y%m%d %H:%M') for t in times] # datetime object
ords = [t.toordinal() for t in times] # ordinals (integer for each day)
P = data[1:,1:].astype(float)


#### compare with news data ####
# load news data
with open('Alex_Top100_2011to2013/Alex_Top100_2011.xml') as input:
	lines = input.readlines()
with open('Alex_Top100_2011to2013/Alex_Top100_2012.xml') as input:
	for l in input:
		lines.append(l)
with open('Alex_Top100_2011to2013/Alex_Top100_2013.xml') as input:
	for l in input:
		lines.append(l)

# loop through tickers...
for tick in tickers[:10]:
	n = where(array(tickers)==tick)[0][0]
	newsdat = []
	newstime = []
	for i in range(len(lines)):
		if '<Row>' in lines[i] and '>'+tick+'<' in lines[i+3]:
			day = lines[i+5].split('Type="String">')[1].split('</Data>')[0]
			minute = lines[i+6].split('Type="String">')[1].split('</Data>')[0][:8]
			sentiment = float(lines[i+7].split('Type="Number">')[1].split('</Data>')[0])
			confidence = float(lines[i+8].split('Type="Number">')[1].split('</Data>')[0])
			novelty = float(lines[i+9].split('Type="Number">')[1].split('</Data>')[0])
			relevance = float(lines[i+11].split('Type="Number">')[1].split('</Data>')[0])
			newsdat.append([sentiment, confidence, novelty, relevance])
			newstime.append([day, minute])
	newsdat = array(newsdat)
	
	if len(newsdat)==0: # no events for this ticker
		continue
	
	X = [] # high quality events
	for i in range(len(newsdat)):
		if newsdat[i,0]!=0.0 and newsdat[i,1]>0.95 and newsdat[i,2]==1.0 and newsdat[i,3]==1.0:
			event_time = datetime.datetime.strptime(newstime[i][0]+' '+newstime[i][1],'%Y-%m-%d %H:%M:%S')
			X.append([event_time, newsdat[i,0]])

	L = [] # check to see if news anticipates (intraday)
	F = [] # check to see if news follows (intraday)
	L_o = [] # overnight
	F_o = [] # overnight
	for x in X:
		if x[0].toordinal() in ords:
			# intraday
			if (x[0].time() >= datetime.time(9,30)) and (x[0].time() <= datetime.time(16,00)):
				close_p = P[find_le(ords, x[0].toordinal()),n] # close price that day
				open_p = P[find_ge(ords, x[0].toordinal()),n]
				recent_p = P[find_le(times, x[0]),n] # most recent price before news
				L.append([x[1], (close_p-recent_p)/recent_p])
				F.append([x[1], (recent_p-open_p)/open_p])
			# overnight
			else:
				close_p = P[find_le(ords, x[0].toordinal()),n] # close price that day
				open_p = P[find_ge(ords, x[0].toordinal()),n]
				recent_p = P[find_le(times, x[0]),n] # most recent price before news
				next_close_p = P[find_le(ords, x[0].toordinal()+1),n] # should revise to handle Fridays...
				L_o.append([x[1], (next_close_p - recent_p)/recent_p])
				F_o.append([x[1], (close_p - open_p)/open_p])
	L = array(L)
	F = array(F)
	print(tick+': '+str(sum(L[:,0]==1))+' positive, '+str(sum(L[:,0]==-1))+' negative')
	
	# make KDE plots
	b = 1.5*max(abs(array([min(L[:,1]), max(L[:,1]), min(F[:,1]), max(F[:,1])])))
	xs = arange(-b, b, 2*b/1000.0)
	kde_L_p = gaussian_kde([L[i,1] for i in range(len(L)) if L[i,0]>0]) # leading, positive
	y_L_p = kde_L_p.evaluate(xs)
	kde_L_n = gaussian_kde([L[i,1] for i in range(len(L)) if L[i,0]<0]) # leading, negative
	y_L_n = kde_L_n.evaluate(xs)
	kde_F_p = gaussian_kde([F[i,1] for i in range(len(F)) if F[i,0]>0]) # following, positive
	y_F_p = kde_F_p.evaluate(xs)
	kde_F_n = gaussian_kde([F[i,1] for i in range(len(F)) if F[i,0]<0]) # following, negative
	y_F_n = kde_F_n.evaluate(xs)
	
	fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
	ax = fig.add_subplot(111)
	ax.plot(xs, y_L_p, linewidth=2, color='r')
	ax.plot(xs, y_L_n, linewidth=2, color='b')
	ax.fill_between(xs, y_L_p, color='r', alpha=0.2)
	ax.fill_between(xs, y_L_n, color='b', alpha=0.2)
	ax.legend(('Positive', 'Negative'), loc='upper left')
	top = (int(max([max(y_L_p), max(y_L_n)]))/10)*10+10
	ax.plot([0, 0], [0, top], color='k', linewidth=2)
	ax.grid()
	plt.title(tick,size=20)
	pdf = PdfPages(tick+'_leading_intraday.pdf')
	pdf.savefig()
	pdf.close()
	plt.close()

	fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
	ax = fig.add_subplot(111)
	ax.plot(xs, y_F_p, linewidth=2, color='r')
	ax.plot(xs, y_F_n, linewidth=2, color='b')
	ax.fill_between(xs, y_F_p, color='r', alpha=0.2)
	ax.fill_between(xs, y_F_n, color='b', alpha=0.2)
	ax.legend(('Positive', 'Negative'), loc='upper left')
	top = (int(max([max(y_F_p), max(y_F_n)]))/10)*10+10
	ax.plot([0, 0], [0, top], color='k', linewidth=2)
	ax.grid()
	plt.title(tick,size=20)
	pdf = PdfPages(tick+'_following_intraday.pdf')
	pdf.savefig()
	pdf.close()
	plt.close()