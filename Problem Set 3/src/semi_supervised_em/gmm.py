import matplotlib.pyplot as plt
import numpy as np
import os

PLOT_COLORS = ['red', 'green', 'blue', 'orange']  # Colors for your plots
K = 4           # Number of Gaussians in the mixture model
NUM_TRIALS = 3  # Number of trials to run (can be adjusted for debugging)
UNLABELED = -1  # Cluster label for unlabeled data points (do not change)


def main(is_semi_supervised, trial_num):
    """Problem 3: EM for Gaussian Mixture Models (unsupervised and semi-supervised)"""
    print('Running {} EM algorithm...'
          .format('semi-supervised' if is_semi_supervised else 'unsupervised'))

    # Load dataset
    train_path = os.path.join('.', 'train.csv')
    x_all, z_all = load_gmm_dataset(train_path)

    # Split into labeled and unlabeled examples
    labeled_idxs = (z_all != UNLABELED).squeeze()
    x_tilde = x_all[labeled_idxs, :]   # Labeled examples
    z_tilde = z_all[labeled_idxs, :]   # Corresponding labels
    x = x_all[~labeled_idxs, :]        # Unlabeled examples

    # *** START CODE HERE ***
    ''' (1) Initialize mu and sigma by splitting the m data points uniformly at random
     into K groups, then calculating the sample mean and covariance for each group '''

    p = x.copy()    
    np.random.shuffle(p)
    groups = np.split(p, K)
    mu = []
    sigma = []
    
    for group in groups:
        
        mean = np.sum(group, axis = 0)/group.shape[0]
        covariance = (x - mean).T.dot(x - mean)/group.shape[0]
        
        mu.append(mean)
        sigma.append(covariance)

    phi = np.ones(K)/K
    
    n = x.shape[0]
    
    w = np.ones([n, K])/K
    
    # *** END CODE HERE ***

    if is_semi_supervised:
        w = run_semi_supervised_em(x, x_tilde, z_tilde, w, phi, mu, sigma)
    else:
        w = run_em(x, w, phi, mu, sigma)

    # Plot your predictions
    z_pred = np.zeros(n)
    if w is not None:  # Just a placeholder for the starter code
        for i in range(n):
            z_pred[i] = np.argmax(w[i])

    plot_gmm_preds(x, z_pred, is_semi_supervised, plot_id=trial_num)


def run_em(x, w, phi, mu, sigma):
    """Problem 3(d): EM Algorithm (unsupervised).

    See inline comments for instructions.

    Args:
        x: Design matrix of shape (n, d).
        w: Initial weight matrix of shape (n, k).
        phi: Initial mixture prior, of shape (k,).
        mu: Initial cluster means, list of k arrays of shape (d,).
        sigma: Initial cluster covariances, list of k arrays of shape (d, d).

    Returns:
        Updated weight matrix of shape (n, d) resulting from EM algorithm.
        More specifically, w[i, j] should contain the probability of
        example x^(i) belonging to the j-th Gaussian in the mixture.
    """
    # No need to change any of these parameters
    eps = 1e-3  # Convergence threshold
    max_iter = 1000

    # Stop when the absolute change in log-likelihood is < eps
    # See below for explanation of the convergence criterion
    it = 0
    logl = prev_logl = None

    while it < max_iter and (prev_logl is None or np.abs(logl - prev_logl) >= eps):

        # *** START CODE HERE
        prev_logl = logl
        
        n = w.shape[0]
        K = w.shape[1]
        
        for j, (mu_j, sigma_j) in enumerate(zip(mu, sigma)):
            for i in range(n):
                w[i, j] = gaussian(x[i], mu_j, sigma_j) * phi[j]

        sumG = np.sum(w, axis = 1)
        for a in range(K):
            w[:, a] = w[:, a]/sumG

        phi = np.sum(w, axis = 0)/n

        for j in range(K):
            mu[j] = w[:, j].dot(x)/np.sum(w[:, j])
            sigma[j] = (x - mu[j]).T.dot(np.diag(w[:, j])).dot(x - mu[j])/np.sum(w[:, j])
        
        px = np.zeros(n)
        pxz = np.zeros(n)
        
        for j in range(K):
            for i in range(n):
                pxz[i] = gaussian(x[i], mu[j], sigma[j]) * phi[j]
                
            px += pxz
            
        logl = np.sum(np.log(px))

        it += 1

    print(it)
        
        # By log-likelihood, we mean `ll = sum_x[log(sum_z[p(x|z) * p(z)])]`.
        # We define convergence by the first iteration where abs(ll - prev_ll) < eps.
        # Hint: For debugging, recall part (a). We showed that ll should be monotonically increasing.
        # *** END CODE HERE ***

    return w


def run_semi_supervised_em(x, x_tilde, z_tilde, w, phi, mu, sigma):
    """Problem 3(e): Semi-Supervised EM Algorithm.

    See inline comments for instructions.

    Args:
        x: Design matrix of unlabeled examples of shape (n, d).
        x_tilde: Design matrix of labeled examples of shape (n_tilde, d).
        z_tilde: Array of labels of shape (n_tilde, 1).
        w: Initial weight matrix of shape (n, k).
        phi: Initial mixture prior, of shape (k,).
        mu: Initial cluster means, list of k arrays of shape (d,).
        sigma: Initial cluster covariances, list of k arrays of shape (d, d).

    Returns:
        Updated weight matrix of shape (n, d) resulting from semi-supervised EM algorithm.
        More specifically, w[i, j] should contain the probability of
        example x^(i) belonging to the j-th Gaussian in the mixture.
    """
    # No need to change any of these parameters
    alpha = 20.  # Weight for the labeled examples
    eps = 1e-3   # Convergence threshold
    max_iter = 1000

    # Stop when the absolute change in log-likelihood is < eps
    # See below for explanation of the convergence criterion
    it = 0
    logl = prev_logl = None

    while it < max_iter and (prev_logl is None or np.abs(logl - prev_logl) >= eps):
        # *** START CODE HERE ***
        prev_logl = logl
        n = w.shape[0]
        k = w.shape[1]
        n_tilde = x_tilde.shape[0]

        for j, (mu_j, sigma_j) in enumerate(zip(mu, sigma)):
            
            for i in range(n):
                
                w[i, j] = gaussian(x[i], mu_j, sigma_j) * phi[j]
        
        sumG = np.sum(w, axis = 1)
        
        for a in range(K):
            w[:, a] = w[:, a]/sumG

        w_tilde = np.zeros([n_tilde, k])
        
        for j in range(K):
            for i in range(n_tilde):
                if z_tilde[i] == j:
                    w_tilde[i, j] = 1

        phi = (np.sum(w, axis = 0) + alpha * np.sum(w_tilde, axis = 0))/(n + alpha * n_tilde)
        
        for j in range(K):
            mu[j] = (w[:, j].dot(x) + alpha * w_tilde[:, j].dot(x_tilde))/(np.sum(w[:, j]) + alpha * np.sum(w_tilde[:, j]))
            sNum = (x - mu[j]).T.dot(np.diag(w[:, j])).dot(x - mu[j]) + alpha * (x_tilde - mu[j]).T.dot(np.diag(w_tilde[:, j]).dot(x_tilde - mu[j]))
            sDen = np.sum(w[:, j]) + alpha * np.sum(w_tilde[:, j])
            sigma[j] = sNum/sDen
        
        px = np.zeros(n)
        pxz = np.zeros(n)
        
        for j in range(K):
            for i in range(n):
                pxz[i] = gaussian(x[i], mu[j], sigma[j]) * phi[j]
            px += pxz
            
        l_unsup = np.sum(np.log(px))

        pxz_tilde = np.zeros(n_tilde)
        
        for j in range(K):
            for i in range(n_tilde):
                pxz_tilde[i] += gaussian(x_tilde[i], mu[j], sigma[j]) * phi[j]
                
        l_sup = np.sum(np.log(pxz_tilde))

        logl = l_unsup + alpha * l_sup
        it += 1
        
    print(it)
        # Hint: For debugging, recall part (a). We showed that ll should be monotonically increasing.
        # *** END CODE HERE ***

    return w


# *** START CODE HERE ***
def gaussian(x_i, mu, sigma):
    
        n = sigma.shape[0]
        num = ((2 * np.pi) ** (n/2)) * np.sqrt(np.linalg.det(sigma))
        f = 1 / num

        matrix = (x_i - mu) @ np.linalg.inv(sigma) @ (x_i - mu).T

        return f * np.exp(-0.5 * matrix)
    # *** END CODE HERE ***


def plot_gmm_preds(x, z, with_supervision, plot_id):
    """Plot GMM predictions on a 2D dataset `x` with labels `z`.

    Write to the output directory, including `plot_id`
    in the name, and appending 'ss' if the GMM had supervision.

    NOTE: You do not need to edit this function.
    """
    plt.figure(figsize=(12, 8))
    plt.title('{} GMM Predictions'.format('Semi-supervised' if with_supervision else 'Unsupervised'))
    plt.xlabel('x_1')
    plt.ylabel('x_2')

    for x_1, x_2, z_ in zip(x[:, 0], x[:, 1], z):
        color = 'gray' if z_ < 0 else PLOT_COLORS[int(z_)]
        alpha = 0.25 if z_ < 0 else 0.75
        plt.scatter(x_1, x_2, marker='.', c=color, alpha=alpha)

    file_name = 'pred{}_{}.pdf'.format('_ss' if with_supervision else '', plot_id)
    save_path = os.path.join('.', file_name)
    plt.savefig(save_path)


def load_gmm_dataset(csv_path):
    """Load dataset for Gaussian Mixture Model.

    Args:
         csv_path: Path to CSV file containing dataset.

    Returns:
        x: NumPy array shape (n_examples, dim)
        z: NumPy array shape (n_exampls, 1)

    NOTE: You do not need to edit this function.
    """

    # Load headers
    with open(csv_path, 'r') as csv_fh:
        headers = csv_fh.readline().strip().split(',')

    # Load features and labels
    x_cols = [i for i in range(len(headers)) if headers[i].startswith('x')]
    z_cols = [i for i in range(len(headers)) if headers[i] == 'z']

    x = np.loadtxt(csv_path, delimiter=',', skiprows=1, usecols=x_cols, dtype=float)
    z = np.loadtxt(csv_path, delimiter=',', skiprows=1, usecols=z_cols, dtype=float)

    if z.ndim == 1:
        z = np.expand_dims(z, axis=-1)

    return x, z


if __name__ == '__main__':
    np.random.seed(229)
    # Run NUM_TRIALS trials to see how different initializations
    # affect the final predictions with and without supervision
    for t in range(NUM_TRIALS):
        main(is_semi_supervised=False, trial_num=t)

        # *** START CODE HERE ***
        # Once you've implemented the semi-supervised version,
        # uncomment the following line.
        # You do not need to add any other lines in this code block.
        main(is_semi_supervised=True, trial_num=t)
        # *** END CODE HERE ***
