
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
import random

X = np.array([[1,2,3,4,5,6,7,8,9],[4,6,7,8,9,10,11,12,13],[6,9,8,7,1,6,58,6,10]])
y = []
for i in range(0,len(X[0])):
    y.append(random.randint(0,3))
y = np.array(y)
plt.rcParams['figure.figsize'] = (10, 5)
kmeans = KMeans(n_clusters=3)
kmeans = kmeans.fit(X)
labels = kmeans.predict(X)
C = kmeans.cluster_centers_
point = []
for i in range(len(X[0])):
    d = []
    for j in X:
        d.append(j[i])
    point.append(d)

X = np.array(point)
fig = plt.figure()
ax = Axes3D(fig)

ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=y)
ax.scatter(C[:, 0], C[:, 1], C[:, 2], marker='^', c='red', s=1000)
plt.show()