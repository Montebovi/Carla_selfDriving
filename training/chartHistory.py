import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


history=np.load(r'G:\18SetLossGr\my_history2.npy',allow_pickle='TRUE').item()

pd.set_option('display.max_columns', None)
data = pd.DataFrame(history)
print(data.head())
# data.plot()
# plt.xlabel("epochs")
# plt.show()

loss = data[["loss","val_loss"]]
loss.plot()
plt.xlabel("epochs")
plt.ylabel("loss")
plt.show()

loss = data[["meanSteer","val_meanSteer"]]
loss.plot()
plt.xlabel("epochs")
plt.ylabel("mean steer error")
plt.show()

loss = data[["cosine_proximity","val_cosine_proximity"]]
loss.plot()
plt.xlabel("epochs")
plt.ylabel("cosine similarity")
plt.show()

