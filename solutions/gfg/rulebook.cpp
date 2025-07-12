#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    int ruleBook(int N, vector<int> A, vector<int> B) {
        long long sum = 0;
        for (int i = 0; i < N; i++) {
            sum += (long long)A[i] * B[i];
        }
        return sum % 1000000007;
    }
};