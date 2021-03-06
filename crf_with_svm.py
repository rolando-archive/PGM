"""
===============================
OCR Letter sequence recognition
===============================
This example illustrates the use of a chain CRF for optical character
recognition. The example is taken from Taskar et al "Max-margin markov random
fields".

Each example consists of a handwritten word, that was presegmented into
characters.  Each character is represented as a 16x8 binary image. The task is
to classify the image into one of the 26 characters a-z. The first letter of
every word was ommited as it was capitalized and the task does only consider
small caps letters.

We compare classification using a standard linear SVM that classifies
each letter individually with a chain CRF that can exploit correlations
between neighboring letters (the correlation is particularly strong
as the same words are used during training and testing).

The first figures shows the segmented letters of four words from the test set.
In set are the ground truth (green), the prediction using SVM (blue) and the
prediction using a chain CRF (red).

The second figure shows the pairwise potentials learned by the chain CRF.
The strongest patterns are "y after l" and "n after i".

There are obvious extensions that both methods could benefit from, such as
window features or non-linear kernels. This example is more meant to give a
demonstration of the CRF than to show its superiority.
"""
import numpy as np
import matplotlib.pyplot as plt
import copy
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from common.viewers.imshow import imshow
from pystruct.datasets import load_letters
from pystruct.models import ChainCRF, GraphCRF
from pystruct.learners import FrankWolfeSSVM
from sklearn.linear_model import LinearRegression
from common.utils import get_letters_in_pred_like

abc = "abcdefghijklmnopqrstuvwxyz"

# Load data:
letters = load_letters()
X, y, folds = letters['data'], letters['labels'], letters['folds']

# we convert the lists to object arrays, as that makes slicing much more
# convenient
X, y = np.array(X), np.array(y)
X_train, X_test = X[folds == 1], X[folds != 1]
y_train, y_test = y[folds == 1], y[folds != 1]

# Train linear SVM
svm = LinearSVC(dual=False, C=.1)
# svm = SVC(kernel='linear', C=.1)
svm.fit(np.vstack(X_train), np.hstack(y_train))

# Predict all data with the SVM calssifier:
# y_train[word_ind].reshape((-1,1))
svm_predictions_train = get_letters_in_pred_like(X_train, svm, size_of_pred=26)
svm_predictions_test = get_letters_in_pred_like(X_test, svm, size_of_pred=26)

# Train CRF
model = ChainCRF(directed=True)
ssvm = FrankWolfeSSVM(model=model, C=.1, max_iter=11)
ssvm.fit(np.vstack(svm_predictions_train).reshape((5375, 1, 26)), np.hstack(y_train).reshape(5375, 1))

# Train linear chain CRF
chain_model = ChainCRF(directed=True)
chain_ssvm = FrankWolfeSSVM(model=chain_model, C=.1, max_iter=20, verbose=1)
chain_ssvm.fit(svm_predictions_train, y_train)

# # Create linear regression object
# regr = LinearRegression()
# # Train the model using the training sets
# regr.fit(np.vstack(svm_predictions_train), np.hstack(y_train))

# print("Test score with linear regression: %f" % regr.score(np.vstack(svm_predictions_test),
#                                                    np.hstack(y_test)))
print("Test score with linear SVM: %f" % svm.score(np.vstack(X_test),
                                                   np.hstack(y_test)))
print("Test score with CRF: %f" % ssvm.score(svm_predictions_test, y_test))

print("Test score with Linear Chain CRF: %f" % chain_ssvm.score(svm_predictions_test, y_test))

# # plot some word sequenced
# n_words = 4
# rnd = np.random.RandomState(1)
# selected = rnd.randint(len(y_test), size=n_words)
# max_word_len = max([len(y_) for y_ in y_test[selected]])
# fig, axes = plt.subplots(n_words, max_word_len, figsize=(10, 10))
# fig.subplots_adjust(wspace=0)
# fig.text(0.2, 0.05, 'GT', color="#00AA00", size=25)
# fig.text(0.4, 0.05, 'SVM', color="#5555FF", size=25)
# fig.text(0.6, 0.05, 'LCCRF', color="#FF5555", size=25)
# fig.text(0.8, 0.05, 'CRF', color="#FFD700", size=25)

# fig.text(0.05, 0.5, 'Word', color="#000000", size=25)
# fig.text(0.5, 0.95, 'Letters', color="#000000", size=25)

# for ind, axes_row in zip(selected, axes):
#     y_pred_svm = svm.predict(X_test[ind])
#     y_pred_chain = chain_ssvm.predict([X_test[ind]])[0]
#     y_pred_crf = ssvm.predict([X_test[ind]])[0]
#     import pdb
#     pdb.set_trace()
#     for i, (a, image, y_true, y_svm, y_chain, y_crf) in enumerate(
#             zip(axes_row, X_test[ind], y_test[ind], y_pred_svm, y_pred_chain, y_pred_crf)):
#         a.matshow(image.reshape(16, 8), cmap=plt.cm.Greys)
#         a.text(0, 3, abc[y_true], color="#00AA00", size=25)    # Green
#         a.text(0, 14, abc[y_svm], color="#5555FF", size=25)    # Blue
#         a.text(5, 14, abc[y_chain], color="#FF5555", size=25)  # Red
#         a.text(5, 3, abc[y_crf], color="#FFD700", size=25)     # Yellow
#         a.set_xticks(())
#         a.set_yticks(())
#     for ii in range(i + 1, max_word_len):
#         axes_row[ii].set_visible(False)

w = chain_ssvm.w[26 * 26:].reshape(26, 26)
# w = ssvm.w[26 * 8 * 16:].reshape(26, 26)
w_prob = np.exp(w) / sum(np.exp(w))

fig, ax = plt.subplots(nrows=1, ncols=2)
ax[0].set_title('Transition parameters of the chain CRF.', fontsize=30)
# ax[0].set_title('Transition parameters of the CRF.', fontsize=30)

plt.sca(ax[0])
plt.xticks(np.arange(26), abc, fontsize=20)
plt.yticks(np.arange(26), abc, fontsize=20)
imshow(w, ax=ax[0], fig=fig, colormap='rainbow')

ax[1].set_title('Transition Probability of the chain CRF.', fontsize=30)
# ax[1].set_title('Transition Probability of the CRF.', fontsize=30)
plt.sca(ax[1])
plt.xticks(np.arange(26), abc, fontsize=20)
plt.yticks(np.arange(26), abc, fontsize=20)
imshow(w_prob, ax=ax[1], fig=fig, colormap='rainbow', block=True)


