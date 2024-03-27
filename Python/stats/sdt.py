"""Module to run different signal detection theory analyses.

Usage example:
import numpy as np
import sdt

# Load your data (signal present is the ground truth)
response = np.array(your_response_data)
signal_present = np.array(your_signal_present_data)

# Extract SDT metrics (assuming equal variance in signal+noise and noise distributions)
sdt_metrics = sdt.extract_sdt(response, signal_present, equal_var=True, distributions_plot=True, roc_plot=True)

# Extract SDT metrics (assuming different variance in signal+noise and noise distributions)
sdt_metrics = sdt.extract_sdt(response, signal_present, equal_var=False, distributions_plot=True, roc_plot=True)

# Access the metrics
d = sdt_metrics['d'] # d-prime
c_coefficient = sdt_metrics['c'] # Coefficient-c
criterion = sdt_metrics['criterion'] # Criterion point
beta = sdt_metrics['beta'] # Beta coefficient
logbeta = sdt_metrics['logbeta'] # Logarithm of beta
AUC = sdt_metrics['AUC'] # Area under the curve
hitrate = sdt_metrics['hitrate'] # Hit rate
farate = sdt_metrics['farate'] # False alarm rate
"""

import warnings
import numpy as np
import scipy.stats as stats
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import seaborn as sns


def plot_roc(hitrate: np.ndarray, farate: np.ndarray, auc: float = None) -> None:
    """Plots the ROC curve.

    Parameters:
    -----------
    hitrate: np.ndarray
        Hit rate values (sorted and with 0 and 1 at the ends).
    farate: np.ndarray
        False alarm rate values (sorted and with 0 and 1 at the ends).
    auc: float
        Area under the curve. If provided, it will be displayed in the plot title.
    """
    # Plot ROC curve
    title = 'ROC Curve'
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(farate, hitrate, marker='o')
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray')
    if auc is not None:
        title = 'ROC Curve\nAUC = {:.2f}'.format(auc)
    ax.set(xlabel='False Alarm Rate', ylabel='Hit Rate', title=title)
    plt.show()


def plot_distributions(d: float, sigmasignal: float, cpoint: float = None):
    """Plots the signal+noise and noise distributions with the criterion point.

    Parameters:
    -----------
    d: float
        d-prime value.
    sigmasignal: float
        Standard deviation of the signal+noise distribution.
    cpoint: float
        (Optional) Criterion point. Default = None. If provided, a criterion line is plotted.
    """
    n = 10000

    # Generate signal+noise and noise distributions
    noise = np.random.normal(loc=0, scale=1, size=n)
    signal = np.random.normal(loc=d, scale=sigmasignal, size=n)

    # Plot distributions
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.histplot(noise, color=".2", kde=True,
                 stat='density', ax=ax, label='Noise')
    sns.histplot(signal, color="darkred", kde=True, stat='density',
                 ax=ax, label='Signal+Noise')
    if cpoint:
        ax.axvline(cpoint, color='black', linestyle='--',
                   label='Criterion Point')
        ax.set_xticks(list(ax.get_xticks()) + [cpoint])
    ax.set(xlabel='', ylabel='Frequency',
           title=f'Signal+Noise and Noise Distributions\nd-prime = {d:.2f}')
    ax.legend()
    plt.show()


def extract_sdt(ypred: np.ndarray, ytrue: np.ndarray, equal_var: bool = False, distributions_plot: bool = False, roc_plot: bool = False) -> dict:
    """Extracts signal detection theory metrics from predicted and true labels.

    Parameters:
    -----------
    ypred: np.ndarray
        Predicted labels. Shape (n_samples, n_conditions). Signal responses = 1, noise responses = 0.
    ytrue: np.ndarray
        True labels. Shape (n_samples, n_conditions). Signal present = 1, signal absent = 0.
    equal_var: bool
        Whether to assume equal variance in signal and noise distributions.
    roc_plot: bool
        Whether to plot the ROC curve.
    distributions_plot: bool
        Whether to plot the signal+noise and noise distributions.

    Returns:
    --------
    sdt_metrics: dict
        Dictionary containing signal detection theory metrics.
        {'hitrate': hit-rate, 'farate': false-alarm-rate, 'd': d-prime, 'sigmasignal': signal distribution std. dev., 
        'c': coefficient-c,  'beta': beta, 'logbeta': log-beta, 'criterion': criterion point, 'AUC': area-under-curve}
    """
    # Hits and False Alarms
    hits: np.ndarray = np.sum((ypred == 1) & (ytrue == 1), axis=0)
    fas: np.ndarray = np.sum((ypred == 1) & (ytrue == 0), axis=0)

    # Hit rate and False Alarm rate
    hitrate: np.ndarray = hits / np.sum(ytrue == 1, axis=0)
    farate: np.ndarray = fas / np.sum(ytrue == 0, axis=0)

    # z-scores
    zhit = stats.norm.ppf(hitrate)
    zfa = stats.norm.ppf(farate)

    if equal_var or hits.size == 1:
        # Assuming equal variance assumption in signal+noise and noise distributions
        # also if only one condition is present
        sigmasignal = 1
        d: float = np.mean(zhit - zfa)
        c: float = -.5 * np.mean(zhit + zfa)
        if d == 0:
            warnings.warn(
                "Distribution of signal+noise is equal to noise distribution.")
        cpoint: float = d / 2 + c

    else:
        # Assuming different variance in signal+noise and noise distributions
        # approx. = signal+noise distribution standard deviation
        sigmasignal: float = np.std(zfa) / np.std(zhit)
        d: float = sigmasignal * np.mean(zhit) - np.mean(zfa)
        c: float = -.5 * np.mean(zhit + zfa)
        if sigmasignal != 1:
            # find intersection points of the two distributions
            roots: np.array = np.zeros((2,), dtype=float)
            A = 1 - 1/sigmasignal**2
            B = 2 * d / sigmasignal**2
            C = 2 * np.log(1/sigmasignal) - d**2 / sigmasignal**2
            roots[0] = (-B + np.sqrt(B**2 - 4*A*C)) / (2*A)
            roots[1] = (-B - np.sqrt(B**2 - 4*A*C)) / (2*A)
            roots = np.sort(roots, axis=None)
            if sigmasignal >= 1:
                # if sigma signal+noise distribution > sigma noise distribution
                cpoint: float = roots[1] + c
            else:
                cpoint: float = roots[0] + c
        else:
            if d == 0:
                warnings.warn(
                    "Distribution of signal+noise is equal to noise distribution.")
            cpoint: float = d / 2 + c

    beta: float = stats.norm.pdf(
        cpoint, loc=d, scale=sigmasignal) / stats.norm.pdf(cpoint, loc=0, scale=1)
    lnbeta: float = np.log(beta)

    # Add 0 and 1 to hitrate and farate for ROC curve and AUC calculation
    y: np.ndarray = np.concatenate(([0], np.array(hitrate).flatten(), [1]))
    x: np.ndarray = np.concatenate(([0], np.array(farate).flatten(), [1]))
    # sort by farate
    y = y[np.argsort(x)]
    x = np.sort(x)
    auc: float = integrate.simpson(y=y, x=x)

    sdt_metrics: dict = {'hitrate': hitrate, 'farate': farate, 'd': d, 'sigmasignal': sigmasignal, 'c': c,
                         'beta': beta, 'logbeta': lnbeta, 'criterion': cpoint, 'AUC': auc}

    if distributions_plot:
        plot_distributions(d, cpoint, sigmasignal)

    if roc_plot:
        plot_roc(hitrate=y, farate=x, auc=auc)

    return sdt_metrics


def _test_distribution_plot(d, sigmasignal, cpoint, truec, ax: plt.Axes):
    n = 1000

    # Generate signal+noise and noise distributions
    noise = np.random.normal(loc=0, scale=1, size=n)
    signal = np.random.normal(loc=d, scale=sigmasignal, size=n)

    # Plot distributions
    sns.histplot(noise, color=".2", kde=True, ax=ax, label='Noise')
    sns.histplot(signal, color="darkred", kde=True,
                 ax=ax, label='Signal+Noise')
    ax.axvline(cpoint, color='black', linestyle='--', label='Criterion Point')
    ax.axvline(truec, color='steelblue', linestyle='--',
               label='True Criterion Point')
    ax.set_xticks(list(ax.get_xticks()) + [truec])
    ax.set(xlabel='', ylabel='Density',
           title='Signal+Noise and Noise Distributions; d = {:.2f}'.format(d))


def test():
    criterions = [.5, .2, 1.5, 1]

    signal_present = np.random.rand(1000) > .5

    # Assuming signal distributed as N(2, 1) and noise as N(0, 1)
    signal = np.random.normal(0, 1, size=signal_present.size)
    signal[signal_present] = np.random.normal(
        2, 1, size=np.sum(signal_present))

    responses = np.zeros((signal.size, len(criterions)))

    # Extract SDT metrics for different criterions
    fig, axs = plt.subplots(2, 2, figsize=(12, 12))
    for i, truec in enumerate(criterions):
        response = signal > truec
        responses[:, i] += response

        sdt_metrics = extract_sdt(
            response, signal_present, equal_var=True, distributions_plot=False, roc_plot=False)
        print(f"SDT metrics assuming equal variance (criterion = {truec}):")
        print(sdt_metrics)

        _test_distribution_plot(
            d=sdt_metrics['d'], sigmasignal=sdt_metrics['sigmasignal'], cpoint=sdt_metrics['criterion'], truec=truec, ax=axs[i//2, i % 2])

        if i == 0:
            sdt_metrics = extract_sdt(
                response, signal_present, equal_var=False)
            print(
                f"SDT metrics assuming different variance but only one value test:")
            print(sdt_metrics)
        print("\n"*2)

    # Plots and SDT metrics over different conditions (criterions)
    axs[1, 1].legend()
    plt.show()

    # And overall
    print("SDT metrics over different conditions assuming unequal variance:")
    sdt_metrics = extract_sdt(responses, np.array(
        [signal_present]*len(criterions)).T, equal_var=False, distributions_plot=True, roc_plot=True)
    print(sdt_metrics)


if __name__ == '__main__':
    test()
