import random
import math

scaling_factor = { 2 : 4, 3 : 6}
# In 2D, volume of unit ball is pi/4. In 3D, volume is pi/6.

def proportion_one_batch(n, dimension):
    """ The proportion among 2**n points that sits inside the unit ball"""
    count = 0
    for i in range(2**n):
        if sum(random.random()**2 for j in range(dimension)) <= 1:
            count += 1
    return float(count)/2**n

def deviation_one_batch(n, dimension):
    """ Deviation between pi and the approx calculated by using 2**n points"""
    return (proportion_one_batch(n, dimension) * scaling_factor[dimension] 
                - math.pi)
    
def experiment_all_batches(n, dimension, repeats):
    """ Logarithm of the average over repeats of the square of the deviation"""
    return math.log(sum([deviation_one_batch(n, dimension)**2 
                for i in range(repeats)])/repeats)
    
def full_experiment(dimension, max_n, repeats):
    """ Performs the repeated experiment of approximating pi.
    
    We use the Monte Carlo method to approximate pi. We draw 2**n points in the unit box of given dimension (2 or 3), for n between 0 and max_n. We compute the proportion of those points sitting inside the unit ball and deduce an approximation for pi.  As indicated by the repeats argument, we repeat this many times over, and average the square of the deviation. Finally, we return the log of those averages for different n. 
    """
    return [experiment_all_batches(n, dimension, repeats) for n in range(max_n)]

print "For 100 batches of sizes increasing up to 2**15 points in dimension 2:"
result2 = full_experiment(2, 15, 100)
print result2
print "For 100 batches of sizes increasing up to 2**15 points in dimension 3:"
result3 = full_experiment(3, 15, 100)
print result3

# What is below produces an image
import matplotlib.pyplot as plt
plt.plot(range(15), result2, "ro", range(15), result3, "r--")
plt.show()

    