def two_sum_sort(nums, k):
    nums.sort()
    left, right = 0, len(nums) - 1

    while left < right:
        current_sum = nums[left] + nums[right]

        if current_sum == k:
            return [nums[left], nums[right]]
        elif current_sum < k:
            left += 1
        else:
            right -= 1

    return False


def two_sum_one_pass(nums, k):
    seen = set()

    for num in nums:
        complement = k - num
        if complement in seen:
            return [complement, num]
        seen.add(num)

    return False


def main():
    nums = list(map(int, input("Enter numbers separated by space: ").split()))
    k = int(input("Enter target k: "))

    print("Using sort + two pointers:")
    print(two_sum_sort(nums.copy(), k))

    print("\nUsing one-pass hash set:")
    print(two_sum_one_pass(nums, k))


if __name__ == "__main__":
    main()