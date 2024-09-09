import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot') # this was just used for the examples

# data
t = np.linspace(0,100,100)
y = 5 * np.sin(t/10) + 4*np.random.randn(100*150).reshape(150, 100)
y_ = 5 * np.sin(t/10) + 4*np.random.randn(100*4000).reshape(4000, 100)

t__ = np.linspace(0,100,6)
y__ = 5 * np.sin(t__/10) + 4*np.random.randn(6*4000).reshape(4000, 6)

t.shape
y.shape
perc1 =
np.percentile(y, np.linspace(1, 50, num=10, endpoint=False), axis=0)#.shape
n=10
np.percentile(y, np.linspace(1, 50, num=n, endpoint=False), axis=0)
np.percentile(y, np.linspace(50, 99, num=n+1)[1:], axis=0)

# credit goes to this thread:
# https://github.com/arviz-devs/arviz/issues/2#issuecomment-310468720
def tsplot(x, y, n=20, percentile_min=1, percentile_max=99, color='r', plot_mean=True, plot_median=False, line_color='k', **kwargs):
    # calculate the lower and upper percentile groups, skipping 50 percentile
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


tsplot(t, y, n=100, percentile_min=2.5, percentile_max=97.5, plot_median=True, plot_mean=False, color='g', line_color='navy')

plt.plot()
plt.show()
tsplot(t, y, n=5, percentile_min=2.5, percentile_max=97.5, plot_median=True, plot_mean=False, color='g', line_color='navy')
# IQR
tsplot(t, y_, n=1, percentile_min=25, percentile_max=75, plot_median=False, plot_mean=False, color='g', line_color='navy', alpha=0.3)
#  90% interval
tsplot(t, y_, n=1, percentile_min=5, percentile_max=95, plot_median=True, plot_mean=False, color='g', line_color='navy', alpha=0.3)


y_.shape
