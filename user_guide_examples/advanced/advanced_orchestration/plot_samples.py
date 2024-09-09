# This is used to generate the final plot using results data from a previous simulation run

import json
import sys, os
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
plt.style.use('ggplot')
plt.figure(figsize=[5,4])

def tsplot(x, y, n=20, percentile_min=1, percentile_max=99, color='r', plot_mean=True, plot_median=False, line_color='k', **kwargs):
    '''
    This is a plotting helper function. It calculate the lower and upper percentile groups, skipping 50 percentile.
    '''
    perc1 = np.percentile(y, np.linspace(percentile_min, 50, num=n, endpoint=False), axis=0)
    perc2 = np.percentile(y, np.linspace(50, percentile_max, num=n+1)[1:], axis=0)

    if 'alpha' in kwargs:
        alpha = kwargs.pop('alpha')
    else:
        alpha = 1/n
    # fill lower and upper percentile groups
    for p1, p2 in zip(perc1, perc2):
        plt.fill_between(x, p1, p2, alpha=alpha, color=color, edgecolor=None)
    if plot_mean:
        plt.plot(x, np.mean(y, axis=0), color=line_color)
    if plot_median:
        plt.plot(x, np.median(y, axis=0), color=line_color)

    return plt.gca()

def main():
    # variable inputs from execution
    samples = 30
    output_path = os.getcwd()
    if len(sys.argv) > 1:
        samples = sys.argv[1]
        output_path = sys.argv[2]
    # variable inputs set internal
    out_data = output_path+'/results'
    offset = 10

    print('plotting results')
    peak = []
    for i in range(int(samples)):
        if i == 0:
            df = pd.read_csv(out_data+r'/peak_power_at_all_evs_'+str(i+offset)+'.csv')
        else:
            df = pd.read_csv(out_data+r'/peak_power_at_all_evs_'+str(i+offset)+'.csv')
            df.drop(['Hour'], axis=1, inplace=True)
        peak.append(df)

    peak_power = pd.concat(peak, axis=1)
    t = np.array(peak_power.Hour)
    y = np.array(peak_power.iloc[:,1:]).T
    tsplot(t, y, n=100, percentile_min=2.5, percentile_max=97.5, plot_median=True, plot_mean=False, color='g', line_color='navy')
    plt.ylabel('kW')
    plt.xlabel('Hours')
    plt.plot()
    plt.gca().set_position([.14,.14,.82,.82])
    plt.savefig("montecarlo-ev-peak-power.png")
    plt.show()

if __name__ == "__main__":
    main()
