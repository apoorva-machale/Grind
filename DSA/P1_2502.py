# Given an array of integers, return a new array such that each element at index i of the new array is the product of all the numbers in the original array except the one at i.
# For example, if our input was [1, 2, 3, 4, 5], the expected output would be [120, 60, 40, 30, 24]. If our input was [3, 2, 1], the expected output would be [2, 3, 6].
# Follow-up: what if you can't use division?

def product_array(nums):
    n= len(nums)
    product_array = n*[1]
    for i in range(1,n):
        product_array[i] = product_array[i-1] * nums[i-1]
    
    right = 1
    for i in range(n-1, -1, -1):
        product_array[i] *= right
        right *= nums[i]
    return product_array

def main():
    nums = list(map(int, input("Enter numbers separated by space: ").split()))
    print("Product of Array")
    print(product_array(nums))

if __name__ == "__main__":
    main()
