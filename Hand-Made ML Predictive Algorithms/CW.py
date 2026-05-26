import numpy as np
import pandas as pd
import math
import os
import time

from collections import Counter
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

studentID = 39944042

# DATA AND PREPARATION

column_names = ['Id', 'RI', 'Na', 'Mg', 'Al', 'Si', 'K', 'Ca', 'Ba', 'Fe', 'Type']

# Load the Glass Identification dataset
data = pd.read_csv('./glass+identification/glass.data', header=None, names=column_names)

# Seed random number generator with student ID for reproducibility
np.random.seed(studentID)

# Drop Id column which carries no useful information for classification
data = data.drop(columns=['Id'])

# Separate features (X = chemical properties) and labels (y = glass type)
X = data.drop(columns=['Type']).values  # .values converts to numpy array
y = data['Type'].values

# Randomly shuffle indices then split 80% training, 20% testing
indices = np.random.permutation(len(data))
split = int(0.8 * len(data))

xTrain = X[indices[:split]]
yTrain = y[indices[:split]]
xTest  = X[indices[split:]]
yTest  = y[indices[split:]]

print("-------------------------")
print(f"Training samples: {len(xTrain)}")
print(f"Testing samples:  {len(xTest)}")

# fit on training data only to prevent data leakage
scaler = StandardScaler()
xTrainScaled = scaler.fit_transform(xTrain)
xTestScaled  = scaler.transform(xTest)


# METHODOLOGY - K-NEAREST NEIGHBOURS (KNN)

def euclideanDistance(a, b):
    # Euclidean distance between two samples
    return np.sqrt(np.sum((a - b) ** 2))

def getNeighbors(xTrain, yTrain, testSample, k):
    # get the k nearest neighbours to the test sample
    distances = [euclideanDistance(testSample, x) for x in xTrain]
    sortedIndices = np.argsort(distances)
    kNearest = sortedIndices[:k]
    return yTrain[kNearest]

def majorityVote(neighborLabels):
    # return the most common label among neighbours
    labels, counts = np.unique(neighborLabels, return_counts=True)
    return labels[np.argmax(counts)]

def knnPredict(xTrain, yTrain, xTest, k):
    # predict class for all test samples
    predictions = []
    for testSample in xTest:
        neighbourLabels = getNeighbors(xTrain, yTrain, testSample, k)
        predictions.append(majorityVote(neighbourLabels))
    return np.array(predictions)

# test K from 1 to 19, pick the K with highest accuracy
print("-------------------------")
print("KNN - testing K values 1 to 19:")
bestK = 1
bestKAccuracy = 0
for k in range(1, 20):
    preds = knnPredict(xTrainScaled, yTrain, xTestScaled, k)
    acc = np.sum(preds == yTest) / len(yTest) * 100
    print(f"  K={k:2d} -> Accuracy={acc:.3f}%")
    if acc > bestKAccuracy:
        bestKAccuracy = acc
        bestK = k
print(f"  Best K={bestK} (Accuracy={bestKAccuracy:.3f}%)")

# METHODOLOGY - DECISION TREE

def entropy(y):
    # measures how mixed a group of labels is
    total = len(y)
    _, counts = np.unique(y, return_counts=True)
    result = 0
    for c in counts:
        p = c / total
        result -= p * np.log2(p)  # entropy formula
    return result

def informationGain(y, yLeft, yRight):
    # scores how good a split is
    n, nLeft, nRight = len(y), len(yLeft), len(yRight)
    if nLeft == 0 or nRight == 0:
        return 0
    return entropy(y) - (nLeft/n) * entropy(yLeft) - (nRight/n) * entropy(yRight)

def bestSplit(x, y):
    # try every feature and threshold to find the best split
    bestGain = -1  # start at -1 so first split is always saved
    bestFeature = None
    bestThreshold = None

    for feature in range(x.shape[1]):  # loop through each feature (column)
        thresholds = np.unique(x[:, feature])
        for i in range(len(thresholds) - 1):
            # try midpoint between consecutive values as threshold
            threshold = (thresholds[i] + thresholds[i+1]) / 2
            leftMask  = x[:, feature] <= threshold
            gain = informationGain(y, y[leftMask], y[~leftMask])
            if gain > bestGain:
                bestGain = gain
                bestFeature = feature
                bestThreshold = threshold

    return bestFeature, bestThreshold

class Node:
    # a single point in the tree, either a question or an answer
    def __init__(self, feature=None, threshold=None, left=None, right=None, label=None):
        self.feature   = feature
        self.threshold = threshold
        self.left      = left
        self.right     = right
        self.label     = label

def buildTree(x, y, maxDepth=None, depth=0):
    # recursively build the decision tree
    if len(set(y)) == 1:
        return Node(label=y[0])  # all same class, return leaf
    if maxDepth is not None and depth >= maxDepth:
        return Node(label=majorityVote(y))  # depth limit reached

    feature, threshold = bestSplit(x, y)
    if feature is None:
        return Node(label=majorityVote(y))  # no good split found

    leftMask = x[:, feature] <= threshold
    left  = buildTree(x[leftMask],  y[leftMask],  maxDepth, depth+1)
    right = buildTree(x[~leftMask], y[~leftMask], maxDepth, depth+1)
    return Node(feature=feature, threshold=threshold, left=left, right=right)

def predictOne(node, x):
    # walk down the tree for one sample
    if node.label is not None:
        return node.label  # reached a leaf node
    if x[node.feature] <= node.threshold:
        return predictOne(node.left, x)   # go left
    else:
        return predictOne(node.right, x)  # go right

def dtPredict(tree, X):
    # predict for all samples, since predictOne only works one at a time
    return np.array([predictOne(tree, x) for x in X])

# test depths 1 to 14, pick the depth with highest accuracy
print("-------------------------")
print("Decision Tree - testing depths 1 to 14:")
bestDepth = 1
bestDTAccuracy = 0
for depth in range(1, 15):
    tree = buildTree(xTrainScaled, yTrain, depth)
    preds = dtPredict(tree, xTestScaled)
    acc = np.sum(preds == yTest) / len(yTest) * 100
    print(f"  Depth={depth:2d} -> Accuracy={acc:.3f}%")
    if acc > bestDTAccuracy:
        bestDTAccuracy = acc
        bestDepth = depth
print(f"  Best Depth={bestDepth} (Accuracy={bestDTAccuracy:.3f}%)")


# METHODOLOGY - NAIVE BAYES

def calcPDF(x, mu, sigma):
    # Gaussian probability density function
    # used because features are continuous numerical values (from lab Exercise 3)
    epsilon = 1e-9  # prevent divide by zero
    sigma = max(sigma, epsilon)
    return (1 / np.sqrt(2 * math.pi * sigma**2)) * np.exp(-(x - mu)**2 / (2 * sigma**2))

def nbFit(x, y):
    # learn the mean, spread and prior for each class from training data
    classes = np.unique(y)
    model = {}
    for c in classes:
        xClass = x[y == c]  # only rows belonging to this class
        model[c] = {
            'mu'    : np.mean(xClass, axis=0),  # average of each feature
            'sigma' : np.std(xClass, axis=0),   # spread of each feature
            'prior' : len(xClass) / len(x)      # how common this class is
        }
    return model

def nbPredict(model, x):
    # predict class for all samples
    predictions = []
    for s in x:  # loop through every sample
        bestScore = -1  # make sure first class is always saved
        bestClass = None
        for c in model:  # try every glass type
            score = model[c]['prior']
            for i in range(len(s)):  # loop through each feature
                score *= calcPDF(s[i], model[c]['mu'][i], model[c]['sigma'][i])
            if score > bestScore:
                bestScore = score
                bestClass = c
        predictions.append(bestClass)
    return np.array(predictions)


# RESULTS

print("-------------------------")
print("Final Results:")

# KNN
kStart = time.time()
kPredictions = knnPredict(xTrainScaled, yTrain, xTestScaled, bestK)
kEnd = time.time()
kTime = kEnd - kStart
kAccuracy = np.sum(kPredictions == yTest) / len(yTest) * 100
print(f"KNN Algorithm: K={bestK} -> Accuracy={kAccuracy:.3f}% | Time={kTime:.6f}s")

# Decision Tree
dStart = time.time()
dtTree = buildTree(xTrainScaled, yTrain, bestDepth)
dtPredictions = dtPredict(dtTree, xTestScaled)
dEnd = time.time()
dTime = dEnd - dStart
dtAccuracy = np.sum(dtPredictions == yTest) / len(yTest) * 100
print(f"Decision Tree: Depth={bestDepth} -> Accuracy={dtAccuracy:.3f}% | Time={dTime:.6f}s")

# Naive Bayes
nStart = time.time()
nbModel = nbFit(xTrainScaled, yTrain)
nbPredictions = nbPredict(nbModel, xTestScaled)
nEnd = time.time()
nTime = nEnd - nStart
nbAccuracy = np.sum(nbPredictions == yTest) / len(yTest) * 100
print(f"Naive Bayes: Accuracy={nbAccuracy:.3f}% | Time={nTime:.6f}s")

# Confusion matrices for all three models
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
classes = np.unique(yTest)

cmKNN = confusion_matrix(yTest, kPredictions, labels=classes)
ConfusionMatrixDisplay(cmKNN, display_labels=classes).plot(ax=axes[0])
axes[0].set_title(f"KNN (K={bestK})")

cmDT = confusion_matrix(yTest, dtPredictions, labels=classes)
ConfusionMatrixDisplay(cmDT, display_labels=classes).plot(ax=axes[1])
axes[1].set_title(f"Decision Tree (Depth={bestDepth})")

cmNB = confusion_matrix(yTest, nbPredictions, labels=classes)
ConfusionMatrixDisplay(cmNB, display_labels=classes).plot(ax=axes[2])
axes[2].set_title("Naive Bayes")

plt.tight_layout()
plt.show()