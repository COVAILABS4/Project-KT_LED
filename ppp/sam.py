from scipy.special import gamma
import matplotlib.pyplot as plt
import numpy as np

V = 1
alpha_m = 0.1 * (V + 40) / (1 - np.exp(-(V + 40) / 10))
beta_m = 4 * np.exp(-(V + 65) / 18)

q = 1
al = 1

dp = [0 for i in range(1000)]

def generate_data_with_nan_handling(i):
    num = gamma(1 + (i / q))
    den = gamma(al + 1 + (i / q))
    
    if den != 0:  # Avoid division by zero
        div = num / den
        dp[i] = div * (alpha_m - (alpha_m + beta_m) * dp[i - 1])
    else:
        dp[i] = np.nan  # Handle potential NaN

# Generate data for dp array
for i in range(1, 1000):
    generate_data_with_nan_handling(i)

# Prepare for plotting
x_values = np.arange(1000)
y_values = np.array(dp)

# Plot the data
plt.figure(figsize=(10, 6))

# Plot non-NaN values in blue
plt.plot(x_values[~np.isnan(y_values)], y_values[~np.isnan(y_values)], label="Valid Data", color='blue')

# Plot NaN values in red as a straight line
plt.plot(x_values[np.isnan(y_values)], [0]*np.sum(np.isnan(y_values)), label="NaN Values", color='red')

plt.xlim(0, 1000)
plt.xlabel("Index")
plt.ylabel("Data Values")
plt.title("Plot of Generated Data with NaN values")
plt.legend()
plt.grid(True)
plt.show()
